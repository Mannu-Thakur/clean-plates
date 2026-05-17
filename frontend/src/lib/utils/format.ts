export function grams(value: number | null | undefined) {
  const safe = Number(value ?? 0);
  if (safe >= 1000) return `${(safe / 1000).toFixed(safe >= 10000 ? 0 : 1)} kg`;
  return `${safe.toFixed(safe >= 100 ? 0 : 1)} g`;
}

export function number(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === '') return '0';
  const parsed = typeof value === 'number' ? value : Number(value);
  if (Number.isNaN(parsed)) return String(value);
  return new Intl.NumberFormat('en-IN').format(parsed);
}

export function pct(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '0%';
  return `${value.toFixed(Math.abs(value) >= 10 ? 0 : 1)}%`;
}

export function dateTime(value: string | Date | null | undefined) {
  if (!value) return 'Never';
  const date = typeof value === 'string' ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return 'Invalid date';
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(date);
}

export function shortDate(value: string | Date | null | undefined) {
  if (!value) return 'None';
  const date = typeof value === 'string' ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return 'Invalid date';
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(date);
}

export function fileSize(bytes: number | null | undefined) {
  const safe = Number(bytes ?? 0);
  if (safe < 1024) return `${safe} B`;
  if (safe < 1024 * 1024) return `${(safe / 1024).toFixed(1)} KB`;
  return `${(safe / (1024 * 1024)).toFixed(1)} MB`;
}

export function titleCase(value: string | null | undefined) {
  return String(value ?? 'unknown')
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function statusTone(value: string | boolean | null | undefined) {
  const normalized = String(value ?? '').toLowerCase();
  if (
    value === true ||
    [
      'online',
      'active',
      'success',
      'healthy',
      'delivered',
      'green',
      'resolved'
    ].includes(normalized)
  ) {
    return 'good';
  }
  if (
    [
      'warning',
      'yellow',
      'pending',
      'queued',
      'generating',
      'medium',
      'level_1'
    ].includes(normalized)
  )
    return 'warn';
  if (
    [
      'critical',
      'red',
      'failed',
      'offline',
      'revoked',
      'level_3',
      'penalty'
    ].includes(normalized)
  )
    return 'bad';
  if (
    ['orange', 'escalated', 'level_2', 'converted_to_penalty'].includes(
      normalized
    )
  )
    return 'hot';
  return 'neutral';
}

export function itemsOf<T>(
  payload: { items?: T[] } | T[] | null | undefined
): T[] {
  if (Array.isArray(payload)) return payload;
  return payload?.items ?? [];
}
