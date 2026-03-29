export type PointerDetail = {
  name: string;
  index: number | string;
};

export type ScalarBadge = {
  name: string;
  value: unknown;
};

export function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)) : [];
}

export function asNumberArray(value: unknown): number[] {
  return Array.isArray(value)
    ? value.filter((item): item is number => typeof item === 'number' && Number.isFinite(item))
    : [];
}

export function asMatrix(value: unknown): Array<Array<string | number>> {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.map((row) =>
    Array.isArray(row) ? row.map((cell) => (typeof cell === 'number' ? cell : String(cell))) : [],
  );
}

export function asPointerDetails(value: unknown): PointerDetail[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      if (!item || typeof item !== 'object') {
        return null;
      }

      const record = item as Record<string, unknown>;
      if (
        typeof record.name !== 'string' ||
        (typeof record.index !== 'number' && typeof record.index !== 'string')
      ) {
        return null;
      }

      return { name: record.name, index: record.index };
    })
    .filter((item): item is PointerDetail => item !== null);
}

export function asScalarBadges(value: unknown): ScalarBadge[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      if (!item || typeof item !== 'object') {
        return null;
      }

      const record = item as Record<string, unknown>;
      if (typeof record.name !== 'string') {
        return null;
      }

      return { name: record.name, value: record.value };
    })
    .filter((item): item is ScalarBadge => item !== null);
}

export function asNodeList(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value)
    ? value.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object')
    : [];
}

export function asEdgeList(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value)
    ? value.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object')
    : [];
}

export function asCellKeys(value: unknown): Set<string> {
  if (!Array.isArray(value)) {
    return new Set();
  }

  return new Set(
    value
      .filter((item): item is number[] => Array.isArray(item) && item.length >= 2)
      .map(([row, col]) => `${row}:${col}`),
  );
}

export function asStringSet(value: unknown): Set<string> {
  return new Set(asStringArray(value));
}

export function formatValue(value: unknown) {
  if (typeof value === 'string') {
    return value;
  }

  return JSON.stringify(value);
}

export function buildPointerMap(pointers: PointerDetail[]) {
  return pointers.reduce<Map<number | string, PointerDetail[]>>((map, pointer) => {
    const current = map.get(pointer.index) ?? [];
    current.push(pointer);
    map.set(pointer.index, current);
    return map;
  }, new Map<number | string, PointerDetail[]>());
}
