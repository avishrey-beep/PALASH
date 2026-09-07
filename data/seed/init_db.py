import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models import (
    User, Role, Language, Curriculum, CurriculumVersion, Lesson, LessonVersion,
    Phrase, TranslationMemoryItem, GlossaryTerm, Flashcard, AIModelEntry, Device
)

def deterministic_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def seed_database(engine_override=None):
    target_engine = engine_override or engine
    Base.metadata.create_all(bind=target_engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=target_engine)
    db = session_factory()
    try:
        # 1. Seed Roles
        roles = [
            ("ADMIN", "System Administrator with full access"),
            ("TEACHER", "Primary School Teacher conducting classroom lessons"),
            ("CURRICULUM_MANAGER", "Curriculum Ingestion and Review Specialist"),
            ("LANGUAGE_REVIEWER", "Native speaker validating low-resource translations"),
            ("ML_OPERATOR", "Machine Learning & Model Registry Specialist"),
            ("DEVICE", "Registered Classroom Android Device")
        ]
        for role_name, desc in roles:
            if not db.query(Role).filter_by(name=role_name).first():
                db.add(Role(name=role_name, description=desc))
        db.commit()

        # 2. Seed Users
        users_data = [
            ("admin", "admin@edutech.jharkhand.gov.in", "Admin@Jharkhand2026", "System Administrator", ["ADMIN"]),
            ("teacher_dumka", "teacher.dumka@schools.jharkhand.gov.in", "Teacher@Jharkhand2026", "Sunita Soren (Primary Teacher)", ["TEACHER"]),
            ("reviewer_santali", "reviewer.santali@language.jharkhand.gov.in", "Reviewer@Jharkhand2026", "Dr. B. Murmu (Santhali Linguist)", ["LANGUAGE_REVIEWER"]),
            ("curriculum_mgr", "curriculum@jcert.jharkhand.gov.in", "Curriculum@Jharkhand2026", "JCERT Curriculum Lead", ["CURRICULUM_MANAGER"]),
            ("ml_operator", "mlops@edutech.jharkhand.gov.in", "MLOp@Jharkhand2026", "Edge ML Engineer", ["ML_OPERATOR"]),
        ]
        for uname, email, pwd, fname, role_list in users_data:
            user = db.query(User).filter_by(username=uname).first()
            if not user:
                role_objs = db.query(Role).filter(Role.name.in_(role_list)).all()
                user = User(
                    username=uname,
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    full_name=fname,
                    school_id="GPS_DUMKA_01",
                    is_active=True,
                    is_verified=True,
                    roles=role_objs
                )
                db.add(user)
        db.commit()

        # 3. Seed Languages
        languages_data = [
            ("hin", "Hindi", "हिन्दी", "Devanagari"),
            ("sat", "Santhali", "ᱥᱟᱱᱛᱟᱲᱤ", "Ol Chiki"),
            ("unr", "Mundari", "मुंडारी", "Mundari Bani / Devanagari"),
            ("hoc", "Ho", "ᱦᱳ", "Warang Chiti / Devanagari")
        ]
        for code, name, native_name, script in languages_data:
            if not db.query(Language).filter_by(code=code).first():
                db.add(Language(code=code, name=name, native_name=native_name, default_script=script, is_active=True))
        db.commit()

        # 4. Seed Curriculum and Lessons (JCERT Class 2 Mathematics)
        curriculum = db.query(Curriculum).filter_by(title="JCERT Class 2 Mathematics - Ganit Khel").first()
        if not curriculum:
            curriculum = Curriculum(
                title="JCERT Class 2 Mathematics - Ganit Khel",
                state="Jharkhand",
                board="JCERT",
                class_grade=2,
                subject="Mathematics",
                medium="Hindi",
                current_version=1,
                description="Foundational Literacy and Numeracy (FLN) Grade 2 mathematics curriculum focusing on counting and addition up to 20."
            )
            db.add(curriculum)
            db.commit()

            c_version = CurriculumVersion(
                curriculum_id=curriculum.id,
                version_number=1,
                checksum=deterministic_hash("curriculum_v1_jcert_class2_math"),
                status="PUBLISHED",
                changelog="Initial baseline curriculum import for Class 2 Mathematics."
            )
            db.add(c_version)

            lesson = Lesson(
                curriculum_id=curriculum.id,
                unit_number=1,
                lesson_number=1,
                title_hindi="संख्याओं का खेल - २० तक जोड़",
                topic="Addition up to 20 with concrete objects",
                learning_outcomes=[
                    "Children can count objects from 1 to 20 in their home language and Hindi",
                    "Children understand combining two groups of objects (addition)",
                    "Children can verbally state the total number of objects"
                ],
                activities=[
                    "Use tamarind seeds (imli ke beej) or pebbles to count up to 10",
                    "Combine 3 pebbles and 2 pebbles, then count total",
                    "Peer counting game in pairs"
                ],
                assessments=[
                    "गिनो और बताओ: कितने आम हैं?",
                    "३ और २ मिलाकर कितने होते हैं?",
                    "अपनी किताब में दिए गए चित्रों को गिनकर लिखो।"
                ],
                vocabulary=["जोड़ (addition)", "गिनती (counting)", "कुल (total)", "बराबर (equals)"],
                current_version=1
            )
            db.add(lesson)
            db.commit()

            l_version = LessonVersion(
                lesson_id=lesson.id,
                version_number=1,
                checksum=deterministic_hash("lesson_v1_numbers_game"),
                content_json={
                    "title": "संख्याओं का खेल - २० तक जोड़",
                    "topic": "Addition up to 20 with concrete objects",
                    "unit": 1,
                    "lesson_number": 1
                },
                status="PUBLISHED"
            )
            db.add(l_version)
            db.commit()

        # 5. Seed Tier 1 Phrase Cache (Verified Classroom Expressions)
        phrases_data = [
            ("बैठ जाओ", "ᱫᱩᱲᱩᱵ ᱢᱮ", "duṛup' me", "classroom", 2, "General"),
            ("खड़े हो जाओ", "ᱛᱤᱸᱜᱩᱱ ᱢᱮ", "tĩgun me", "classroom", 2, "General"),
            ("अपनी किताब खोलो", "ᱯᱚᱛᱚᱵ ᱡᱷᱤᱡᱽ ᱢᱮ", "potob jhij me", "classroom", 2, "General"),
            ("ध्यान से सुनो", "ᱫᱷᱮᱭᱟᱱ ᱛᱮ ᱟᱧᱡᱚᱢ ᱢᱮ", "dhiyan te añjom me", "classroom", 2, "General"),
            ("गिनो और बताओ", "ᱞᱮᱠᱷᱟᱭ ᱢᱮ ᱟᱨ ᱞᱟᱹᱭ ᱢᱮ", "lekhai me ar ləy me", "classroom", 2, "Mathematics"),
            ("कितने आम हैं?", "ᱛᱤᱱᱟᱹᱜ ᱩᱞ ᱢᱮᱱᱟᱜ-ᱟ?", "tinəg ul menag-a?", "classroom", 2, "Mathematics"),
            ("तीन और दो मिलाकर कितने होते हैं?", "ᱯᱮ ᱟᱨ ᱵᱟᱨ ᱢᱮᱥᱟ ᱠᱟᱛᱮ ᱛᱤᱱᱟᱹᱜ ᱦᱩᱭᱩᱜ-ᱟ?", "pe ar bar mesa kate tinəg huyug-a?", "classroom", 2, "Mathematics"),
            ("बहुत अच्छा", "ᱟᱹᱰᱤ ᱵᱷᱟᱹᱜᱤ", "aḍi bhagi", "classroom", 2, "Praise"),
            ("शाबाश बच्चों", "ᱥᱟᱨᱦᱟᱣ ᱜᱤᱫᱽᱨᱟᱹ ᱠᱚ", "sarhaw gidrə ko", "classroom", 2, "Praise"),
            ("अपनी कॉपी में लिखो", "ᱟᱢᱟᱜ ᱠᱷᱟᱛᱟ ᱨᱮ ᱚᱞ ᱢᱮ", "amag khata re ol me", "classroom", 2, "Instruction"),
            ("यहाँ देखो", "ᱱᱚᱸᱰᱮ ᱧᱮᱞ ᱢᱮ", "nõṇḍe ñel me", "classroom", 2, "Instruction"),
            ("श्यामपट्ट पर देखो", "ᱵᱽᱞᱮᱠᱵᱳᱨᱰ ᱨᱮ ᱧᱮᱞ ᱢᱮ", "blackboard re ñel me", "classroom", 2, "Instruction"),
            ("मेरे बाद दोहराओ", "ᱤᱧ ᱛᱟᱭᱚᱢ ᱛᱮ ᱨᱚᱲ ᱢᱮ", "iñ tayom te roṛ me", "classroom", 2, "Instruction"),
            ("क्या तुमने समझ लिया?", "ᱪᱮᱫ ᱟᱢ ᱵᱩᱡᱷᱟᱹᱣ ᱠᱮᱫ-ᱟ?", "chet' am bujhəw ket'-a?", "classroom", 2, "Check"),
            ("हाथ ऊपर करो", "ᱛᱤ ᱛᱩᱞ ᱢᱮ", "ti tul me", "classroom", 2, "Activity"),
            ("एक", "ᱢᱤᱫ", "mit'", "numeracy", 2, "Mathematics"),
            ("दो", "ᱵᱟᱨ", "bar", "numeracy", 2, "Mathematics"),
            ("तीन", "ᱯᱮ", "pe", "numeracy", 2, "Mathematics"),
            ("चार", "ᱯᱳᱱ", "pon", "numeracy", 2, "Mathematics"),
            ("पाँच", "ᱢᱚᱬᱮ", "mõṛẽ", "numeracy", 2, "Mathematics"),
            ("छह", "ᱛᱩᱨᱩᱭ", "turui", "numeracy", 2, "Mathematics"),
            ("सात", "ᱮᱭᱟᱭ", "eyae", "numeracy", 2, "Mathematics"),
            ("आठ", "ᱤᱨᱟᱹᱞ", "irəl", "numeracy", 2, "Mathematics"),
            ("नौ", "ᱟᱨᱮ", "are", "numeracy", 2, "Mathematics"),
            ("दस", "ᱜᱮᱞ", "gel", "numeracy", 2, "Mathematics")
        ]

        for src, tgt, pron, domain, grade, subj in phrases_data:
            norm_key = f"hin:sat:{src.strip().lower()}"
            ckey = deterministic_hash(norm_key)
            if not db.query(Phrase).filter_by(cache_key=ckey).first():
                phrase = Phrase(
                    cache_key=ckey,
                    source_lang="hin",
                    target_lang="sat",
                    source_text=src,
                    target_text=tgt,
                    domain=domain,
                    class_grade=grade,
                    subject=subj,
                    confidence=1.0,
                    verification_status="human_verified",
                    audio_asset_path=f"audio/sat/{ckey[:12]}.wav",
                    usage_frequency=10,
                    version=1
                )
                db.add(phrase)
        db.commit()

        # 6. Seed Translation Memory Items
        tm_data = [
            ("Count the objects and write the number in your notebook.", "ᱡᱤᱱᱤᱥ ᱠᱚ ᱞᱮᱠᱷᱟᱭ ᱢᱮ ᱟᱨ ᱟᱢᱟᱜ ᱠᱷᱟᱛᱟ ᱨᱮ ᱱᱚᱢᱵᱚᱨ ᱚᱞ ᱢᱮ।", "hin", "sat", 1.0),
            ("Look at the picture and answer the question.", "ᱪᱤᱛᱟᱹᱨ ᱧᱮᱞ ᱢᱮ ᱟᱨ ᱠᱩᱠᱞᱤ ᱨᱮᱱᱟᱜ ᱛᱮᱞᱟ ᱮᱢ ᱢᱮ।", "hin", "sat", 1.0),
            ("Add two numbers together.", "ᱵᱟᱨᱭᱟ ᱮᱞ ᱢᱮᱥᱟᱭ ᱢᱮ।", "hin", "sat", 1.0),
            ("How many birds are on the tree?", "ᱫᱟᱨᱮ ᱨᱮ ᱛᱤᱱᱟᱹᱜ ᱪᱮᱬᱮ ᱢᱮᱱᱟᱜ ᱠᱚᱣᱟ?", "hin", "sat", 1.0)
        ]
        for src, tgt, sl, tl, qs in tm_data:
            if not db.query(TranslationMemoryItem).filter_by(source_text=src).first():
                tm_item = TranslationMemoryItem(
                    source_lang=sl,
                    target_lang=tl,
                    source_text=src,
                    target_text=tgt,
                    domain="education",
                    subject="Mathematics",
                    class_grade=2,
                    verification_status="human_verified",
                    quality_score=qs,
                    source_type="fln_curriculum"
                )
                db.add(tm_item)
        db.commit()

        # 7. Seed Glossary Terms (Multilingual: Santhali, Mundari, Ho)
        glossary_data = [
            ("गिनती", "ᱞᱮᱠᱷᱟ", "sat", "mathematics", "ᱞᱮᱠᱷᱟ", "lekha", 2, "Mathematics"),
            ("जोड़", "ᱢᱮᱥᱟ", "sat", "mathematics", "ᱢᱮᱥᱟ", "mesa", 2, "Mathematics"),
            ("घटाव", "ᱜᱮᱫ / ᱚᱪᱚᱜ", "sat", "mathematics", "ᱜᱮᱫ", "ged", 2, "Mathematics"),
            ("किताब", "ᱯᱚᱛᱚᱵ", "sat", "classroom", "ᱯᱚᱛᱚᱵ", "potob", 2, "General"),
            ("कलम", "ᱠᱚᱞᱚᱢ", "sat", "classroom", "ᱠᱚᱞᱚᱢ", "kolom", 2, "General"),
            ("शिक्षक", "ᱢᱟᱪᱮᱛ", "sat", "classroom", "ᱢᱟᱪᱮᱛ", "machet'", 2, "General"),
            ("बच्चा", "ᱜᱤᱫᱽᱨᱟᱹ", "sat", "classroom", "ᱜᱤᱫᱽᱨᱟᱹ", "gidrə", 2, "General"),
            ("पेड़", "ᱫᱟᱨᱮ", "sat", "nature", "ᱫᱟᱨᱮ", "dare", 2, "EVS"),
            ("फल", "ᱡᱚ", "sat", "nature", "ᱡᱚ", "jo", 2, "EVS"),
            ("पानी", "ᱫᱟᱜ", "sat", "nature", "ᱫᱟᱜ", "dag", 2, "EVS"),
            # Mundari terms
            ("गिनती", "ᱞᱮᱠᱷᱟ / लेका", "unr", "mathematics", "लेका", "leka", 2, "Mathematics"),
            ("जोड़", "मेशा", "unr", "mathematics", "मेशा", "mesha", 2, "Mathematics"),
            ("किताब", "पुथी", "unr", "classroom", "पुथी", "puthi", 2, "General"),
            ("पानी", "दाः", "unr", "nature", "दाः", "da:", 2, "EVS"),
            # Ho terms
            ("गिनती", "ᱞᱮᱠᱟ / लेका", "hoc", "mathematics", "लेका", "leka", 2, "Mathematics"),
            ("किताब", "पुथी", "hoc", "classroom", "पुथी", "puthi", 2, "General"),
            ("पानी", "दाः", "hoc", "nature", "दाः", "da:", 2, "EVS")
        ]
        for h_term, t_term, lang, dom, app_trans, pron, grade, subj in glossary_data:
            if not db.query(GlossaryTerm).filter_by(hindi_term=h_term, target_lang=lang).first():
                g_term = GlossaryTerm(
                    hindi_term=h_term,
                    target_term=t_term,
                    target_lang=lang,
                    domain=dom,
                    class_grade=grade,
                    subject=subj,
                    approved_translation=app_trans,
                    pronunciation=pron,
                    verification_status="human_verified"
                )
                db.add(g_term)
        db.commit()

        # 8. Seed Flashcards
        flashcard_data = [
            ("apple", "fruits", "सेब", "ᱥᱮᱣ / सेब", "sat", "sew"),
            ("mango", "fruits", "आम", "ᱩᱞ", "sat", "ul"),
            ("book", "classroom", "किताब", "ᱯᱚᱛᱚᱵ", "sat", "potob"),
            ("tree", "nature", "पेड़", "ᱫᱟᱨᱮ", "sat", "dare"),
            ("water", "nature", "पानी", "ᱫᱟᱜ", "sat", "dag"),
            ("one", "numbers", "एक", "ᱢᱤᱫ", "sat", "mit'"),
            ("two", "numbers", "दो", "ᱵᱟᱨ", "sat", "bar"),
            ("three", "numbers", "तीन", "ᱯᱮ", "sat", "pe"),
            ("four", "numbers", "चार", "ᱯᱳᱱ", "sat", "pon"),
            ("five", "numbers", "पाँच", "ᱢᱚᱬᱮ", "sat", "mõṛẽ")
        ]
        for concept, cat, h_term, t_term, t_lang, pron in flashcard_data:
            det_id = deterministic_hash(f"{cat}:{concept}:{t_lang}")
            if not db.query(Flashcard).filter_by(deterministic_id=det_id).first():
                fc = Flashcard(
                    deterministic_id=det_id,
                    concept=concept,
                    category=cat,
                    hindi_term=h_term,
                    target_term=t_term,
                    target_language=t_lang,
                    pronunciation=pron,
                    image_asset_path=f"images/flashcards/{concept}.png",
                    audio_asset_path=f"audio/flashcards/{concept}_{t_lang}.wav"
                )
                db.add(fc)
        db.commit()

        # 9. Seed AI Models in Model Registry
        models_data = [
            ("nllb-200-distilled-600M-sat-int8", "1.0.0", "TRANSLATION", "sat", "hin-sat", "ONNX", "INT8",
             deterministic_hash("nllb_200_distilled_600M_sat_int8"), 580.0, 380, "CC-BY-NC-4.0",
             {"bleu": 18.2, "chrf": 42.1}, 180.0, "PRODUCTION", "models/nmt/nllb_sat_int8.onnx"),
            ("indictrans2-indic-indic-distilled-int8", "2.0.0", "TRANSLATION", "sat", "hin-sat", "CTRANSLATE2", "INT8",
             deterministic_hash("indictrans2_indic_int8"), 450.0, 320, "MIT",
             {"bleu": 21.4, "chrf": 46.8}, 140.0, "PRODUCTION", "models/nmt/indictrans2_sat_int8.bin"),
            ("mms-1b-all-sat-adapter-int8", "1.0.0", "ASR", "sat", "sat", "ONNX", "INT8",
             deterministic_hash("mms_1b_sat_adapter_int8"), 320.0, 260, "CC-BY-NC-4.0",
             {"wer": 0.34, "cer": 0.12}, 240.0, "PRODUCTION", "models/asr/mms_sat_int8.onnx"),
            ("whisper-tiny-indic-int8", "1.0.0", "ASR", "hin", "hin", "ONNX", "INT8",
             deterministic_hash("whisper_tiny_hin_int8"), 75.0, 150, "MIT",
             {"wer": 0.18, "cer": 0.06}, 95.0, "PRODUCTION", "models/asr/whisper_tiny_hin.onnx"),
            ("tier1-phrase-cache-engine", "1.0.0", "TRANSLATION", "sat", "hin-sat", "SQLITE", "RAW",
             deterministic_hash("tier1_phrase_cache_engine"), 12.0, 15, "PROPRIETARY_GOV",
             {"exact_accuracy": 1.00}, 15.0, "PRODUCTION", "storage/packs/sat/phrases.db")
        ]
        for name, ver, task, lang, pair, fw, quant, csum, dsize, ram, lic, metrics, lat, stat, fpath in models_data:
            if not db.query(AIModelEntry).filter_by(model_name=name, version=ver).first():
                entry = AIModelEntry(
                    model_name=name,
                    version=ver,
                    task=task,
                    language=lang,
                    language_pair=pair,
                    framework=fw,
                    quantization=quant,
                    checksum=csum,
                    disk_size_mb=dsize,
                    ram_required_mb=ram,
                    license=lic,
                    accuracy_metrics=metrics,
                    latency_p50_ms=lat,
                    status=stat,
                    file_path=fpath
                )
                db.add(entry)
        db.commit()

        # 10. Seed Demo Device
        demo_device_id = "TAB_JHARKHAND_DUMKA_0042"
        if not db.query(Device).filter_by(device_id=demo_device_id).first():
            device = Device(
                device_id=demo_device_id,
                installation_id="INST_2026_DUMKA_001",
                school_id="GPS_DUMKA_01",
                device_model="Lava T81n (Government Issue)",
                android_version="9.0 (Pie, API 28)",
                app_version="1.0.0",
                total_ram_mb=2048,
                available_storage_mb=5840,
                supported_languages=["hin", "sat"],
                installed_models={"nmt": "tier1-phrase-cache-engine@1.0.0", "asr": "whisper-tiny-indic-int8@1.0.0"},
                remote_config={"offline_mode": True, "max_offline_sessions": 50},
                is_active=True,
                last_sync_at=datetime.now(timezone.utc)
            )
            db.add(device)
            db.commit()

        print("Database initialization and high-fidelity seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
