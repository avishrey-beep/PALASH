# Palash — Backend API Map

Every HTTP endpoint currently mounted by the existing FastAPI app at
`backend/app/api/v1/api.py` (routers 22–36). Base prefix = `/api/v1`.

Source of truth: backend code itself. This map is a TS-frontend-friendly summary.

Legend:
- 🔒 Requires a valid JWT `Authorization: Bearer <access_token>` header.
- 👑 Requires role(s) above and beyond plain teacher (e.g. ADMIN, CURRICULUM_MANAGER).
- ✅ Used by the current React Native frontend.
- ⏳ Not wired yet (reserved for later phases / admin dashboards / sync enhancements).

---

## 0. Health (outside /api/v1)

| Method | URL     | Auth | Request                           | Response                                        | Errors              | Used |
|--------|---------|------|-----------------------------------|-------------------------------------------------|---------------------|------|
| GET    | `/health` | No | —                                 | `{status:"ok"|"degraded"|"error", app_version, uptime_seconds, services:{db,ai,...}}` | 503 degraded ✅ | 60s heartbeat + app-resume ping. Frontend uses separate axios client (5 s timeout). See [health.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/api/health.ts). |

---

## 1. Auth (`/auth/*`)

Existing JWT auth flow (bcrypt + PyJWT). Access token default 120 min; refresh token 30 days.

| Method | URL                       | Auth       | Request body                                                                   | Response                                                                        | Errors                 | Frontend module |
|--------|---------------------------|------------|--------------------------------------------------------------------------------|---------------------------------------------------------------------------------|------------------------|-----------------|
| POST   | `/auth/register`         | No         | `{email, password, full_name?, phone?, school?, preferred_language?, role?}`   | `{access_token, refresh_token, token_type:"bearer", user:{id,email,...}}`        | 400 validation, 409 duplicate email | ✅ [auth.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/api/auth.ts) |
| POST   | `/auth/login`            | No         | `{email, password}` (JSON) – supports OAuth2-style form too                     | `{access_token, refresh_token, token_type, user}`                               | 401 invalid creds | ✅ Same |
| POST   | `/auth/refresh`          | No         | `{refresh_token:string}`                                                        | `{access_token, refresh_token, token_type}`                                     | 401 expired/invalid refresh | ✅ Same. `client.ts` interceptor auto-refreshes with single-flight mutex. |
| GET    | `/auth/me`               | 🔒         | —                                                                               | `TeacherProfile` (full user row + settings columns)                              | 401 missing/invalid | ✅ Same. Called on session restore. |
| PATCH  | `/auth/me`               | 🔒         | Partial `{full_name?, school?, preferred_language?, settings_json?, ...}`       | Updated `TeacherProfile`                                                         | 400 validation | ✅ Same. Called from onboarding + Settings save. |
| POST   | `/auth/logout`           | 🔒         | `{refresh_token?:string}`                                                       | `{ok:true}`                                                                      | — | ✅ Same. Removes tokens on both sides. |

---

## 2. Languages (`/languages/*`, `/language-packs/*`)

| Method | URL                                  | Auth | Request                                         | Response                                             | Used |
|--------|--------------------------------------|------|-------------------------------------------------|------------------------------------------------------|------|
| GET    | `/languages`                         | No   | `?active_only=true/false`                       | `Language[]` — `{code,name,native_name,script,...}`    | ✅ AppContext boot hydrates the picker. See [languages.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/api/languages.ts). |
| GET    | `/languages/{code}`                  | No   | —                                               | `LanguageDetail`                                       | ⏳ |
| GET    | `/language-packs`                    | 🔒   | `?lang=sat`                                      | `LanguagePackMeta[]` — `{id,language_code,version,size,status}` | ✅ Settings "Language packs" list. |
| GET    | `/language-packs/{id}/download`      | 🔒   | —                                               | Binary `.plpack` (content-addressed, stream)           | ✅ `downloadUrl()` helper. |

Supported codes per `backend/app/core/config.py:42-44`:
- `hin` = Hindi
- `sat` = Santhali
- `unr` = Mundari
- `hoc` = Ho

---

## 3. Translation (`/translation/*`)

| Method | URL                           | Auth | Request                                                                 | Response                                                                 | Used |
|--------|-------------------------------|------|-------------------------------------------------------------------------|--------------------------------------------------------------------------|------|
| POST   | `/translation/translate`      | 🔒   | `{text, source_lang?, target_lang?, context_topic?, domain?, glossary_ids?}` | `{translated_text, source_lang, target_lang, confidence, tier_used, latency_ms?, alternatives?}` | ✅ Cache-first via [translation.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/api/translation.ts). Tier order: local exact → server cache → TM → AI model. Frontend saves the translated phrase to the local tier on successful return. |
| GET    | `/translation/phrases`        | 🔒   | `?target_lang=sat&domain=classroom&limit=500`                             | `CachedPhrase[]` — `{source_text,target_text,confidence,domain,...}`       | ✅ Background sync cache hydration. |
| POST   | `/translation/phrases`        | 🔒   | Verified phrase body (source/target/domain/class_grade/subject/...)       | `{id, ok:true}`                                                          | ⏳ Future review UI. |
| GET    | `/translation/glossary`       | 🔒   | `?target_lang=sat&domain?`                                                | `GlossaryTerm[]`                                                         | ⏳ |
| GET    | `/translation/review/tasks`   | 🔒👑 | `?status_filter=PENDING|APPROVED|REJECTED`                                 | `ReviewTask[]`                                                           | ⏳ |
| POST   | `/translation/review/tasks/{id}/decision` | 🔒👑 | `{decision:APPROVE|EDIT|REJECT, corrected_translation?, reason?}`       | `{ok:true}`                                                              | ⏳ |

---

## 4. Speech (`/speech/*`)

Per backend code, `POST /speech/translate` intentionally returns HTTP 501 with a comment block:
*"ASR is intentionally removed from the server — heavy GPU dependency. Run on-device and send back the resulting utterance."*
The frontend honors this: VoiceTranslationScreen runs stub on-device ASR, then POSTs the resulting transcript as an utterance. The companion TTS routes are real.

| Method | URL                       | Auth | Request                                                      | Response                                                            | Used |
|--------|---------------------------|------|--------------------------------------------------------------|---------------------------------------------------------------------|------|
| POST   | `/speech/translate`      | 🔒   | multipart `audio/*` + `{source_lang?, target_lang?}`         | **HTTP 501** with `{detail:"ASR runs on-device; POST utterances instead."}` | ✅ Expected 501. Frontend uses on-device stub instead. |
| POST   | `/speech/synthesize`     | 🔒   | `{text, target_lang, voice_profile_id?, rate?}` (JSON) or form-data with extra fields | `{pronunciation_form:"ipa|devanagari|tribal_script", transliteration?, is_approximate:bool, audio_url?, audio_bytes_b64?}` | ✅ TextTranslation: shows pronunciation; later plays through expo-speech. |
| POST   | `/speech/utterances`     | 🔒   | `{session_id?, source_text, translated_text?, source_lang, target_lang, audio_sha256?, medium:"VOICE"|"TEXT"|"AUTO"}` | `{id, ok:true, saved_cache:bool}` — also populates translation phrase cache on the server | ✅ VoiceTranslation: sends resulting transcripts for training + cache population. See [speech.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/api/speech.ts). |

---

## 5. Curriculum (`/curriculum/*`) + Jobs (`/jobs/*`)

Curriculum ingest is asynchronous: upload returns a Job, the frontend polls `GET /jobs/{id}` every 2.2 s and maps `progress_pct` →
`UPLOADING → PROCESSING → EXTRACTING → PREPARING_TRANSLATIONS → READY`.

| Method | URL                             | Auth       | Request                                                                 | Response                                                                   | Used |
|--------|---------------------------------|------------|-------------------------------------------------------------------------|----------------------------------------------------------------------------|------|
| POST   | `/curriculum/upload`           | 🔒👑 ADMIN\|CURRICULUM_MANAGER | multipart `file(PDF/DOCX/EPUB/TXT)` + `{title?, class_grade?, subject?, chapter?, language_code?}` | `Job` — `{job_id, job_type:"curriculum_ingest", status:"QUEUED"|"RUNNING"|..., progress_pct:1..100, result:{curriculum_id?}}` | ✅ [curriculum.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/api/curriculum.ts) + [jobs.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/api/jobs.ts) poll loop in CurriculumScreen. |
| GET    | `/curriculum`                  | 🔒         | `?class_grade=&subject=&state=&limit=&offset=`                           | Paginated `{total, curricula:CurriculumSummary[]}`                          | ✅ "MY CURRICULA" list. |
| GET    | `/curriculum/{id}`             | 🔒         | —                                                                       | `CurriculumDetail` — includes nested extracted lessons                     | ✅ Curriculum detail pane + offline save. |
| PATCH  | `/curriculum/{id}`             | 🔒👑      | Partial update metadata                                                 | Updated curriculum                                                         | ⏳ |
| DELETE | `/curriculum/{id}`             | 🔒👑      | —                                                                       | `{ok:true}`                                                                | ⏳ |
| GET    | `/jobs/{job_id}`               | 🔒         | —                                                                       | `Job` (see above)                                                          | ✅ Upload progress polling. |
| GET    | `/jobs`                        | 🔒👑      | `?status=&job_type=&limit=`                                             | Paginated jobs                                                             | ⏳ Admin. |
| POST   | `/jobs/{job_id}/cancel`        | 🔒👑      | —                                                                       | `{ok:true}`                                                                | ⏳ Admin. |

---

## 6. Lessons (`/lessons/*`)

| Method | URL                | Auth | Request                                            | Response                                                                      | Used |
|--------|--------------------|------|----------------------------------------------------|-------------------------------------------------------------------------------|------|
| GET    | `/lessons`         | 🔒   | `?curriculum_id=&class_grade=&subject=&search=&limit=15&offset=0` | `{total, limit, offset, lessons: LessonSummary[]}`                            | ✅ [lessons.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/api/lessons.ts). LessonsScreen paginated FlatList `onEndReached`. |
| GET    | `/lessons/{id}`    | 🔒   | —                                                  | `LessonDetail` — sections: learning_outcomes, vocabulary, activities, assessments | ✅ Open in detail view; "Save offline" button. |
| POST   | `/lessons`         | 🔒👑 | Lesson creation body                               | Created lesson                                                                | ⏳ Authoring UI later. |
| PATCH  | `/lessons/{id}`    | 🔒👑 | Partial lesson update                              | Updated lesson                                                                | ⏳ |
| DELETE | `/lessons/{id}`    | 🔒👑 | —                                                  | `{ok:true}`                                                                   | ⏳ |

---

## 7. Worksheets (`/worksheets/*`)

| Method | URL                            | Auth | Request                                                                                                          | Response                                                                                                                                           | Used |
|--------|--------------------------------|------|------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|------|
| POST   | `/worksheets/generate`        | 🔒   | `{class_grade?, subject?, topic?, target_lang:"sat|unr|hoc|hin", worksheet_type:FILL_BLANKS|MCQ|MATCHING|PICTURE_BASED, difficulty:EASY|MEDIUM|HARD, question_count?, curriculum_id?, lesson_id?, vocabulary_ids?}` | `GeneratedWorksheet` — `{id, worksheet_type, difficulty, questions:[MCQ|FillBlanks|Matching|Picture], metadata:{usage_rights, ai_model, tokens}}` | ✅ [worksheets.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/api/worksheets.ts). Render per-kind + Regenerate / Save / View HTML / Export PDF. |
| GET    | `/worksheets/{id}/html`       | 🔒   | —                                                                                                                | Bilingual HTML page download                                                                                                                      | ✅ `htmlUrl(id)` helper opens in system browser. |
| GET    | `/worksheets/{id}/pdf`        | 🔒   | —                                                                                                                | PDF download                                                                                                                                      | ✅ `pdfUrl(id)` → share via expo-sharing + expo-file-system. |
| GET    | `/worksheets/{id}`            | 🔒   | —                                                                                                                | `GeneratedWorksheet`                                                                                                                              | ⏳ |
| DELETE | `/worksheets/{id}`            | 🔒   | —                                                                                                                | `{ok:true}`                                                                                                                                       | ⏳ |

---

## 8. Classrooms + Context

Temporary classroom session context. NOT permanently stored unless the teacher explicitly saves.

| Method | URL                               | Auth | Request                                                                                  | Response                                                                 | Used |
|--------|-----------------------------------|------|------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|------|
| POST   | `/classrooms`                     | 🔒   | `{class_grade?, subject?, topic?, learning_outcome?, target_language?, expires_in_minutes?}` | `ClassroomSession:{session_id, teacher_id, state:"ACTIVE", expires_at, ...}` | ✅ HomeScreen "Start classroom session" → session-context tag used for better translation. Frontend falls back to a fully local `LocalSessionContext` object if network is down. See [classrooms.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/api/classrooms.ts) + AppContext `startClassroomSession`. |
| GET    | `/classrooms/active`              | 🔒   | —                                                                                        | `ClassroomSession|null`                                                  | ✅ Active session restore on app boot. |
| POST   | `/classrooms/{id}/end`            | 🔒   | —                                                                                        | `{ended:true, session_id, dialogue_line_count}`                          | ✅ HomeScreen "End session". |
| POST   | `/context/{session_id}/items`     | 🔒   | `{role:"teacher"|"student"|"assistant", source, target?, medium?, metadata?}`            | `{id, ok:true}` — appends to the server-side ephemeral dialogue log      | ✅ `appendContextDialogue()` in AppContext. |
| GET    | `/context/{session_id}`           | 🔒   | `?limit=100&offset=0`                                                                    | `DialogueContext:{session_id, topic, items:[...]}`                        | ✅ `contextApi.get()`. |
| POST   | `/context/{session_id}/command`   | 🔒   | `{command:"SUMMARY"|"TOPIC"|"VOCABULARY"|"GENERATE_QUESTIONS"|"CLEAR", payload?}`       | Command result                                                           | ⏳ Long-press menu later. |

---

## 9. Sync / Device / Models / Flashcards

| Method | URL                       | Auth | Request                                                                    | Response                                                                | Used |
|--------|---------------------------|------|---------------------------------------------------------------------------|-------------------------------------------------------------------------|------|
| GET    | `/sync/manifest`          | 🔒   | `?lang=sat`                                                                | `SyncManifest:{manifest_version, generated_at, sections:[{id,checksum,size_bytes}], language_pack_ref}` | ✅ Settings "Sync now" + `useBackgroundHydration`. See [sync.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/api/sync.ts). |
| POST   | `/sync/delta`             | 🔒   | `{client_version, language_code, client_checksums}`                        | `DeltaResponse:{to_update, to_delete, missing_sections, server_manifest_version}` | ✅ Future incremental offline sync. |
| POST   | `/sync/upload`            | 🔒   | `{device_id, offline_sessions:[], offline_utterances:[]}`                  | `{applied:true, new_server_items:[]}`                                   | ✅ Future bidirectional sync. |
| POST   | `/devices/register`       | 🔒   | `{device_id, make, model, os_version, app_version, form_factor}`           | `{id, ok:true}`                                                         | ✅ AppContext boot: per-install UUID stored. |
| GET    | `/models`                 | 🔒👑| —                                                                          | List of available AI models                                             | ⏳ Admin. |
| GET    | `/flashcards`             | 🔒   | `?lesson_id=&lang=&due_only=`                                              | Flashcard list                                                          | ⏳ Vocab practice later. |
