import type {
  ExecutionLanguage,
  ExecutionResult,
  VisualizationMode,
  VisualizationRequestMode,
} from '../types/execution';
import type { AuthSessionState } from '../types/auth';
import type { ExamCategory, ExamSession, ExamSubmissionResult } from '../types/exam';
import type {
  LearningCategory,
  LearningInsight,
  LearningLesson,
  LearningLessonSummary,
  LearningProgress,
} from '../types/learning';

const DEFAULT_API_BASE_URL = '/api/v1';
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL).replace(
  /\/+$/,
  '',
);

interface ApiSuccess<T> {
  status: 'success';
  data: T;
  meta?: Record<string, unknown>;
}

export class UnauthorizedError extends Error {
  constructor(message = '로그인이 필요합니다.') {
    super(message);
    this.name = 'UnauthorizedError';
  }
}

export class ApiRequestError extends Error {
  constructor(message = '요청 처리 중 오류가 발생했습니다.') {
    super(message);
    this.name = 'ApiRequestError';
  }
}

export class ApiConnectionError extends Error {
  constructor(message = '백엔드 서버에 연결하지 못했습니다. 서버가 켜져 있는지 확인해 주세요.') {
    super(message);
    this.name = 'ApiConnectionError';
  }
}

export function getErrorMessage(error: unknown, fallbackMessage: string) {
  return error instanceof Error && error.message ? error.message : fallbackMessage;
}

export function shouldReportError(error: unknown) {
  return !(
    error instanceof UnauthorizedError ||
    error instanceof ApiRequestError ||
    error instanceof ApiConnectionError
  );
}

function isAbsoluteUrl(value: string) {
  return /^https?:\/\//i.test(value);
}

function buildUrl(path: string, params?: Record<string, string | undefined>) {
  const rawUrl = `${API_BASE_URL}${path}`;
  const url = isAbsoluteUrl(rawUrl)
    ? new URL(rawUrl)
    : new URL(rawUrl, window.location.origin);

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value) {
        url.searchParams.set(key, value);
      }
    });
  }
  return url.toString();
}

function extractPayloadMessage(payload: unknown) {
  if (!payload || typeof payload !== 'object') {
    return null;
  }

  const data = payload as { detail?: unknown; message?: unknown };
  if (typeof data.detail === 'string') {
    return data.detail;
  }
  if (typeof data.message === 'string') {
    return data.message;
  }
  return null;
}

async function parseResponse<T>(response: Response): Promise<T> {
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (response.status === 401) {
      window.dispatchEvent(new CustomEvent('codeviz:auth-required'));
      throw new UnauthorizedError(extractPayloadMessage(payload) || '로그인이 필요합니다.');
    }
    throw new ApiRequestError(extractPayloadMessage(payload) || '요청 처리 중 오류가 발생했습니다.');
  }

  return payload as T;
}

async function apiFetch(pathOrUrl: string, init?: RequestInit) {
  const targetUrl = pathOrUrl.startsWith('http://') || pathOrUrl.startsWith('https://')
    ? pathOrUrl
    : buildUrl(pathOrUrl);

  try {
    return await fetch(targetUrl, {
      credentials: 'include',
      ...init,
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiConnectionError();
    }
    throw error;
  }
}

export async function fetchLearningCategories(): Promise<LearningCategory[]> {
  const response = await apiFetch('/learning/categories');
  const payload = await parseResponse<ApiSuccess<LearningCategory[]>>(response);
  return payload.data;
}

export async function fetchLearningLessons(params?: {
  categoryId?: string;
  visualizationMode?: VisualizationMode;
  language?: string;
}): Promise<LearningLessonSummary[]> {
  const response = await apiFetch(
    buildUrl('/learning/lessons', {
      categoryId: params?.categoryId,
      visualizationMode: params?.visualizationMode,
      language: params?.language,
    }),
  );
  const payload = await parseResponse<ApiSuccess<LearningLessonSummary[]>>(response);
  return payload.data;
}

export async function fetchLearningLessonDetail(lessonId: string): Promise<LearningLesson> {
  const response = await apiFetch(`/learning/lessons/${lessonId}`);
  const payload = await parseResponse<ApiSuccess<LearningLesson>>(response);
  return payload.data;
}

export async function fetchLearningInsights(): Promise<LearningInsight> {
  const response = await apiFetch('/learning/insights');
  const payload = await parseResponse<ApiSuccess<LearningInsight>>(response);
  return payload.data;
}

export async function markLearningLessonStudied(lessonId: string): Promise<LearningProgress> {
  const response = await apiFetch(`/learning/lessons/${lessonId}/progress`, {
    method: 'POST',
  });
  const payload = await parseResponse<ApiSuccess<LearningProgress>>(response);
  return payload.data;
}

export async function executeCode(params: {
  language: ExecutionLanguage;
  sourceCode: string;
  visualizationMode: VisualizationRequestMode;
  stdin?: string;
}): Promise<ExecutionResult> {
  const response = await apiFetch('/executions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      language: params.language,
      source_code: params.sourceCode,
      stdin: params.stdin ?? '',
      visualizationMode: params.visualizationMode,
    }),
  });
  const payload = await parseResponse<ApiSuccess<ExecutionResult>>(response);
  return payload.data;
}

export async function fetchExamCategories(params?: { language?: ExecutionLanguage }): Promise<ExamCategory[]> {
  const response = await apiFetch(
    buildUrl('/exams/categories', {
      language: params?.language,
    }),
  );
  const payload = await parseResponse<ApiSuccess<ExamCategory[]>>(response);
  return payload.data;
}

export async function createExamSession(params: {
  categoryId: string;
  questionCount: number;
  language: ExecutionLanguage;
}): Promise<ExamSession> {
  const response = await apiFetch('/exams/sessions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      categoryId: params.categoryId,
      questionCount: params.questionCount,
      language: params.language,
    }),
  });
  const payload = await parseResponse<ApiSuccess<ExamSession>>(response);
  return payload.data;
}

export async function submitExamAnswer(params: {
  lessonId: string;
  sourceCode: string;
  language: ExecutionLanguage;
}): Promise<ExamSubmissionResult> {
  const response = await apiFetch('/exams/submissions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      lessonId: params.lessonId,
      sourceCode: params.sourceCode,
      language: params.language,
    }),
  });
  const payload = await parseResponse<ApiSuccess<ExamSubmissionResult>>(response);
  return payload.data;
}

export async function fetchAuthMe(): Promise<AuthSessionState | null> {
  const response = await apiFetch('/auth/me');
  const payload = await parseResponse<ApiSuccess<AuthSessionState | null>>(response);
  return payload.data;
}

export async function registerUser(params: {
  email: string;
  password: string;
  name: string;
}): Promise<AuthSessionState> {
  const response = await apiFetch('/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });
  const payload = await parseResponse<ApiSuccess<AuthSessionState>>(response);
  return payload.data;
}

export async function loginUser(params: {
  email: string;
  password: string;
}): Promise<AuthSessionState> {
  const response = await apiFetch('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });
  const payload = await parseResponse<ApiSuccess<AuthSessionState>>(response);
  return payload.data;
}

export async function logoutUser(): Promise<void> {
  const response = await apiFetch('/auth/logout', {
    method: 'POST',
  });
  await parseResponse<ApiSuccess<boolean>>(response);
}
