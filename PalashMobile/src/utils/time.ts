/** Small, dependency-free date/time helpers for display. */

/** Time-of-day greeting in English (teacher-facing UI copy is English). */
export function greeting(date = new Date()): string {
  const h = date.getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

/**
 * Compact relative time, e.g. "just now", "3h ago", "2d ago", or a date for
 * anything older than a week. Falls back to the raw string if unparseable.
 */
export function relativeTime(iso: string, now = new Date()): string {
  const then = new Date(iso);
  const ms = then.getTime();
  if (Number.isNaN(ms)) return iso;

  const diff = now.getTime() - ms;
  const min = Math.round(diff / 60000);
  if (min < 1) return 'just now';
  if (min < 60) return `${min}m ago`;

  const hr = Math.round(min / 60);
  if (hr < 24) return `${hr}h ago`;

  const day = Math.round(hr / 24);
  if (day <= 7) return `${day}d ago`;

  return then.toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
}
