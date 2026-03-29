import type { VisualizationMode } from './execution';

export interface LearningCategory {
  id: string;
  name: string;
  description: string;
  order: number;
  lessonCount: number;
  visualizationModes: VisualizationMode[];
}

export interface LearningLessonSummary {
  id: string;
  title: string;
  categoryId: string;
  categoryName: string;
  description: string;
  language: 'python';
  visualizationMode: VisualizationMode;
  difficulty: string;
  estimatedMinutes: number;
  tags: string[];
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

export interface StudioLessonSeed {
  id: string;
  title: string;
  categoryName: string;
  description: string;
  visualizationMode: VisualizationMode;
  sourceCode: string;
  difficulty: string;
  estimatedMinutes: number;
  learningPoints: string[];
  tags: string[];
}
