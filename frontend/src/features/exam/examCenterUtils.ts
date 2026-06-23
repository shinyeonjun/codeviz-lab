import type { ExamQuestion, ExamSession, ExamSubmissionResult } from '../../types/exam';
import type { StudioLessonSeed } from '../../types/learning';

export interface WrongReviewItem {
  question: ExamQuestion;
  index: number;
  submission: ExamSubmissionResult;
}

export const QUESTION_COUNT_OPTIONS = [2, 3, 5];

export function createEmptyExamSeed(): StudioLessonSeed {
  return {
    id: 'exam-empty',
    title: '시험을 준비하는 중',
    categoryName: '시험',
    description: '카테고리를 선택하고 시험을 시작하세요.',
    language: 'python',
    visualizationMode: 'none',
    sourceCode: '',
    difficulty: '시험',
    estimatedMinutes: 0,
    learningPoints: [],
    tags: [],
  };
}

export function buildQuestionSeed(question: ExamQuestion, code: string): StudioLessonSeed {
  return {
    id: question.id,
    title: question.title,
    categoryName: question.categoryName,
    description: question.prompt,
    language: question.language,
    visualizationMode: 'auto',
    sourceCode: code,
    difficulty: question.difficulty,
    estimatedMinutes: question.estimatedMinutes,
    learningPoints: [],
    tags: question.tags,
  };
}

export function formatValue(value: unknown) {
  if (typeof value === 'string') {
    return value;
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function getStatusLabel(status: ExamSubmissionResult['status']) {
  if (status === 'passed') {
    return '통과';
  }
  if (status === 'failed') {
    return '미통과';
  }
  if (status === 'timeout') {
    return '시간 초과';
  }
  return '오류';
}

export function getStatusClass(status: ExamSubmissionResult['status']) {
  if (status === 'passed') {
    return 'bg-emerald-50 text-emerald-600';
  }
  if (status === 'failed') {
    return 'bg-amber-50 text-amber-600';
  }
  return 'bg-rose-50 text-rose-600';
}

export function getWrongReviewItems(
  session: ExamSession | null,
  submissionMap: Record<string, ExamSubmissionResult>,
): WrongReviewItem[] {
  if (!session) {
    return [];
  }

  return session.questions
    .map((question, index) => ({
      question,
      index,
      submission: submissionMap[question.id],
    }))
    .filter(
      (item): item is WrongReviewItem =>
        Boolean(item.submission) && item.submission.status !== 'passed',
    );
}
