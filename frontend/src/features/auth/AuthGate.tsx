import { useState } from 'react';
import { LockKeyhole, LogIn, UserPlus } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { AuthModal } from './AuthModal';

interface AuthGateProps {
  isSubmitting: boolean;
  error: string | null;
  onLogin: (params: { email: string; password: string }) => Promise<boolean>;
  onRegister: (params: { email: string; password: string; name: string }) => Promise<boolean>;
  onClearError: () => void;
}

export function AuthGate({
  isSubmitting,
  error,
  onLogin,
  onRegister,
  onClearError,
}: AuthGateProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const openModal = (nextMode: 'login' | 'register') => {
    onClearError();
    setMode(nextMode);
    setIsModalOpen(true);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-soft px-6 py-10">
      <Card className="w-full max-w-[520px]">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-accent text-white">
          <LockKeyhole size={20} />
        </div>

        <div className="mt-6 text-center">
          <h1 className="text-2xl font-bold tracking-tight text-ink">로그인 후 이용할 수 있습니다</h1>
          <p className="mt-3 text-sm leading-relaxed text-ink-secondary">
            코드 렌즈는 학습, 자유 스튜디오, 시험 기록을 계정 기준으로 관리합니다.
            <br />
            먼저 로그인하거나 새 계정을 만들어 주세요.
          </p>
        </div>

        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          <Button variant="primary" onClick={() => openModal('login')}>
            <LogIn size={16} />
            로그인
          </Button>
          <Button variant="outline" onClick={() => openModal('register')}>
            <UserPlus size={16} />
            회원가입
          </Button>
        </div>

        {error && (
          <p className="mt-4 text-center text-sm text-rose-600">{error}</p>
        )}
      </Card>

      <AuthModal
        mode={mode}
        open={isModalOpen}
        isSubmitting={isSubmitting}
        error={error}
        onClose={() => setIsModalOpen(false)}
        onSwitchMode={(nextMode) => {
          onClearError();
          setMode(nextMode);
        }}
        onLogin={onLogin}
        onRegister={onRegister}
      />
    </div>
  );
}
