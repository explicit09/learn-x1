import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistance } from 'date-fns';

/**
 * Combines class names with Tailwind CSS classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Formats a date string to a human-readable format
 * @param dateString - ISO date string
 * @param formatStr - Date format string (default: 'PPP')
 */
export function formatDate(dateString: string, formatStr = 'PPP') {
  const date = new Date(dateString);
  return format(date, formatStr);
}

/**
 * Returns a relative time string (e.g., "2 hours ago")
 * @param dateString - ISO date string
 */
export function getRelativeTime(dateString: string) {
  const date = new Date(dateString);
  return formatDistance(date, new Date(), { addSuffix: true });
}

/**
 * Truncates text to a specified length
 * @param text - Text to truncate
 * @param length - Maximum length (default: 100)
 */
export function truncateText(text: string, length = 100) {
  if (text.length <= length) return text;
  return text.slice(0, length) + '...';
}

/**
 * Converts a string to title case
 * @param str - String to convert
 */
export function toTitleCase(str: string) {
  return str
    .toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Formats a percentage value
 * @param value - Percentage value (0-100)
 * @param decimals - Number of decimal places (default: 1)
 */
export function formatPercentage(value: number, decimals = 1) {
  return value.toFixed(decimals) + '%';
}

/**
 * Generates a random color based on a string input
 * @param str - Input string
 */
export function stringToColor(str: string) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  let color = '#';
  for (let i = 0; i < 3; i++) {
    const value = (hash >> (i * 8)) & 0xFF;
    color += ('00' + value.toString(16)).substr(-2);
  }
  return color;
}

/**
 * Gets initials from a name
 * @param name - Full name
 * @param limit - Maximum number of characters (default: 2)
 */
export function getInitials(name: string, limit = 2) {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, limit);
}

/**
 * Debounces a function
 * @param fn - Function to debounce
 * @param ms - Debounce delay in milliseconds
 */
export function debounce<T extends (...args: any[]) => any>(fn: T, ms = 300) {
  let timeoutId: ReturnType<typeof setTimeout>;
  return function(...args: Parameters<T>) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), ms);
  };
}

/**
 * Safely parses JSON with error handling
 * @param jsonString - JSON string to parse
 * @param fallback - Fallback value if parsing fails
 */
export function safeJsonParse<T>(jsonString: string, fallback: T): T {
  try {
    return JSON.parse(jsonString) as T;
  } catch (error) {
    return fallback;
  }
}
