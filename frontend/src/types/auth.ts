export interface Workspace {
  id: string;
  title: string;
  isGuest: boolean;
  createdAt: string;
}

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  createdAt: string;
}

export interface AuthSessionState {
  isAuthenticated: boolean;
  isGuest: boolean;
  user: AuthUser | null;
  currentWorkspace: Workspace;
  workspaces: Workspace[];
}

export interface ExecutionActivity {
  runId: string;
  status: string;
  visualizationMode: string;
  sourcePreview: string;
  createdAt: string;
}

export interface ExamAttemptActivity {
  attemptId: string;
  lessonId: string;
  questionId: string;
  status: string;
  score: number;
  createdAt: string;
}

export interface WorkspaceActivity {
  currentWorkspace: Workspace;
  recentExecutions: ExecutionActivity[];
  recentExamAttempts: ExamAttemptActivity[];
}
