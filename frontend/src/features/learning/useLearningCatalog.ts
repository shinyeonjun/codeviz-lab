import { useEffect, useMemo, useState } from 'react';
import {
  fetchLearningCategories,
  fetchLearningLessonDetail,
  fetchLearningLessons,
} from '../../lib/api';
import type {
  LearningCategory,
  LearningGroup,
  LearningLesson,
  LearningLessonSummary,
} from '../../types/learning';

interface UseLearningCatalogResult {
  categories: LearningCategory[];
  groups: LearningGroup[];
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
  const [lessonDetails, setLessonDetails] = useState<Record<string, LearningLesson>>({});
  const [currentLessonId, setCurrentLessonId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSelectingLesson, setIsSelectingLesson] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const [categoryData, lessonData] = await Promise.all([
          fetchLearningCategories(),
          fetchLearningLessons({ language: 'python' }),
        ]);

        setCategories(categoryData);
        setLessons(lessonData);

        const firstLessonId = lessonData[0]?.id ?? null;
        if (firstLessonId) {
          const detail = await fetchLearningLessonDetail(firstLessonId);
          setLessonDetails({ [detail.id]: detail });
          setCurrentLessonId(detail.id);
        }
      } catch (loadError) {
        console.error(loadError);
        setError('학습 목록을 불러오지 못했습니다. 백엔드 서버가 켜져 있는지 확인해 주세요.');
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, []);

  const selectLesson = async (lessonId: string): Promise<LearningLesson | null> => {
    setIsSelectingLesson(true);
    setError(null);

    try {
      const cachedLesson = lessonDetails[lessonId];
      if (cachedLesson) {
        setCurrentLessonId(lessonId);
        return cachedLesson;
      }

      const detail = await fetchLearningLessonDetail(lessonId);
      setLessonDetails((prev) => ({ ...prev, [detail.id]: detail }));
      setCurrentLessonId(detail.id);
      return detail;
    } catch (loadError) {
      console.error(loadError);
      setError('학습 상세를 불러오지 못했습니다.');
      return null;
    } finally {
      setIsSelectingLesson(false);
    }
  };

  return {
    categories,
    groups,
    currentLesson: currentLessonId ? lessonDetails[currentLessonId] ?? null : null,
    currentLessonId,
    isLoading,
    isSelectingLesson,
    error,
    selectLesson,
  };
}
