import { describe, expect, it } from 'vitest';
import { formatValue } from './visualizationUtils';

describe('formatValue', () => {
  it('replaces unavailable C trace values in scalar and nested values', () => {
    expect(formatValue('<optimized out>')).toBe('아직 값 없음');
    expect(
      formatValue({
        root: '<optimized out>',
        values: [1, '<optimized out>', { child: '<optimized out>' }],
      }),
    ).toBe('{"root":"아직 값 없음","values":[1,"아직 값 없음",{"child":"아직 값 없음"}]}');
  });
});
