import type { ExecutionLanguage } from '../../../types/execution';

export function getEditorFileName(language: ExecutionLanguage, fallback = 'scratch') {
  if (language === 'python') {
    return `${fallback}.py`;
  }
  if (language === 'c') {
    return 'main.c';
  }
  return 'Main.java';
}

export function getMonacoLanguage(language: ExecutionLanguage) {
  return language;
}
