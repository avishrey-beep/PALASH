# Palash — Frontend ↔ Backend communication architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│  Android Device / Emulator (React Native + Expo SDK 57 + TypeScript)  │
│                                                                       │
│  ┌───────────────┐    ┌──────────────────┐    ┌──────────────────┐    │
│  │   UI Screens  │───▶│  Domain Services  │───▶│  src/api/*      │    │
│  │  (11 screens) │    │ offlineCache.ts   │    │ client.ts ← JWT │    │
│  └───────────────┘    │  audioService.ts  │    │  + typed APIs   │    │
│       ▲               │ useBackgroundHydr │    └──────┬─────────┘    │
│       │               └────────┬─────────┘           │ axios          │
│       │                        │                       ▼              │
│       │                        │               ┌───────────────┐     │
│       │                        │               │  AsyncStorage │     │
│       │                        │               │ (offline DB)  │     │
│       │                        │               └──────┬────────┘     │
│       │                        │                      │              │
│       └──────── on-device data ◄──────────────────────┘              │
│                                     HTTPS / LAN                       │
└─────────────────────────────────────────┬─────────────────────────────┘
                                          │
                                          ▼
                   ┌────────────────────────────────────────┐
                   │  Python FastAPI @ uvicorn:8000         │
                   │  prefix = /api/v1  (except /health)    │
                   │                                        │
                   │  Depends(get_current_user) → JWT check │
                   │  → Pydantic request / response models  │
                   │  → Supabase PG / SQLite via existing   │
                   │    DB clients in backend/app/          │
                   │  → AI service layer (translation,      │
                   │    TTS, worksheet gen, curric ingest)  │
                   │                                        │
                   │ Routers: auth devices languages        │
                   │          curriculum lessons             │
                   │          translation speech             │
                   │          classrooms context worksheets │
                   │          flashcards language_packs     │
                   │          models sync jobs               │
                   └────────────────────────────────────────┘
                                          │
                                          ▼
                       Supabase PostgreSQL / local SQLite
                           + storage/* (uploads, exports)
```

---

## 1. Strict layering rule

A screen component **never** calls `fetch` or `axios` directly. All network logic lives under `src/api/`.
All offline logic lives under `src/database/` and `src/services/`. Screens only get/save observables via:

- Hooks: `useApp()` for global auth/user/network/session state.
- Domain functions: `translationApi.translate()`, `offlineDB.saveOfflineLesson()`, etc.
- Return type convention: **every** public API call returns `ApiResult<T> = { ok:true, data:T } | { ok:false, data:null, error:ApiError }`. Functions never throw across module boundaries (the try/catch lives inside `client.wrap<T>()`). This guarantees screens always have an `if (res.ok)` branch with friendly error UI.

---

## 2. Centralised HTTP client + JWT lifecycle

File: [client.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/api/client.ts)

### Token store (`TokenStore`)

| Aspect           | Mechanism                                                   |
|------------------|-------------------------------------------------------------|
| Persistence      | AsyncStorage keys `@palash/access_token`, `@palash/refresh_token`. Written **atomically** on every set/clear. |
| Hydration        | `tokenStore.init()` is `await`-ed inside the first request interceptor **and** inside `AppContext.load()` on boot. Both paths are idempotent (read once, cache in module-level fields). |
| Transport        | Request interceptor `attachAuth` adds `Authorization: Bearer <access_token>` — unless `config.__skipAuth` (used for e.g. `POST /auth/login` itself). |

### 401 refresh mutex (single-flight pattern)

```ts
let refreshPromise: Promise<void> | null = null;
```

1. Response interceptor sees a 401 on an authenticated call.
2. If `refreshPromise == null`: kick off `POST /auth/refresh` → on success update both tokens; finally `refreshPromise = null`.
3. If `refreshPromise != null` (another concurrent request already started refreshing): `await` the **same** promise.
4. Both callers then retry their original failed request with the new header.

This prevents the classic "refresh token is single-use; two 401s at once → one call fails" bug.

### Network / error mapping

The interceptor converts errors to classes:

| Error class        | When                                                                 | How screens react                                                    |
|--------------------|----------------------------------------------------------------------|----------------------------------------------------------------------|
| `OfflineError`     | `ERR_NETWORK`, `ECONNABORTED`, timeout without any response byte.    | `DataView` shows "Unable to reach the server right now. Your saved offline content is still available." + Retry button. Translation falls back to local fuzzy cache. |
| `ApiError`         | Any HTTP 4xx/5xx. Stores `.status`, `.detail` (FastAPI `response.data.detail` human-readable string), `.code`. | Friendly string in card; **never** a raw JSON stack trace.           |

---

## 3. Configuration & base URL (never hardcode `localhost`)

File: [env.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/utils/env.ts)

Resolution order, **highest to lowest priority**:

1. Env var `EXPO_PUBLIC_API_BASE_URL` — Expo auto-injects this at build; set it on Windows via `$env:EXPO_PUBLIC_API_BASE_URL="http://192.168.1.42:8000"`.
2. `app.json → expo.extra.API_BASE_URL` — for static installs without env vars.
3. **Dev auto-detect:**
   - Android emulator → `http://10.0.2.2:8000` (the magic address of the host loopback inside AOSP).
   - iOS simulator or web → `http://127.0.0.1:8000`.
4. **Production default:** `https://palash.example.com` (replace before first release build).

---

## 4. Cache-first translation pipeline

Implemented in [translation.ts → translate()](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/api/translation.ts).

```
1. Empty input → return EMPTY_INPUT short-circuit.
2. offlineDB.getPhrase(text, target_lang)
   ├─ hit → return TIER_0_LOCAL_CACHE instantly.
   └─ miss → continue.
3. apiClient.safePost("/translation/translate", body)
   ├─ ok && translated_text →
   │     offlineDB.savePhrase(text, target, translated)  (catch ignored)
   │     return data + tier TIER_1_SERVER_CACHE / TIER_2_TM / TIER_3_MODEL.
   └─ error → step 4.
4. offlineDB.getPhraseApprox(text, target_lang)
   ├─ hit → return TIER_0_LOCAL_CACHE_FUZZY with confidence 0.7.
   └─ miss → throw the original server error (handled by screen UI as OfflineError).
```

The teacher therefore sees **"0 ms / instant"** on any repeated classroom phrase, even if the server is offline for an entire lesson.

---

## 5. Offline-first architecture

### Connectivity state machine (stored in AppContext networkStatus)

```
ONLINE ──► SYNCING (background hydration) ──► ONLINE
 │
 └──► any request fails with OfflineError ──► OFFLINE
      │
      └──► local tier-0 phrases + saved lessons exist ──► OFFLINE_READY
```

The `ConnectivityBadge` component (from PalBadge) displays this everywhere in the header.
The UI never shows "Error" with a red screen for an offline condition — it shows a neutral banner "Your saved offline content is still available."

### AsyncStorage OfflineStorageEngine (SQLite-ready interface)

File: [database.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PLASH/palash-mobile/src/database/database.ts)

| Method                                | Entity stored                     | Sync counterpart                                     |
|---------------------------------------|-----------------------------------|------------------------------------------------------|
| `savePhrase / getPhrase / getPhraseApprox / savePhrasesBulk / getAllPhrases` | `PhraseCache` | `GET /translation/phrases` + `useBackgroundHydration` |
| `saveOfflineLesson / getOfflineLesson / getOfflineLessons / deleteOfflineLesson` | `StoredLesson` | `GET /lessons/{id}` Save button in detail            |
| `saveWorksheet / getSavedWorksheets / deleteWorksheet` | `SavedWorksheet` | Future `POST /worksheets/{id}/fork?`                 |
| `saveSyncManifest / getSyncManifest`  | `SyncManifest` cache entry | `GET /sync/manifest`                           |
| `getSessionContext / saveSessionContext / clearSessionContext` | ephemeral classroom dialogue log | `POST /context/items` — only pushes **additional** rows online; local log is the source of truth during a lesson. |
| `saveSettings / getSettings`          | Teacher preferences: TTS rate, defaults, auto-save | PATCH `/auth/me` |
| `getDeviceId / saveDeviceId`          | Per-install UUID for crash/sync attribution | `POST /devices/register` |

All methods are promise-based, interface-compatible with a future `expo-sqlite` migration where we'd rewrite storage.ts once while keeping the rest of the app identical.

---

## 6. Temporary classroom context

"Do not permanently store every classroom conversation automatically."

The server-side `/classrooms` session is:
- `expires_in_minutes` default 120 min (sent on create).
- Explicitly ended via HomeScreen "End session" button → `POST /classrooms/{id}/end`.
- The dialogue log pushed to `/context/{session_id}/items` during the lesson is **ephemeral** on the server — not mirrored into permanent lessons/history.
- On the frontend, `LocalSessionContext` (saved in AsyncStorage under the session key) is automatically cleared the next time a new session is started or when the teacher taps "Clear session" in Settings.

---

## 7. Typed end-to-end

Every backend Pydantic model is mirrored as a TypeScript interface in [models/index.ts](file:///d:/MY%20STUFF/ProjectBasedLearning/PALASH/palash-mobile/src/models/index.ts).
Examples: `TranslationRequest → TranslationResponse`, `Job`, `JobStatus`, `LessonDetail`, `GeneratedWorksheet`, `WorksheetQuestionMCQ | WorksheetQuestionFillBlanks | WorksheetQuestionMatching | WorksheetQuestionPictureBased`, `ClassroomSession`, `CachedPhrase`, `SyncManifest`, `HealthResponse`.

The API client wraps each route with a generic parameter:
```ts
apiClient.safePost<GeneratedWorksheet>('/worksheets/generate', body)
```

Result: refactoring a backend field name in VSCode will highlight **every** frontend consumer immediately. No surprise runtime `undefined`s because the shape drifted.

---

## 8. Error handling contract in screens

Every screen that triggers network calls follows this UI pattern (wrapped by `<DataView>` component):

```
 Loading (spinner + "Loading…")
    │
    ├─ Success → data render
    │
    ├─ OfflineError →
    │     title:   "⚠ Unable to reach the server right now."
    │     body:    "Your saved offline content is still available."
    │     button:  [Retry]  (re-fetches)
    │
    └─ ApiError →
          title:   "✕ Something went wrong"
          body:    e.detail || "Please try again in a moment."
          button:  [Retry]
```

`TextTranslation` adds one extra fall-through branch on OfflineError:
> "Translation used locally cached content where available."

— because cache-first translate may still return a valid fuzzy result even if the network call failed.

---

## 9. Security summary: what stays OFF the device

| Secret                           | Lives on…                              |
|----------------------------------|----------------------------------------|
| JWT signing secret / keypair     | Backend only (env / config).           |
| Supabase connection string       | Backend only.                          |
| Database credentials             | Backend only.                          |
| AI provider API keys             | Backend AI service layer only.         |
| Access token (short-lived 120m)  | AsyncStorage (encrypted-at-rest via device Keystore in production builds). |
| Refresh token (30 d, single-use) | AsyncStorage; rotated on each 401.    |

Zero of the above are hardcoded in `palash-mobile/`.
