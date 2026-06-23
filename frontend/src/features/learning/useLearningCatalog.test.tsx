import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  fetchLearningCategories,
  fetchLearningInsights,
  fetchLearningLessonDetail,
  fetchLearningLessons,
  getErrorMessage,
  markLearningLessonStudied,
  shouldReportError,
} from '../../lib/api';
import type {
  LearningCategory,
  LearningInsight,
  LearningLesson,
  LearningLessonSummary,
  LearningProgress,
} from '../../types/learning';
import { useLearningCatalog } from './useLearningCatalog';

vi.mock('../../lib/api', () => ({
  fetchLearningCategories: vi.fn(),
  fetchLearningInsights: vi.fn(),
  fetchLearningLessonDetail: vi.fn(),
  fetchLearningLessons: vi.fn(),
  getErrorMessage: vi.fn((error: unknown, fallback: string) =>
    error instanceof Error ? error.message : fallback,
  ),
  markLearningLessonStudied: vi.fn(),
  shouldReportError: vi.fn(() => false),
}));

const mockedFetchLearningCategories = vi.mocked(fetchLearningCategories);
const mockedFetchLearningInsights = vi.mocked(fetchLearningInsights);
const mockedFetchLearningLessonDetail = vi.mocked(fetchLearningLessonDetail);
const mockedFetchLearningLessons = vi.mocked(fetchLearningLessons);
const mockedMarkLearningLessonStudied = vi.mocked(markLearningLessonStudied);
const mockedGetErrorMessage = vi.mocked(getErrorMessage);
const mockedShouldReportError = vi.mocked(shouldReportError);

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function buildCategory(id = 'category-1'): LearningCategory {
  return {
    id,
    name: '기초 개념',
    description: '기초 학습',
    order: 1,
    lessonCount: 3,
    visualizationModes: ['none'],
  };
}

function buildLessonSummary(id: string): LearningLessonSummary {
  return {
    id,
    title: `수업 ${id}`,
    categoryId: 'category-1',
    categoryName: '기초 개념',
    description: '설명',
    language: 'python',
    supportedLanguages: ['python', 'c', 'java'],
    visualizationMode: 'none',
    difficulty: '입문',
    estimatedMinutes: 10,
    tags: [],
  };
}

function buildLesson(id: string): LearningLesson {
  return {
    ...buildLessonSummary(id),
    learningPoints: [],
    sourceCode: 'print("hello")',
    learningContent: {
      title: `학습 ${id}`,
      summary: '요약',
      conceptPoints: [],
      walkthroughCode: 'print("hello")',
    },
    implementationChallenge: {
      title: `구현 ${id}`,
      prompt: '직접 구현',
      starterCode: 'print("hello")',
      checkpoints: [],
    },
    relatedLessonIds: [],
  };
}

function buildProgress(lessonId: string): LearningProgress {
  return {
    lessonId,
    status: 'studied',
    firstStudiedAt: '2026-06-11T05:00:00Z',
    lastStudiedAt: '2026-06-11T05:00:00Z',
    studyCount: 1,
    totalStudySeconds: 0,
    completedAt: null,
  };
}

function buildInsights(): LearningInsight {
  const lesson = buildLessonSummary('lesson-a');
  return {
    totalLessons: 3,
    studiedLessons: 1,
    completionRate: 0.3333,
    categoryProgress: [
      {
        categoryId: 'category-1',
        categoryName: '湲곗큹 媛쒕뀗',
        studiedCount: 1,
        totalCount: 3,
        completionRate: 0.3333,
        nextLessonId: 'lesson-a',
      },
    ],
    weakCategories: [
      {
        categoryId: 'category-1',
        categoryName: '湲곗큹 媛쒕뀗',
        studiedCount: 1,
        totalCount: 3,
        completionRate: 0.3333,
        nextLessonId: 'lesson-a',
      },
    ],
    nextRecommendations: [{ lesson, reason: 'next' }],
    reviewRecommendations: [{ lesson: buildLessonSummary('lesson-initial'), reason: 'review' }],
    dailyRecommendation: { lesson, reason: 'daily' },
  };
}

describe('useLearningCatalog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedGetErrorMessage.mockImplementation((error: unknown, fallback: string) =>
      error instanceof Error ? error.message : fallback,
    );
    mockedShouldReportError.mockReturnValue(false);
    mockedFetchLearningCategories.mockResolvedValue([buildCategory()]);
    mockedFetchLearningInsights.mockResolvedValue(buildInsights());
    mockedFetchLearningLessons.mockResolvedValue([
      buildLessonSummary('lesson-initial'),
      buildLessonSummary('lesson-a'),
      buildLessonSummary('lesson-b'),
    ]);
    mockedFetchLearningLessonDetail.mockResolvedValue(buildLesson('lesson-initial'));
    mockedMarkLearningLessonStudied.mockImplementation((lessonId: string) =>
      Promise.resolve(buildProgress(lessonId)),
    );
  });

  it('늦게 끝난 이전 수업 요청이 최신 선택을 덮어쓰지 않는다', async () => {
    const lessonA = createDeferred<LearningLesson>();
    const lessonB = createDeferred<LearningLesson>();

    mockedFetchLearningLessonDetail.mockImplementation((lessonId: string) => {
      if (lessonId === 'lesson-a') {
        return lessonA.promise;
      }
      if (lessonId === 'lesson-b') {
        return lessonB.promise;
      }
      return Promise.resolve(buildLesson(lessonId));
    });

    const { result } = renderHook(() => useLearningCatalog());

    await waitFor(() => expect(result.current.currentLessonId).toBe('lesson-initial'));
    expect(mockedFetchLearningLessons).toHaveBeenCalledWith();

    let firstSelection!: Promise<LearningLesson | null>;
    let secondSelection!: Promise<LearningLesson | null>;
    act(() => {
      firstSelection = result.current.selectLesson('lesson-a');
      secondSelection = result.current.selectLesson('lesson-b');
    });

    await act(async () => {
      lessonB.resolve(buildLesson('lesson-b'));
      await secondSelection;
    });
    expect(result.current.currentLessonId).toBe('lesson-b');

    await act(async () => {
      lessonA.resolve(buildLesson('lesson-a'));
      await expect(firstSelection).resolves.toBeNull();
    });
    expect(result.current.currentLessonId).toBe('lesson-b');
    expect(result.current.currentLesson?.id).toBe('lesson-b');
    expect(result.current.currentLesson?.progress?.lessonId).toBe('lesson-b');
  });
});
