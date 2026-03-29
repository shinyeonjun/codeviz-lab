import type { VisualizationMode } from './execution';


export interface ExamCategory {
  id: string;
  name: string;
  description: string;
  questionCount: number;
}

export interface ExamQuestion {
  id: string;
  lessonId: string;
  categoryId: string;
  categoryName: string;
  title: string;
  prompt: string;
  visualizationMode: VisualizationMode;
  starterCode: string;
  difficulty: string;
  estimatedMinutes: number;
  tags: string[];
}

export interface ExamSession {
  sessionId: string;
  categoryId: string;
  categoryName: string;
  questionCount: number;
  questions: ExamQuestion[];
}

export interface ExamCaseResult {
  caseId: string;
  passed: boolean;
  inputSummary: string;
  expected: unknown;
  actual: unknown;
  message: string;
}

export interface ExamSubmissionResult {
  lessonId: string;
  questionId: string;
  status: 'passed' | 'failed' | 'error' | 'timeout';
  score: number;
  passedCount: number;
  totalCount: number;
  errorMessage?: string | null;
  results: ExamCaseResult[];
}
