# Palash — Setup Instructions

An educational Android-first mobile app for teachers. **React Native (Expo SDK 57) + TypeScript frontend** on top of an existing **Python FastAPI + SQLite/PostgreSQL + JWT + AI services backend**.

All backend routes, auth, DB tables, and AI translation/speech pipelines are reused **as-is** from the existing `backend/` directory. No backend routes were renamed, removed, or rewritten.

---

## 0. Prerequisites

| Layer     | Minimum version | Notes                                           |
|-----------|-----------------|-------------------------------------------------|
| Python    | 3.10+           | For the FastAPI backend.                        |
| Node.js   | 20+             | For the Expo / React Native build.              |
| npm       | 9+              | Bundled with Node 20.                           |
| Java      | 17              | Only if you build native APK (EAS/local build). |
| Android   | 9 (API 28)      | Target devices (low-cost tablets / phones).     |
| Expo Go   | latest          | Optional; fastest way to run on device during dev. |

---

## 1. Start the existing FastAPI backend

The backend was NOT modified in this deliverable (see `NEW_ENDPOINTS.md`). Start it the same way you always have. Example:

```bash
# from repo root PALASH/
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell)
# source .venv/bin/activate     # macOS / Linux

pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify:

- Health check:  `curl http://127.0.0.1:8000/health`
- OpenAPI docs:  http://127.0.0.1:8000/api/v1/docs
- Redoc:         http://127.0.0.1:8000/api/v1/redoc

The frontend calls every endpoint under the `/api/v1` prefix.

### Important: the backend must listen on 0.0.0.0 (not 127.0.0.1)

An Android emulator or a real Android device on the same LAN cannot reach `127.0.0.1` on your laptop. `--host 0.0.0.0` makes the backend reachable.

---

## 2. Install and run the React Native frontend

```bash
cd palash-mobile
npm install --no-audit --no-fund   # already run; use this on a fresh clone
```

Optional native-capability packages (already installed via `npx expo install` for SDK 57):

```
expo-speech, expo-file-system, expo-sharing, expo-av, @react-native-community/netinfo
```

### 2a. Configure `API_BASE_URL`

The frontend **never hardcodes localhost**. The base URL is resolved in order by [env.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/utils/env.ts):

1. `EXPO_PUBLIC_API_BASE_URL` environment variable (highest priority)
2. `expo.extra.API_BASE_URL` in `app.json`
3. **Dev auto-detect**:
   - Android emulator → `http://10.0.2.2:8000`
   - iOS simulator / web → `http://127.0.0.1:8000`
4. **Production** → `https://palash.example.com` (placeholder, replace before release)

To set it via env var on Windows PowerShell:

```powershell
$env:EXPO_PUBLIC_API_BASE_URL="http://192.168.1.42:8000"
npx expo start
```

Or via `app.json` `expo.extra.API_BASE_URL` for a static value.

### 2b. Start the Expo dev server

```bash
cd palash-mobile
npx expo start          # opens the Expo dev menu
# press 'a' to open Android emulator
# or scan QR with Expo Go on a real device on the same Wi-Fi
```

---

## 3. First-run onboarding

1. Open the app — you land on the **Login** screen.
2. Tap **Create Account** → Register (calls `POST /api/v1/auth/register` on the existing backend).
3. After register, the frontend auto-calls `POST /api/v1/auth/login` and stores the JWT access + refresh tokens securely via AsyncStorage.
4. **Onboarding flow** (4 steps):
   - Step 1 – Teacher profile: full name, school name.
   - Step 2 – Preferred tribal language.
   - Step 3 – Classroom noise calibration (real audio-permission stub; ready for the real noise-filter service).
   - Step 4 – Teacher voice enrollment (real recording stub; ready to POST to the voice pipeline).
5. On submit, profile is sent to the backend via `PATCH /api/v1/auth/me`.
6. Land on **Home** with a classroom-session card and 6 feature tiles.

---

## 4. Verifying end-to-end integration

| Action in UI           | Frontend calls → FastAPI route                         | Failures surface as                        |
|------------------------|---------------------------------------------------------|---------------------------------------------|
| Register / Login       | `/api/v1/auth/register`, `/api/v1/auth/login`           | Human-friendly error cards, never raw JSON. |
| Tap "Heartbeat OK"     | `GET /health` (60 s ping + on app resume)               | Flips `networkStatus` to `OFFLINE_READY`.   |
| Text → Translate       | Cache-first → `POST /api/v1/translation/translate`      | Falls back to fuzzy local cache if offline. |
| Play pronunciation     | `POST /api/v1/speech/synthesize`                        | Alert with TTS form + transliteration.      |
| Upload curriculum PDF  | `POST /api/v1/curriculum/upload` → `GET /api/v1/jobs/{id}` poll every 2.2 s | 5-stage pipeline row + progress bar. |
| Generate worksheet     | `POST /api/v1/worksheets/generate`                      | MCQ / Fill blanks / Match / Picture render. |
| Browse lessons         | `GET /api/v1/lessons?limit=15&offset=N` (paginated)     | `FlatList` + `onEndReached` lazy load.     |
| Save lesson offline    | `offlineDB.saveOfflineLesson()` (AsyncStorage)          | Shows in "OFFLINE" tab even with no server. |
| Start classroom session | `POST /api/v1/classrooms` → fallback to LocalSessionContext if offline | Classroom context used for better translation quality. |
| Sync now (Settings)    | `GET /api/v1/translation/phrases` + `GET /api/v1/sync/manifest` | Flips `SYNCING` → `ONLINE`. |

---

## 5. Project layout (frontend)

```
palash-mobile/
├─ App.tsx                              Classic entry (expo-router is NOT used)
├─ app.json                             Expo config, package name = com.palash.app
├─ package.json                         main = App.tsx, typecheck = tsc --noEmit
└─ src/
   ├─ api/                              ✅ Typed API layer (UI → Services → API → Backend)
   │  ├─ client.ts                      axios + tokenStore + 401 refresh mutex + ApiResult<T>
   │  ├─ auth.ts, translation.ts, speech.ts, curriculum.ts
   │  ├─ lessons.ts, worksheets.ts, classrooms.ts, context.ts
   │  ├─ languages.ts, language_packs.ts, sync.ts, devices.ts
   │  ├─ flashcards.ts, jobs.ts, models.ts, health.ts
   │  └─ index.ts                       barrel
   ├─ components/                       13 reusable neo-brutalist components
   ├─ screens/                          All 11 required screens
   ├─ navigation/                       Stack navigator, auth-gated
   ├─ store/AppContext.tsx              Auth / profile / network / session / settings
   ├─ database/database.ts              AsyncStorage offline engine (SQLite-ready interface)
   ├─ services/                         offlineCache.ts / audioService.ts / hooks
   ├─ theme/                            colors, typography, spacing, NeoStyles presets
   ├─ models/index.ts                   Full TS mirror of backend Pydantic models
   └─ utils/env.ts                      API_BASE_URL resolver (never localhost-assumed)
```

---

## 6. Production checklist

Before a release build:

1. Replace the production `API_BASE_URL` in one of the two supported ways (env var or `app.json` `expo.extra.API_BASE_URL`).
2. Build via EAS Build: `eas build -p android --profile production`.
3. **Never** commit JWT secrets, Supabase credentials, or model credentials. All of those live on the backend only.
4. Ship language packs OTA via the existing `/api/v1/language-packs` download endpoint.
5. Use `/api/v1/sync/manifest` + `/api/v1/sync/delta` for incremental offline updates.

---

## 7. Common issues & fixes

| Symptom                                                      | Fix                                                          |
|--------------------------------------------------------------|--------------------------------------------------------------|
| "Unable to connect" on Android emulator, backend is running. | Backend must bind `0.0.0.0`. Set `EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8000`. |
| "Unable to connect" on real device.                          | Put phone + laptop on same Wi-Fi. Use laptop LAN IP, not `localhost`. |
| 401 Unauthorized repeating after login.                      | Refresh token single-flight mutex in `client.ts` should handle it. If the backend rotated secret, log out once manually. |
| 403 Forbidden on curriculum upload.                          | Backend requires ADMIN or CURRICULUM_MANAGER role; assign via backend seed. |
| Translation returns 501 on /speech/translate.                | INTENTIONAL — backend comment block says ASR is removed from server; frontend runs stubbed on-device ASR in VoiceTranslation and only POSTs resulting utterances to `/speech/utterances`. |
