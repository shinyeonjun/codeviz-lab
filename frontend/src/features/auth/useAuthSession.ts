import { useCallback, useEffect, useState } from 'react';
import {
  createWorkspace,
  ensureGuestSession,
  fetchWorkspaceActivity,
  loginUser,
  logoutUser,
  registerUser,
  selectWorkspace,
} from '../../lib/api';
import type { AuthSessionState, WorkspaceActivity } from '../../types/auth';

export function useAuthSession() {
  const [authState, setAuthState] = useState<AuthSessionState | null>(null);
  const [activity, setActivity] = useState<WorkspaceActivity | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshActivity = useCallback(async () => {
    try {
      const nextActivity = await fetchWorkspaceActivity();
      setActivity(nextActivity);
    } catch (activityError) {
      console.error(activityError);
      setActivity(null);
    }
  }, []);

  const bootstrap = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const state = await ensureGuestSession();
      setAuthState(state);
      const nextActivity = await fetchWorkspaceActivity();
      setActivity(nextActivity);
    } catch (bootstrapError) {
      console.error(bootstrapError);
      setError(bootstrapError instanceof Error ? bootstrapError.message : '세션을 준비하지 못했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  const handleRegister = useCallback(async (params: {
    email: string;
    password: string;
    name: string;
  }) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const state = await registerUser(params);
      setAuthState(state);
      await refreshActivity();
      return true;
    } catch (registerError) {
      console.error(registerError);
      setError(registerError instanceof Error ? registerError.message : '회원가입에 실패했습니다.');
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, [refreshActivity]);

  const handleLogin = useCallback(async (params: {
    email: string;
    password: string;
  }) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const state = await loginUser(params);
      setAuthState(state);
      await refreshActivity();
      return true;
    } catch (loginError) {
      console.error(loginError);
      setError(loginError instanceof Error ? loginError.message : '로그인에 실패했습니다.');
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, [refreshActivity]);

  const handleLogout = useCallback(async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      await logoutUser();
      await bootstrap();
    } catch (logoutError) {
      console.error(logoutError);
      setError(logoutError instanceof Error ? logoutError.message : '로그아웃에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  }, [bootstrap]);

  const handleCreateWorkspace = useCallback(async (title: string) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const state = await createWorkspace({ title });
      setAuthState(state);
      await refreshActivity();
      return true;
    } catch (workspaceError) {
      console.error(workspaceError);
      setError(workspaceError instanceof Error ? workspaceError.message : '작업공간을 만들지 못했습니다.');
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, [refreshActivity]);

  const handleSelectWorkspace = useCallback(async (workspaceId: string) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const state = await selectWorkspace({ workspaceId });
      setAuthState(state);
      await refreshActivity();
      return true;
    } catch (workspaceError) {
      console.error(workspaceError);
      setError(workspaceError instanceof Error ? workspaceError.message : '작업공간 전환에 실패했습니다.');
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, [refreshActivity]);

  return {
    authState,
    activity,
    isLoading,
    isSubmitting,
    error,
    clearError: () => setError(null),
    refreshActivity,
    register: handleRegister,
    login: handleLogin,
    logout: handleLogout,
    createWorkspace: handleCreateWorkspace,
    selectWorkspace: handleSelectWorkspace,
  };
}
