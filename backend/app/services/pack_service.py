import os
import json
import zipfile
import hashlib
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.core.config import settings
from backend.app.models.pack import LanguagePack, SyncManifest
from backend.app.models.curriculum import Lesson
from backend.app.models.translation import Phrase, GlossaryTerm
from ml.transliteration.olchiki import contains_ol_chiki, ol_chiki_to_devanagari

class LanguagePackService:
    @staticmethod
    def calculate_file_checksum(filepath: str) -> str:
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def build_pack(
        cls,
        db: Session,
        language_code: str = "sat",
        version: str = "1.0.0",
        min_app_version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """
        Builds a self-contained offline Language Pack (.zip) containing:
        - manifest.json
        - phrases.json
        - glossary.json
        - lessons.json
        - checksums.sha256

        Audio note (§2/§72): earlier this bundled sine-wave WAVs as
        "pre-synthesized verified clips". No real recordings exist (all seeded
        audio_asset_path files are absent from disk), so no audio is bundled.
        Instead each Ol Chiki phrase carries a Devanagari ``pronunciation``
        form the device TTS can voice offline -- labelled approximate.
        """
        os.makedirs(settings.PACKS_DIR, exist_ok=True)
        pack_filename = f"language_pack_{language_code}_v{version}.zip"
        pack_filepath = os.path.join(settings.PACKS_DIR, pack_filename)

        # 1. Collect Data from Database
        phrases = db.query(Phrase).filter_by(target_lang=language_code).all()
        phrases_data = [
            {
                "cache_key": p.cache_key,
                "source_text": p.source_text,
                "target_text": p.target_text,
                "domain": p.domain,
                "confidence": p.confidence,
                "verification_status": p.verification_status,
                "audio_asset_path": p.audio_asset_path,
                # Speakable form for offline device TTS. For Ol Chiki targets a
                # Hindi voice needs Devanagari or it produces no sound; None
                # when the target is already speakable. Approximate, not
                # native-verified -- the client must label it as such.
                "pronunciation_deva": (
                    ol_chiki_to_devanagari(p.target_text)
                    if contains_ol_chiki(p.target_text or "")
                    else None
                ),
                "pronunciation_is_approximate": contains_ol_chiki(p.target_text or ""),
            }
            for p in phrases
        ]

        glossary = db.query(GlossaryTerm).filter_by(target_lang=language_code).all()
        glossary_data = [
            {
                "hindi_term": g.hindi_term,
                "target_term": g.target_term,
                "domain": g.domain,
                "pronunciation": g.pronunciation,
                "approved_translation": g.approved_translation
            }
            for g in glossary
        ]

        lessons = db.query(Lesson).all()
        lessons_data = [
            {
                "id": l.id,
                "unit": l.unit_number,
                "lesson_number": l.lesson_number,
                "title_hindi": l.title_hindi,
                "topic": l.topic,
                "learning_outcomes": l.learning_outcomes,
                "activities": l.activities,
                "assessments": l.assessments,
                "vocabulary": l.vocabulary,
                "version": l.current_version
            }
            for l in lessons
        ]

        # No audio is bundled: no real recordings exist, and fabricated clips
        # would be a §2 mockup. The device synthesises phrase audio from the
        # pronunciation form above using its own on-device TTS.
        audio_files: Dict[str, bytes] = {}

        # Checksums of individual sections
        phrases_bytes = json.dumps(phrases_data, ensure_ascii=False, indent=2).encode("utf-8")
        glossary_bytes = json.dumps(glossary_data, ensure_ascii=False, indent=2).encode("utf-8")
        lessons_bytes = json.dumps(lessons_data, ensure_ascii=False, indent=2).encode("utf-8")

        p_csum = hashlib.sha256(phrases_bytes).hexdigest()
        g_csum = hashlib.sha256(glossary_bytes).hexdigest()
        l_csum = hashlib.sha256(lessons_bytes).hexdigest()

        manifest = {
            "pack_id": f"pack_{language_code}_{version}",
            "language_code": language_code,
            "version": version,
            "min_app_version": min_app_version,
            "created_at": "2026-09-04T00:00:00Z",
            "section_checksums": {
                "phrases": p_csum,
                "glossary": g_csum,
                "lessons": l_csum
            },
            "counts": {
                "phrases": len(phrases_data),
                "glossary": len(glossary_data),
                "lessons": len(lessons_data),
                "audio_clips": len(audio_files)
            }
        }
        manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")

        # 3. Write Zip Archive
        with zipfile.ZipFile(pack_filepath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", manifest_bytes)
            zf.writestr("phrases.json", phrases_bytes)
            zf.writestr("glossary.json", glossary_bytes)
            zf.writestr("lessons.json", lessons_bytes)
            for a_path, a_bytes in audio_files.items():
                zf.writestr(a_path, a_bytes)

        total_size = os.path.getsize(pack_filepath)
        total_checksum = cls.calculate_file_checksum(pack_filepath)

        # 4. Save LanguagePack record in DB
        lp = db.query(LanguagePack).filter_by(language_code=language_code, version=version).first()
        if not lp:
            lp = LanguagePack(
                language_code=language_code,
                version=version,
                min_app_version=min_app_version,
                file_path=pack_filepath,
                file_size_bytes=total_size,
                checksum=total_checksum,
                manifest_json=manifest,
                status="READY"
            )
            db.add(lp)
        else:
            lp.file_path = pack_filepath
            lp.file_size_bytes = total_size
            lp.checksum = total_checksum
            lp.manifest_json = manifest

        # 5. Create SyncManifest record
        sync_m = db.query(SyncManifest).filter_by(version=version, language_code=language_code).first()
        if not sync_m:
            sync_m = SyncManifest(
                version=version,
                language_code=language_code,
                curriculum_checksum=l_csum,
                phrases_checksum=p_csum,
                glossary_checksum=g_csum,
                audio_checksum=total_checksum,
                manifest_data=manifest
            )
            db.add(sync_m)

        db.commit()

        return {
            "language_code": language_code,
            "version": version,
            "file_path": pack_filepath,
            "file_size_bytes": total_size,
            "checksum": total_checksum,
            "manifest": manifest
        }
