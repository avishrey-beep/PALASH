from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.pack import LanguagePack, SyncManifest
from backend.app.models.curriculum import Lesson
from backend.app.models.translation import Phrase
from backend.app.models.device import Device, DeviceSyncLog
from backend.app.models.user import User
from backend.app.models.classroom import ClassroomSession, AudioUtterance

class SyncService:
    @staticmethod
    def get_latest_manifest(db: Session, language_code: str = "sat") -> Dict[str, Any]:
        pack = db.query(LanguagePack).filter_by(
            language_code=language_code,
            is_active=True
        ).order_by(LanguagePack.created_at.desc()).first()

        if not pack:
            raise HTTPException(status_code=404, detail=f"No active language pack found for {language_code}")

        return {
            "version": pack.version,
            "language_code": pack.language_code,
            "pack_checksum": pack.checksum,
            "size_bytes": pack.file_size_bytes,
            "manifest": pack.manifest_json
        }

    @classmethod
    def compute_delta(
        cls,
        db: Session,
        client_version: str,
        client_checksums: Dict[str, str],
        language_code: str = "sat"
    ) -> Dict[str, Any]:
        """
        Computes delta synchronization package (Section 29).
        If client already has phrases with matching checksum, phrases are omitted from download!
        """
        latest = cls.get_latest_manifest(db, language_code)
        latest_manifest = latest["manifest"]
        latest_section_csums = latest_manifest.get("section_checksums", {})

        deltas_required = {}
        # Compare individual sections
        for section in ["phrases", "glossary", "lessons"]:
            client_csum = client_checksums.get(section)
            server_csum = latest_section_csums.get(section)
            if client_csum != server_csum:
                deltas_required[section] = {
                    "action": "UPDATE",
                    "server_checksum": server_csum,
                    "client_checksum": client_csum
                }
            else:
                deltas_required[section] = {
                    "action": "UP_TO_DATE",
                    "checksum": server_csum
                }

        is_up_to_date = all(d["action"] == "UP_TO_DATE" for d in deltas_required.values())

        return {
            "client_version": client_version,
            "server_version": latest["version"],
            "is_up_to_date": is_up_to_date,
            "deltas_required": deltas_required,
            "download_url": f"/api/v1/language-packs/download?lang={language_code}&version={latest['version']}" if not is_up_to_date else None
        }

    @staticmethod
    def upload_client_sync(
        db: Session,
        device_id: str,
        offline_sessions: List[Dict[str, Any]],
        offline_utterances: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Persist classroom work a device recorded while offline (Section 31).

        HONESTY NOTE (§2, §72)
        ----------------------
        The previous implementation returned ``"SYNC_MERGED"`` with
        ``merged_sessions``/``merged_utterances`` counts that were simply
        ``len()`` of the request lists -- it wrote a DeviceSyncLog row and
        NOTHING ELSE. No session or utterance ever reached the database, so a
        teacher's offline classroom work was silently discarded while the API
        reported success. This rewrite actually inserts the rows and reports
        what genuinely happened: how many were created, how many were skipped
        as already-synced, and how many were rejected (with the reason), never
        a fabricated success count.

        CONFLICT RESOLUTION
        -------------------
        Sessions are de-duplicated by their client-generated id (used as the
        ClassroomSession primary key), so re-uploading an already-synced batch
        is idempotent: a second upload skips rather than duplicates. Utterances
        are attached to their referenced session; an utterance whose session is
        neither in this batch nor already on the server is rejected as an
        orphan rather than silently dropped or attached to the wrong session.

        No raw audio is accepted here (§37/§38) -- only transcripts the device
        already produced and the latencies it measured.
        """
        device = db.query(Device).filter_by(device_id=device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        sessions_created = 0
        sessions_skipped = 0
        session_errors: List[Dict[str, Any]] = []
        # Client session ids that are valid targets for utterances after this
        # pass: either created now or already present on the server.
        known_session_ids: set[str] = set()

        for idx, s in enumerate(offline_sessions):
            client_id = s.get("client_session_id") or s.get("id")
            teacher_id = s.get("teacher_id")
            topic = s.get("topic")

            if not client_id or not teacher_id or not topic:
                session_errors.append({
                    "index": idx,
                    "error": "MISSING_REQUIRED_FIELDS",
                    "detail": "client_session_id, teacher_id and topic are required.",
                })
                continue

            # Idempotent replay: this session was already synced earlier.
            existing = db.query(ClassroomSession).filter_by(id=client_id).first()
            if existing:
                sessions_skipped += 1
                known_session_ids.add(client_id)
                continue

            teacher = db.query(User).filter_by(id=teacher_id).first()
            if not teacher:
                session_errors.append({
                    "index": idx,
                    "error": "UNKNOWN_TEACHER",
                    "detail": f"teacher_id '{teacher_id}' does not exist.",
                })
                continue

            session = ClassroomSession(
                id=client_id,
                teacher_id=teacher_id,
                school_id=s.get("school_id") or device.school_id,
                class_grade=int(s.get("class_grade", 2)),
                subject=s.get("subject", "Mathematics"),
                topic=topic,
                learning_outcome=s.get("learning_outcome"),
                target_language=s.get("target_language", "sat"),
                is_active=False,  # an uploaded offline session is already over
            )
            db.add(session)
            sessions_created += 1
            known_session_ids.add(client_id)

        # Flush so freshly-created sessions are queryable as utterance targets.
        db.flush()

        utterances_created = 0
        utterance_errors: List[Dict[str, Any]] = []

        for idx, u in enumerate(offline_utterances):
            client_session_id = u.get("client_session_id") or u.get("session_id")
            transcription = u.get("transcription")
            translation = u.get("translation")

            if not client_session_id or transcription is None or translation is None:
                utterance_errors.append({
                    "index": idx,
                    "error": "MISSING_REQUIRED_FIELDS",
                    "detail": "client_session_id, transcription and translation are required.",
                })
                continue

            # The session must exist (created in this batch or previously). We
            # verify against the DB rather than trusting known_session_ids alone
            # so an id that was rejected above is correctly treated as an orphan.
            if client_session_id not in known_session_ids:
                if db.query(ClassroomSession).filter_by(id=client_session_id).first() is None:
                    utterance_errors.append({
                        "index": idx,
                        "error": "ORPHAN_UTTERANCE",
                        "detail": f"No session '{client_session_id}' to attach to.",
                    })
                    continue
                known_session_ids.add(client_session_id)

            # confidence stays None (SQL NULL = unknown) when absent -- never
            # coerced to a fabricated score (§52).
            confidence = u.get("confidence")
            utterance = AudioUtterance(
                session_id=client_session_id,
                source_language=u.get("source_language", "hin"),
                target_language=u.get("target_language", "sat"),
                transcription=transcription,
                translation=translation,
                confidence=confidence,
                tier_used=u.get("tier_used", "cache"),
                vad_latency_ms=float(u.get("vad_latency_ms", 0.0)),
                asr_latency_ms=float(u.get("asr_latency_ms", 0.0)),
                translation_latency_ms=float(u.get("translation_latency_ms", 0.0)),
                tts_latency_ms=float(u.get("tts_latency_ms", 0.0)),
                total_latency_ms=float(u.get("total_latency_ms", 0.0)),
            )
            db.add(utterance)
            utterances_created += 1

        # Log the sync event with the REAL byte count and outcome.
        payload_bytes = len(str(offline_sessions)) + len(str(offline_utterances))
        rejected = len(session_errors) + len(utterance_errors)
        log = DeviceSyncLog(
            device_id=device.id,
            sync_type="offline_upload_delta",
            status="completed" if rejected == 0 else "completed_with_rejections",
            bytes_transferred=payload_bytes,
        )
        db.add(log)
        db.commit()

        return {
            "status": "SYNC_MERGED" if rejected == 0 else "SYNC_PARTIAL",
            "device_id": device_id,
            "conflict_strategy": "CLIENT_APPEND_MERGE",
            "sessions_created": sessions_created,
            "sessions_skipped_already_synced": sessions_skipped,
            "utterances_created": utterances_created,
            "rejected": rejected,
            "session_errors": session_errors,
            "utterance_errors": utterance_errors,
        }
