/**
 * Combines multiple class names into a single string.
 * Filters out falsy values to avoid undefined or null class names.
 * 
 * @param {...(string | undefined | null | false)} classes - Class names to combine
 * @returns {string} Combined class names as a single string
 */
export function classNames(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
