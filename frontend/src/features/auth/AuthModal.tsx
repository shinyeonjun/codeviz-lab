import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';

interface AuthModalProps {
  mode: 'login' | 'register';
  open: boolean;
  isSubmitting: boolean;
  error: string | null;
  onClose: () => void;
  onSwitchMode: (mode: 'login' | 'register') => void;
  onLogin: (params: { email: string; password: string }) => Promise<boolean>;
  onRegister: (params: { email: string; password: string; name: string }) => Promise<boolean>;
}

export function AuthModal({
  mode,
  open,
  isSubmitting,
  error,
  onClose,
  onSwitchMode,
  onLogin,
  onRegister,
}: AuthModalProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  useEffect(() => {
    if (!open) {
      return;
    }
    setEmail('');
    setPassword('');
    setName('');
  }, [open, mode]);

  if (!open) {
    return null;
  }

  const handleSubmit = async () => {
    const ok = mode === 'login'
      ? await onLogin({ email, password })
      : await onRegister({ email, password, name });

    if (ok) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 px-4">
      <Card className="w-full max-w-[420px] p-0">
        <div className="flex items-center justify-between border-b border-surface-border px-5 py-4">
          <div>
            <h3 className="text-base font-semibold text-ink">
              {mode === 'login' ? '로그인' : '회원가입'}
            </h3>
            <p className="mt-1 text-xs text-ink-muted">
              {mode === 'login' ? '기존 작업공간으로 이어서 학습합니다.' : '게스트 작업공간을 계정에 연결합니다.'}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-ink-muted transition-colors hover:bg-surface-soft hover:text-ink"
          >
            <X size={16} />
          </button>
        </div>

        <div className="space-y-4 px-5 py-5">
          {mode === 'register' && (
            <label className="block">
              <span className="mb-1.5 block text-xs font-medium text-ink-muted">이름</span>
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="w-full rounded-xl border border-surface-border px-3 py-2 text-sm text-ink outline-none transition-colors focus:border-accent/40"
                placeholder="이름"
              />
            </label>
          )}

          <label className="block">
            <span className="mb-1.5 block text-xs font-medium text-ink-muted">이메일</span>
            <input
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-xl border border-surface-border px-3 py-2 text-sm text-ink outline-none transition-colors focus:border-accent/40"
              placeholder="you@example.com"
            />
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-medium text-ink-muted">비밀번호</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-xl border border-surface-border px-3 py-2 text-sm text-ink outline-none transition-colors focus:border-accent/40"
              placeholder="8자 이상"
            />
          </label>

          {error && <p className="text-sm text-rose-600">{error}</p>}

          <div className="flex gap-2">
            <Button variant="primary" onClick={() => void handleSubmit()} disabled={isSubmitting}>
              {isSubmitting ? '처리 중...' : mode === 'login' ? '로그인' : '회원가입'}
            </Button>
            <Button
              variant="outline"
              onClick={() => onSwitchMode(mode === 'login' ? 'register' : 'login')}
              disabled={isSubmitting}
            >
              {mode === 'login' ? '회원가입으로' : '로그인으로'}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
