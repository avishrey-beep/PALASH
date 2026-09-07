# Palash — New backend endpoints added in this deliverable

## Answer: **ZERO new endpoints were added.**

The existing FastAPI backend already contained every route required by the 11 screens of the Palash mobile app. This frontend was built strictly **on top of the existing backend** per the user's hard requirements:

> Do NOT build an independent mock frontend.
> Do NOT create fake API responses as the primary implementation.
> Do NOT replace the existing backend with Firebase, Supabase-only frontend calls, or another backend.
> FIRST inspect and understand the existing backend.
> THEN build the React Native frontend ON TOP OF that backend.
> Do NOT remove existing routes.
> Do NOT change existing API contracts unless absolutely necessary.

### Backend routers mounted at the time of the frontend build (`backend/app/api/v1/api.py:22-36`):

1.  `auth`           — register / login / refresh / me / logout
2.  `devices`        — register device ID for sync
3.  `languages`      — language metadata
4.  `curriculum`     — upload / list / detail / update / delete
5.  `lessons`        — paginated list / detail / create / update / delete
6.  `translation`    — translate / phrases / glossary / review tasks
7.  `speech`         — translate (intentionally 501) / synthesize / utterances
8.  `classrooms`     — create session / active / end
9.  `context`        — append dialogue items / fetch context / run commands
10. `worksheets`     — generate / detail / html / pdf / delete
11. `flashcards`     — practice scheduling
12. `language_packs` — list / download
13. `models`         — available AI model metadata (admin)
14. `sync`           — manifest / delta / upload
15. `jobs`           — curriculum ingest progress polling
16. Plus the global `/health` check mounted in `backend/app/main.py` outside the `/api/v1` prefix.

### Items that needed ZERO backend changes:

- **Authentication:** JWT access + refresh tokens, bcrypt password hashing, all in the existing `backend/app/core/security.py` + `auth_service.py`. Frontend matches exactly (see `src/api/client.ts` single-flight refresh mutex).
- **Curriculum ingestion:** Async `Job` model + `progress_pct` exactly match the 5-stage UI row (`UPLOADING → PROCESSING → EXTRACTING → PREPARING_TRANSLATIONS → READY`).
- **Worksheet generation:** Supported types enum `FILL_BLANKS | MCQ | MATCHING | PICTURE_BASED` + difficulties `EASY | MEDIUM | HARD` exactly match the WorksheetGeneratorScreen SegmentedControl.
- **Classroom sessions:** Ephemeral, expireable (default 120 min), optional topic/learning outcome fields exactly match the HomeScreen session card.
- **Translation cache hierarchy:** Backend already returns `tier_used` (`TIER_0_LOCAL_CACHE`, `TIER_0_LOCAL_CACHE_FUZZY`, `TIER_1_SERVER_CACHE`, etc.) which the frontend uses to show the `cache-first` badge.

### Backend `POST /speech/translate` returning 501 — intentional, NOT fixed

Per the explicit comment block in `backend/app/api/v1/endpoints/speech.py:33-44`, the server does **not** run ASR (requires heavy GPU). The frontend was built to honor this:

- VoiceTranslationScreen runs an **on-device ASR stub** (ready to be swapped for a real on-device Whisper / IndicConformer model once bundled).
- The resulting recognized Hindi text is then sent as a structured utterance to the real endpoint: `POST /speech/utterances`.
- The translation itself continues to go through `POST /translation/translate` with the classroom-session topic as context.
