import { describe, expect, it } from 'vitest';
import type { LearningLesson } from '../../../types/learning';
import { resolveLessonCode } from './lessonLanguageVariants';

function buildLesson(visualizationMode: string, id = `lesson-${visualizationMode}`): LearningLesson {
  return {
    id,
    title: 'Sample lesson',
    categoryId: 'basics',
    categoryName: '기초 개념',
    description: 'sample',
    language: 'python',
    supportedLanguages: ['python', 'c', 'java'],
    visualizationMode,
    difficulty: '입문',
    estimatedMinutes: 10,
    tags: [],
    learningPoints: [],
    sourceCode: 'print("python")',
    learningContent: {
      title: '학습',
      summary: 'sample',
      conceptPoints: [],
      walkthroughCode: 'print("python")',
    },
    implementationChallenge: {
      title: '직접 구현',
      prompt: 'sample',
      starterCode: 'print("starter")',
      checkpoints: [],
    },
    relatedLessonIds: [],
  };
}

describe('resolveLessonCode', () => {
  it('keeps the original Python code', () => {
    const lesson = buildLesson('array-bars');

    expect(resolveLessonCode(lesson, 'learn', 'python')).toBe('print("python")');
    expect(resolveLessonCode(lesson, 'implement', 'python')).toBe('print("starter")');
  });

  it('uses runnable Java code for scalar basics instead of a generic hello world', () => {
    const code = resolveLessonCode(buildLesson('none'), 'learn', 'java');

    expect(code).toContain('int value = 2');
    expect(code).not.toContain('Hello, Java');
  });

  it('uses mode-aware C and Java variants for core visualization families', () => {
    expect(resolveLessonCode(buildLesson('stack-vertical'), 'learn', 'c')).toContain('int stack');
    expect(resolveLessonCode(buildLesson('graph-bfs-traversal'), 'learn', 'java')).toContain(
      'int[][] edges',
    );
    expect(resolveLessonCode(buildLesson('dp-table'), 'implement', 'java')).toContain('buildDpTable');
  });

  it('uses lesson-specific variants for basic syntax lessons', () => {
    expect(resolveLessonCode(buildLesson('array-cells', 'lesson-comparison-if'), 'learn', 'java')).toContain(
      'if (score >= 60)',
    );
    expect(resolveLessonCode(buildLesson('array-cells', 'lesson-for-loop-sum'), 'learn', 'c')).toContain(
      'for (int i = 1;',
    );
    expect(resolveLessonCode(buildLesson('array-cells', 'lesson-linear-search'), 'implement', 'java')).toContain(
      'linearSearch',
    );
  });

  it('does not treat generic array cells as a sorting template', () => {
    const code = resolveLessonCode(buildLesson('array-cells'), 'learn', 'java');

    expect(code).toContain('int[] items');
    expect(code).not.toContain('insertion');
  });

  it('uses a Java lambda variant for the lambda lesson', () => {
    const code = resolveLessonCode(buildLesson('call-stack', 'lesson-lambda-functions'), 'learn', 'java');

    expect(code).toContain('IntUnaryOperator');
    expect(code).toContain('value -> value * 2');
    expect(code).not.toContain('factorial');
  });
});
