'use strict';

/**
 * Shared utility helpers used by both the tree and summary commands.
 */

/**
 * Format a byte count as a human-readable string.
 *
 * @param {number} bytes - Non-negative byte count.
 * @returns {string} e.g. "1.0 B", "3.5 KB", "12.0 MB"
 */
function fmtSize(bytes) {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let n = bytes;
  for (let i = 0; i < units.length - 1; i++) {
    if (n < 1024) return `${n.toFixed(1)} ${units[i]}`;
    n /= 1024;
  }
  return `${n.toFixed(1)} TB`;
}

/**
 * Return true if name is hidden (starts with ".").
 *
 * @param {string} name - File or directory name.
 * @returns {boolean}
 */
function isHidden(name) {
  return name.startsWith('.');
}

/**
 * Return true if name matches any glob pattern.
 * Supports * (any sequence of characters) and ? (any single character).
 *
 * @param {string} name - File or directory name to test.
 * @param {string[]} patterns - Glob patterns.
 * @returns {boolean}
 */
function matchesIgnore(name, patterns) {
  return patterns.some(pattern => {
    const escaped = pattern.replace(/[.+^${}()|[\]\\]/g, '\\$&');
    const regexStr = escaped.replace(/\*/g, '.*').replace(/\?/g, '.');
    return new RegExp(`^${regexStr}$`).test(name);
  });
}

module.exports = { fmtSize, isHidden, matchesIgnore };
