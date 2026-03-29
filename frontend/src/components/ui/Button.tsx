/* === Button ===
 * 미니멀 버튼. variant: primary(파란), outline(테두리), ghost(텍스트만).
 */
type Variant = 'primary' | 'outline' | 'ghost';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const styles: Record<Variant, string> = {
  primary: 'bg-accent text-white hover:bg-blue-700',
  outline: 'border border-surface-border bg-white text-ink-secondary hover:bg-surface-soft',
  ghost: 'bg-transparent text-ink-secondary hover:text-ink hover:bg-surface-muted',
};

export const Button = ({
  children,
  variant = 'primary',
  className = '',
  ...props
}: ButtonProps) => (
  <button
    className={`inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${styles[variant]} ${className}`}
    {...props}
  >
    {children}
  </button>
);
