import { useCallback, useEffect, useState } from 'react';
import {
  fetchAuthMe,
  loginUser,
  logoutUser,
  registerUser,
  UnauthorizedError,
} from '../../lib/api';
import type { AuthSessionState } from '../../types/auth';

export function useAuthSession() {
  const [authState, setAuthState] = useState<AuthSessionState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const bootstrap = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const state = await fetchAuthMe();
      setAuthState(state);
    } catch (bootstrapError) {
      console.error(bootstrapError);
      if (bootstrapError instanceof UnauthorizedError) {
        setAuthState(null);
        return;
      }
      setError(
        bootstrapError instanceof Error
          ? bootstrapError.message
          : '인증 상태를 불러오지 못했습니다.',
      );
      setAuthState(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    const handleAuthRequired = () => {
      setAuthState(null);
      setIsLoading(false);
      setIsSubmitting(false);
      setError(null);
    };

    window.addEventListener('codeviz:auth-required', handleAuthRequired);
    return () => window.removeEventListener('codeviz:auth-required', handleAuthRequired);
  }, []);

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
      return true;
    } catch (registerError) {
      console.error(registerError);
      setError(registerError instanceof Error ? registerError.message : '회원가입에 실패했습니다.');
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const handleLogin = useCallback(async (params: {
    email: string;
    password: string;
  }) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const state = await loginUser(params);
      setAuthState(state);
      return true;
    } catch (loginError) {
      console.error(loginError);
      if (loginError instanceof UnauthorizedError) {
        setError('이메일 또는 비밀번호를 다시 확인해 주세요.');
      } else {
        setError(loginError instanceof Error ? loginError.message : '로그인에 실패했습니다.');
      }
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const handleLogout = useCallback(async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      await logoutUser();
      setAuthState(null);
    } catch (logoutError) {
      console.error(logoutError);
      setError(logoutError instanceof Error ? logoutError.message : '로그아웃에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  return {
    authState,
    isLoading,
    isSubmitting,
    error,
    clearError: () => setError(null),
    refreshAuth: bootstrap,
    register: handleRegister,
    login: handleLogin,
    logout: handleLogout,
  };
}
