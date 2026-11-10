export function str(obj: unknown, key: string): string | null {
  if (typeof obj !== "object" || obj === null || !(key in obj)) {
    return null;
  }

  const value = (obj as Record<string, unknown>)[key];
  return typeof value === "string" ? value : null;
}

export function strList(obj: unknown, key: string): string[] {
  if (typeof obj !== "object" || obj === null || !(key in obj)) {
    return [];
  }

  const value = (obj as Record<string, unknown>)[key];
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}
