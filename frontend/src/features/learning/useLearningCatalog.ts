import { useEffect, useMemo, useRef, useState } from 'react';
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
  LearningGroup,
  LearningInsight,
  LearningLesson,
  LearningLessonSummary,
  LearningProgress,
} from '../../types/learning';

interface UseLearningCatalogResult {
  categories: LearningCategory[];
  groups: LearningGroup[];
  insights: LearningInsight | null;
  currentLesson: LearningLesson | null;
  currentLessonId: string | null;
  isLoading: boolean;
  isSelectingLesson: boolean;
  error: string | null;
  selectLesson: (lessonId: string) => Promise<LearningLesson | null>;
}

export function useLearningCatalog(): UseLearningCatalogResult {
  const [categories, setCategories] = useState<LearningCategory[]>([]);
  const [lessons, setLessons] = useState<LearningLessonSummary[]>([]);
  const [insights, setInsights] = useState<LearningInsight | null>(null);
  const [lessonDetails, setLessonDetails] = useState<Record<string, LearningLesson>>({});
  const [currentLessonId, setCurrentLessonId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSelectingLesson, setIsSelectingLesson] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const selectionRequestRef = useRef(0);

  const groups = useMemo<LearningGroup[]>(() => {
    const lessonMap = new Map<string, LearningLessonSummary[]>();
    lessons.forEach((lesson) => {
      const current = lessonMap.get(lesson.categoryId) ?? [];
      current.push(lesson);
      lessonMap.set(lesson.categoryId, current);
    });

    return categories
      .slice()
      .sort((a, b) => a.order - b.order)
      .map((category) => ({
        category,
        lessons: lessonMap.get(category.id) ?? [],
      }));
  }, [categories, lessons]);

  const applyProgressToCatalog = (progress: LearningProgress) => {
    setLessons((prev) => prev.map((lesson) => (
      lesson.id === progress.lessonId ? { ...lesson, progress } : lesson
    )));
    setLessonDetails((prev) => {
      const lesson = prev[progress.lessonId];
      if (!lesson) {
        return prev;
      }
      return {
        ...prev,
        [progress.lessonId]: { ...lesson, progress },
      };
    });
  };

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const [categoryData, lessonData, insightData] = await Promise.all([
          fetchLearningCategories(),
          fetchLearningLessons(),
          fetchLearningInsights(),
        ]);

        setCategories(categoryData);
        setLessons(lessonData);
        setInsights(insightData);

        const firstLessonId = lessonData[0]?.id ?? null;
        if (firstLessonId) {
          const detail = await fetchLearningLessonDetail(firstLessonId);
          setLessonDetails({ [detail.id]: detail });
          setCurrentLessonId(detail.id);
        }
      } catch (loadError) {
        if (shouldReportError(loadError)) {
          console.error(loadError);
        }
        setError(getErrorMessage(loadError, '학습 목록을 불러오지 못했습니다.'));
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, []);

  const selectLesson = async (lessonId: string): Promise<LearningLesson | null> => {
    const requestId = selectionRequestRef.current + 1;
    selectionRequestRef.current = requestId;
    setIsSelectingLesson(true);
    setError(null);

    try {
      const detail = lessonDetails[lessonId] ?? await fetchLearningLessonDetail(lessonId);
      if (requestId !== selectionRequestRef.current) {
        return null;
      }

      const progress = await markLearningLessonStudied(lessonId);
      const progressedDetail = { ...detail, progress };
      if (requestId !== selectionRequestRef.current) {
        return null;
      }

      setLessonDetails((prev) => ({ ...prev, [progressedDetail.id]: progressedDetail }));
      applyProgressToCatalog(progress);
      setInsights(await fetchLearningInsights());
      setCurrentLessonId(progressedDetail.id);
      return progressedDetail;
    } catch (loadError) {
      if (requestId !== selectionRequestRef.current) {
        return null;
      }

      if (shouldReportError(loadError)) {
        console.error(loadError);
      }
      setError(getErrorMessage(loadError, '학습 상세를 불러오지 못했습니다.'));
      return null;
    } finally {
      if (requestId === selectionRequestRef.current) {
        setIsSelectingLesson(false);
      }
    }
  };

  return {
    categories,
    groups,
    insights,
    currentLesson: currentLessonId ? lessonDetails[currentLessonId] ?? null : null,
    currentLessonId,
    isLoading,
    isSelectingLesson,
    error,
    selectLesson,
  };
}
