// Simple unique id generator for habits, rewards and purchases.
// Good enough for local-only storage (no collisions in practice).
export function uid(prefix = 'id'): string {
  const rand = Math.random().toString(36).slice(2, 8);
  const time = Date.now().toString(36);
  return `${prefix}_${time}${rand}`;
}
