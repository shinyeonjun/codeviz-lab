import type { ExecutionLanguage, VisualizationMode, VisualizationRequestMode } from './execution';

export interface LearningCategory {
  id: string;
  name: string;
  description: string;
  order: number;
  lessonCount: number;
  visualizationModes: VisualizationMode[];
}

export interface LearningProgress {
  lessonId: string;
  status: 'studied' | 'completed';
  firstStudiedAt: string;
  lastStudiedAt: string;
  studyCount: number;
  totalStudySeconds: number;
  completedAt?: string | null;
}

export interface LearningLessonSummary {
  id: string;
  title: string;
  categoryId: string;
  categoryName: string;
  description: string;
  language: ExecutionLanguage;
  supportedLanguages: ExecutionLanguage[];
  visualizationMode: VisualizationMode;
  difficulty: string;
  estimatedMinutes: number;
  tags: string[];
  progress?: LearningProgress | null;
}

export interface LearningLesson extends LearningLessonSummary {
  learningPoints: string[];
  sourceCode: string;
  learningContent: {
    title: string;
    summary: string;
    conceptPoints: string[];
    walkthroughCode: string;
  };
  implementationChallenge: {
    title: string;
    prompt: string;
    starterCode: string;
    checkpoints: string[];
  };
  previousLessonId?: string | null;
  nextLessonId?: string | null;
  relatedLessonIds: string[];
}

export interface LearningGroup {
  category: LearningCategory;
  lessons: LearningLessonSummary[];
}

export interface LearningCategoryProgress {
  categoryId: string;
  categoryName: string;
  studiedCount: number;
  totalCount: number;
  completionRate: number;
  nextLessonId?: string | null;
}

export interface LearningRecommendation {
  lesson: LearningLessonSummary;
  reason: string;
}

export interface LearningInsight {
  totalLessons: number;
  studiedLessons: number;
  completionRate: number;
  categoryProgress: LearningCategoryProgress[];
  weakCategories: LearningCategoryProgress[];
  nextRecommendations: LearningRecommendation[];
  reviewRecommendations: LearningRecommendation[];
  dailyRecommendation?: LearningRecommendation | null;
}

export interface StudioLessonSeed {
  id: string;
  title: string;
  categoryName: string;
  description: string;
  language: ExecutionLanguage;
  visualizationMode: VisualizationRequestMode;
  sourceCode: string;
  difficulty: string;
  estimatedMinutes: number;
  learningPoints: string[];
  tags: string[];
}
