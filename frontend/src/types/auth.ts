export interface AuthUser {
  id: string;
  email: string;
  name: string;
  createdAt: string;
}

export interface AuthSessionState {
  isAuthenticated: boolean;
  user: AuthUser | null;
}
