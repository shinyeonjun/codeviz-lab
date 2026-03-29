import React from 'react';

/* === Card ===
 * 미니멀 카드. 흰 배경 + 얇은 테두리만.
 */
export const Card = ({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) => (
  <div className={`rounded-2xl border border-surface-border bg-white p-5 ${className}`}>
    {children}
  </div>
);
