import { useMemo, useState } from 'react';
import { ExamCenter } from './features/exam/ExamCenter';
import { LearningHome } from './features/home/LearningHome';
import { Sidebar } from './features/navigation/Sidebar';
import { ExecutionStudio } from './features/studio/ExecutionStudio';
import { PracticeStudio } from './features/studio/PracticeStudio';
import { useExecutionStudio } from './features/studio/useExecutionStudio';
import { useLearningCatalog } from './features/learning/useLearningCatalog';
import type { StudioLessonSeed } from './types/learning';

type AppView = 'home' | 'lesson' | 'studio' | 'exam';

function createEmptyLesson(): StudioLessonSeed {
  return {
    id: 'empty',
    title: '학습을 불러오는 중',
    categoryName: '대기',
    description: '학습 데이터를 불러오는 중입니다.',
    visualizationMode: 'none',
    sourceCode: '',
    difficulty: '입문',
    estimatedMinutes: 0,
    learningPoints: [],
    tags: [],
  };
}

function App() {
  const [currentView, setCurrentView] = useState<AppView>('home');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const emptyLesson = useMemo(() => createEmptyLesson(), []);
  const studio = useExecutionStudio(emptyLesson);
  const {
    groups,
    currentLesson,
    currentLessonId,
    isLoading,
    isSelectingLesson,
    error,
    selectLesson,
  } = useLearningCatalog();

  const openLesson = async (lessonId: string) => {
    const lesson = await selectLesson(lessonId);
    if (!lesson) {
      return;
    }

    studio.applyLesson(lesson);
    setCurrentView('lesson');
  };

  const selectLessonFromSidebar = async (lessonId: string) => {
    const lesson = await selectLesson(lessonId);
    if (!lesson) {
      return;
    }

    studio.applyLesson(lesson);
    if (currentView !== 'lesson') {
      setCurrentView('lesson');
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface-soft font-sans text-ink">
      <Sidebar
        currentView={currentView}
        onChangeView={setCurrentView}
        groups={groups}
        currentLessonId={currentLessonId}
        onSelectLesson={selectLessonFromSidebar}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        isLoading={isLoading}
      />

      <main className="flex-1 overflow-y-auto scrollbar-light">
        {currentView === 'home' && (
          <LearningHome
            groups={groups}
            currentLesson={currentLesson}
            onOpenLesson={openLesson}
            isLoading={isLoading}
            isSelectingLesson={isSelectingLesson}
            error={error}
          />
        )}
        {currentView === 'lesson' && currentLesson && (
          <ExecutionStudio
            lesson={currentLesson}
            studio={studio}
            onBackHome={() => setCurrentView('home')}
            isSelectingLesson={isSelectingLesson}
          />
        )}
        {currentView === 'lesson' && !currentLesson && (
          <div className="px-6 py-8 text-sm text-ink-muted">불러온 학습이 없습니다.</div>
        )}
        {currentView === 'studio' && <PracticeStudio />}
        {currentView === 'exam' && <ExamCenter />}
        {error && currentView !== 'home' && (
          <div className="px-6 pb-6 text-sm text-red-600">{error}</div>
        )}
      </main>
    </div>
  );
}

export default App;
