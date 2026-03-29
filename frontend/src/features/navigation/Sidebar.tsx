import { useState } from 'react';
import {
  BookOpen,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  FileText,
  LayoutGrid,
  Loader2,
  LogOut,
} from 'lucide-react';
import type { LearningGroup } from '../../types/learning';

type AppView = 'home' | 'lesson' | 'studio' | 'exam';

interface SidebarProps {
  currentView: AppView;
  onChangeView: (view: AppView) => void;
  groups: LearningGroup[];
  currentLessonId: string | null;
  onSelectLesson: (lessonId: string) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  isLoading: boolean;
  userName: string;
  userEmail: string;
  onLogout: () => void;
}

export function Sidebar({
  currentView,
  onChangeView,
  groups,
  currentLessonId,
  onSelectLesson,
  collapsed,
  onToggleCollapse,
  isLoading,
  userName,
  userEmail,
  onLogout,
}: SidebarProps) {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(categoryId)) {
        next.delete(categoryId);
      } else {
        next.add(categoryId);
      }
      return next;
    });
  };

  return (
    <aside
      className={`sticky top-0 z-30 flex h-screen flex-col overflow-hidden bg-sidebar transition-all duration-200 ${
        collapsed ? 'w-16' : 'w-60'
      }`}
    >
      <div className="flex items-center gap-3 px-4 py-5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent text-xs font-bold text-white">
          L
        </div>
        {!collapsed && <span className="truncate text-sm font-semibold text-white">코드 렌즈</span>}
      </div>

      <nav className="mt-1 space-y-0.5 px-2">
        <NavItem
          icon={<LayoutGrid size={16} />}
          label="학습 홈"
          active={currentView === 'home'}
          collapsed={collapsed}
          onClick={() => onChangeView('home')}
        />
        <NavItem
          icon={<BookOpen size={16} />}
          label="스튜디오"
          active={currentView === 'studio'}
          collapsed={collapsed}
          onClick={() => onChangeView('studio')}
        />
        <NavItem
          icon={<FileText size={16} />}
          label="시험"
          active={currentView === 'exam'}
          collapsed={collapsed}
          onClick={() => onChangeView('exam')}
        />
      </nav>

      {!collapsed && (
        <div className="mt-4 flex-1 space-y-3 overflow-y-auto px-2 scrollbar-hide">
          {isLoading ? (
            <div className="flex items-center gap-2 px-3 py-4 text-xs text-sidebar-muted">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              <span>목록을 불러오는 중</span>
            </div>
          ) : (
            groups.map((group) => {
              const isExpanded = expandedCategories.has(group.category.id);

              return (
                <div key={group.category.id}>
                  <button
                    type="button"
                    onClick={() => toggleCategory(group.category.id)}
                    className="group flex w-full items-center justify-between px-2 py-1"
                  >
                    <span className="text-[11px] font-medium uppercase tracking-widest text-sidebar-muted">
                      {group.category.name}
                    </span>
                    <span className="text-sidebar-muted transition-colors group-hover:text-gray-400">
                      {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                    </span>
                  </button>

                  {isExpanded && (
                    <div className="mt-0.5 space-y-0.5">
                      {group.lessons.map((lesson) => {
                        const isActive = lesson.id === currentLessonId;
                        return (
                          <button
                            key={lesson.id}
                            type="button"
                            onClick={() => void onSelectLesson(lesson.id)}
                            className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left transition-colors ${
                              isActive && currentView === 'lesson'
                                ? 'bg-white/10 text-white'
                                : 'text-sidebar-muted hover:bg-white/5 hover:text-gray-300'
                            }`}
                          >
                            <span className="truncate text-[13px]">{lesson.title}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      <div className="mt-auto space-y-2 px-2 py-3">
        {!collapsed && (
          <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-3">
            <p className="truncate text-sm font-semibold text-white">{userName}</p>
            <p className="mt-1 truncate text-xs text-sidebar-muted">{userEmail}</p>
            <button
              type="button"
              onClick={onLogout}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-sidebar-muted transition-colors hover:bg-white/5 hover:text-white"
            >
              <LogOut size={13} />
              로그아웃
            </button>
          </div>
        )}
        <button
          type="button"
          onClick={onToggleCollapse}
          className="flex w-full items-center justify-center rounded-lg p-2 text-sidebar-muted transition-colors hover:bg-white/5 hover:text-gray-300"
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>
    </aside>
  );
}

function NavItem({
  icon,
  label,
  active,
  collapsed,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  collapsed: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] font-medium transition-colors ${
        active ? 'bg-white/10 text-white' : 'text-sidebar-muted hover:bg-white/5 hover:text-gray-300'
      } ${collapsed ? 'justify-center' : ''}`}
      title={collapsed ? label : undefined}
    >
      <span className="shrink-0">{icon}</span>
      {!collapsed && <span className="truncate">{label}</span>}
    </button>
  );
}
