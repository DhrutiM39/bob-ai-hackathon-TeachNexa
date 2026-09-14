/**
 * Format a date string for display.
 */
export function formatDate(dateStr) {
  if (!dateStr) return '';
  try {
    return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(dateStr));
  } catch {
    return dateStr;
  }
}

/**
 * Compute completion percentage from counts.
 */
export function computeProgress(completed, total) {
  if (!total || total === 0) return 0;
  return Math.round((completed / total) * 100);
}

/**
 * Truncate a string to a maximum length.
 */
export function truncate(str, maxLen = 100) {
  if (!str) return '';
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen).trimEnd() + '…';
}

/**
 * Convert bytes to a human-readable size string.
 */
export function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Pluralize a word based on count.
 */
export function pluralize(count, word, plural) {
  return `${count} ${count === 1 ? word : (plural || word + 's')}`;
}

/**
 * Generate a unique local id (for optimistic UI).
 */
export function localId() {
  return `local_${Date.now()}_${Math.random().toString(36).slice(2)}`;
}
