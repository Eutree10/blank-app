// Returns the local date as a YYYY-MM-DD string (day granularity).
export function todayKey(d: Date = new Date()): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// True when `dateKey` refers to a day before today.
export function isNewDay(dateKey: string): boolean {
  return dateKey !== todayKey();
}
