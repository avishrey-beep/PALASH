/**
 * Backend API client for the PALASH FastAPI server.
 *
 * All requests go through this module so the base URL is configured in one
 * place. The client stores the JWT access token in memory (not AsyncStorage)
 * so it is cleared on app restart -- the user must log in again, which is
 * acceptable for a teacher app.
 *
 * Offline behaviour: every method catches network errors and throws an
 * `ApiError` with `isNetworkError: true` so callers can fall back gracefully.
 */

// Change this to your backend URL. For local dev with Expo Go on a physical
// device, use your machine's LAN IP (e.g. http://192.168.1.x:8000).
// For Android emulator use http://10.0.2.2:8000.
// For iOS simulator use http://localhost:8000.
export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

const API_V1 = `${API_BASE_URL}/api/v1`;

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly isNetworkError = false,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// In-memory token store (cleared on app restart).
let _accessToken: string | null = null;
let _refreshToken: string | null = null;

export const tokenStore = {
  setTokens(access: string, refresh: string) {
    _accessToken = access;
    _refreshToken = refresh;
  },
  clearTokens() {
    _accessToken = null;
    _refreshToken = null;
  },
  getAccessToken() {
    return _accessToken;
  },
  getRefreshToken() {
    return _refreshToken;
  },
  isAuthenticated() {
    return _accessToken !== null;
  },
};

const TIMEOUT_MS = 8000;

async function fetchWithTimeout(
  url: string,
  options: RequestInit,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : 'Network request failed';
    throw new ApiError(0, message, true);
  } finally {
    clearTimeout(timer);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  authenticated = true,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (authenticated && _accessToken) {
    headers['Authorization'] = `Bearer ${_accessToken}`;
  }

  const res = await fetchWithTimeout(`${API_V1}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {
      // ignore parse error
    }
    throw new ApiError(res.status, detail);
  }

  // 204 No Content
  if (res.status === 204) return undefined as unknown as T;

  return res.json() as Promise<T>;
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    username: string;
    full_name: string | null;
    roles: string[];
    school_id: string | null;
  };
}

export interface RegisterResponse {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  school_id: string | null;
  roles: string[];
}

export interface UserProfileResponse {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  school_id: string | null;
  preferred_language: string | null;
  roles: string[];
}

export const authApi = {
  async login(username: string, password: string): Promise<LoginResponse> {
    return request<LoginResponse>(
      '/auth/login',
      {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      },
      false,
    );
  },

  async register(data: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
    school_id?: string;
  }): Promise<RegisterResponse> {
    return request<RegisterResponse>(
      '/auth/register',
      {
        method: 'POST',
        body: JSON.stringify(data),
      },
      false,
    );
  },

  async getMe(): Promise<UserProfileResponse> {
    return request<UserProfileResponse>('/auth/me');
  },

  async updateMe(patch: {
    full_name?: string;
    preferred_language?: string;
  }): Promise<UserProfileResponse> {
    return request<UserProfileResponse>('/auth/me', {
      method: 'PATCH',
      body: JSON.stringify(patch),
    });
  },

  async refresh(refreshToken: string): Promise<{ access_token: string }> {
    return request<{ access_token: string }>(
      '/auth/refresh',
      {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken }),
      },
      false,
    );
  },
};

// ─── Translation ─────────────────────────────────────────────────────────────

export interface BackendTranslationResponse {
  translated_text: string | null;
  source_lang: string;
  target_lang: string;
  source_text: string;
  tier_used: string;
  confidence: number | null;
  latency_ms: number | null;
  pronunciation?: string | null;
  script?: string | null;
  note?: string | null;
}

export const translationApi = {
  async translate(
    text: string,
    sourceLang: string,
    targetLang: string,
    contextTopic?: string,
  ): Promise<BackendTranslationResponse> {
    return request<BackendTranslationResponse>('/translation/translate', {
      method: 'POST',
      body: JSON.stringify({
        text,
        source_lang: sourceLang,
        target_lang: targetLang,
        context_topic: contextTopic,
      }),
    });
  },
};

// ─── Lessons ─────────────────────────────────────────────────────────────────

export interface BackendLesson {
  id: string;
  curriculum_id: string;
  unit_number: number;
  lesson_number: number;
  title_hindi: string;
  topic: string;
  learning_outcomes?: string[];
  vocabulary?: Array<{ hindi: string; gloss?: string }>;
  activities?: string[];
  assessments?: string[];
  version?: number;
}

export interface BackendLessonListResponse {
  total: number;
  limit: number;
  offset: number;
  lessons: BackendLesson[];
}

export const lessonsApi = {
  async list(params?: {
    curriculum_id?: string;
    class_grade?: number;
    subject?: string;
    limit?: number;
    offset?: number;
  }): Promise<BackendLessonListResponse> {
    const qs = new URLSearchParams();
    if (params?.curriculum_id) qs.set('curriculum_id', params.curriculum_id);
    if (params?.class_grade != null)
      qs.set('class_grade', String(params.class_grade));
    if (params?.subject) qs.set('subject', params.subject);
    if (params?.limit != null) qs.set('limit', String(params.limit));
    if (params?.offset != null) qs.set('offset', String(params.offset));
    const query = qs.toString() ? `?${qs.toString()}` : '';
    return request<BackendLessonListResponse>(`/lessons${query}`);
  },

  async get(id: string): Promise<BackendLesson> {
    return request<BackendLesson>(`/lessons/${id}`);
  },
};

// ─── Curriculum ──────────────────────────────────────────────────────────────

export interface BackendCurriculum {
  id: string;
  title: string;
  state: string;
  board: string;
  class_grade: number;
  subject: string;
  current_version?: number;
  description?: string;
  lessons_count?: number;
  lessons?: BackendLesson[];
}

export const curriculumApi = {
  async list(params?: {
    class_grade?: number;
    subject?: string;
  }): Promise<BackendCurriculum[]> {
    const qs = new URLSearchParams();
    if (params?.class_grade != null)
      qs.set('class_grade', String(params.class_grade));
    if (params?.subject) qs.set('subject', params.subject);
    const query = qs.toString() ? `?${qs.toString()}` : '';
    return request<BackendCurriculum[]>(`/curriculum${query}`);
  },

  async get(id: string): Promise<BackendCurriculum> {
    return request<BackendCurriculum>(`/curriculum/${id}`);
  },
};

// ─── Worksheets ───────────────────────────────────────────────────────────────

export interface BackendWorksheet {
  id: string;
  title?: string;
  class_grade?: number;
  subject?: string;
  topic?: string;
  target_language?: string;
  questions?: Array<{
    id: string;
    type: string;
    prompt: string;
    options?: string[];
    answer?: string;
  }>;
  html_content?: string;
  pdf_path?: string;
}

export const worksheetsApi = {
  async generate(params: {
    class_grade: number;
    subject: string;
    topic: string;
    target_language: string;
    lesson_id?: string;
    question_count: number;
    difficulty?: string;
  }): Promise<BackendWorksheet> {
    return request<BackendWorksheet>('/worksheets/generate', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },
};
