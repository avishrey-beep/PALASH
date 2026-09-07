# Palash — Backend endpoints actively used by the React Native frontend

All of these endpoints are **already present** in the existing FastAPI app.
See `backend/app/api/v1/endpoints/*.py`. Nothing was added. See `NEW_ENDPOINTS.md`.

URL prefix (except `/health`): **`/api/v1`**

## Public (no JWT)

| # | Method | URL                     | When it is called in the app                            |
|---|--------|-------------------------|---------------------------------------------------------|
| 1 | GET    | `/health`               | Every 60 s heartbeat, plus every time the app is foregrounded (`AppState` 'active'). |
| 2 | POST   | `/auth/register`        | RegisterScreen → "Create Account" submit.              |
| 3 | POST   | `/auth/login`           | LoginScreen submit, plus implicit auto-login after successful register. |
| 4 | POST   | `/auth/refresh`         | `client.ts` response-interceptor when the backend replies 401 — single-flight refresh mutex, then the failed request is retried with the new access token. |
| 5 | GET    | `/languages`            | AppContext boot → hydrates the `LANGUAGES` picker (onboarding, settings, translate screens). |

## JWT-required (🔒) — Auth & profile

| # | Method | URL                     | When it is called                                        |
|---|--------|-------------------------|---------------------------------------------------------|
| 6 | GET    | `/auth/me`              | AppContext bootstrap: after tokenStore hydration, calls to fetch current teacher profile + merges into local settings. |
| 7 | PATCH  | `/auth/me`              | OnboardingScreen final submit (name / school / lang) + SettingsScreen "Save profile & preferences". |
| 8 | POST   | `/auth/logout`          | SettingsScreen logout button → also clears AsyncStorage tokens and wipes in-memory state. |
| 9 | POST   | `/devices/register`     | AppContext boot: generates a per-install UUID if none exists, then registers it for future sync. |

## 🔒 Translation + Speech (the core Palash feature)

| #  | Method | URL                          | When it is called                                                                 |
|----|--------|------------------------------|----------------------------------------------------------------------------------|
| 10 | POST   | `/translation/translate`     | TextTranslation submit, plus VoiceTranslation (after on-device ASR). Cache-first wrapper in `translation.ts` falls back to local exact / fuzzy cache on failure. |
| 11 | GET    | `/translation/phrases`       | `offlineCacheService.hydrateFromNetwork()` → "Sync now" in Settings, `useBackgroundHydration()` hook in HomeScreen. |
| 12 | POST   | `/speech/synthesize`         | TextTranslation "Pronounce" button. Returns IPA/script form and optional TTS audio URL. |
| 13 | POST   | `/speech/utterances`         | VoiceTranslation screen, after each successful on-device ASR → logged to server for cache / stats. Returns 501 is not applicable here; /speech/translate is 501. |

## 🔒 Curriculum + Jobs

| #  | Method | URL                          | When it is called                                                                 |
|----|--------|------------------------------|----------------------------------------------------------------------------------|
| 14 | POST   | `/curriculum/upload`         | CurriculumScreen "Upload & Process" → multipart PDF/DOCX/EPUB/TXT + metadata.   |
| 15 | GET    | `/curriculum`                | CurriculumScreen "MY CURRICULA" list (pull-to-refresh + initial mount).         |
| 16 | GET    | `/curriculum/{id}`           | CurriculumScreen open detail view.                                               |
| 17 | GET    | `/jobs/{job_id}`             | Polling every 2.2 s while ingest job status is QUEUED / RUNNING. Renders 5-stage Uploading→Processing→Extracting→Preparing translations→Ready row with progress bar. |

## 🔒 Lessons

| #  | Method | URL                | When it is called                                                                 |
|----|--------|--------------------|----------------------------------------------------------------------------------|
| 18 | GET    | `/lessons`         | LessonsScreen "ALL" tab — paginated `limit=15, offset=N` via `onEndReached` lazy load; also supports filter params. |
| 19 | GET    | `/lessons/{id}`    | LessonsScreen open detail. Falls back to `offlineDB.getOfflineLesson(id)` copy if it was saved before and network is down. |

## 🔒 Worksheets

| #  | Method | URL                     | When it is called                                                                 |
|----|--------|-------------------------|----------------------------------------------------------------------------------|
| 20 | POST   | `/worksheets/generate`  | WorksheetGeneratorScreen "Generate" + "Regenerate" buttons.                      |
| 21 | GET    | `/worksheets/{id}/html` | `htmlUrl()` helper — opens the printable bilingual worksheet in the system browser. |
| 22 | GET    | `/worksheets/{id}/pdf`  | `pdfUrl()` helper — downloads then shares PDF via expo-sharing / expo-file-system. |

## 🔒 Classrooms + Context (ephemeral)

| #  | Method | URL                             | When it is called                                                                 |
|----|--------|---------------------------------|----------------------------------------------------------------------------------|
| 23 | POST   | `/classrooms`                   | HomeScreen "Start classroom session".                                            |
| 24 | GET    | `/classrooms/active`            | AppContext restore: what was the last session?                                   |
| 25 | POST   | `/classrooms/{id}/end`          | HomeScreen "End session".                                                        |
| 26 | POST   | `/context/{session_id}/items`   | `AppContext.appendContextDialogue()` — every time a teacher translates/utters, it pushes to the ephemeral server log for this classroom session. |
| 27 | GET    | `/context/{session_id}`         | `contextApi.get()` — restores context on resume.                                 |

## 🔒 Language packs + Sync

| #  | Method | URL                 | When it is called                                                                 |
|----|--------|---------------------|----------------------------------------------------------------------------------|
| 28 | GET    | `/language-packs`   | SettingsScreen — list of available installable packs for offline AI/TTS.         |
| 29 | GET    | `/language-packs/{id}/download` | `downloadUrl()` helper — OTA install.                            |
| 30 | GET    | `/sync/manifest`    | SettingsScreen "Sync now" + background hydration → phrase cache + manifest.     |

### Total endpoints used by the frontend: **30**
(1 public health + 5 auth/language public + 24 JWT teacher-scoped)
