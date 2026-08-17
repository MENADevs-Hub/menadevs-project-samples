'use strict';

/**
 * Shared utility helpers for the todo CLI.
 */

const crypto = require('crypto');

/**
 * Generate a random 8-character hex ID.
 *
 * @returns {string}
 */
function generateId() {
  return crypto.randomBytes(4).toString('hex');
}

/**
 * Format an ISO date string as YYYY-MM-DD for display.
 *
 * @param {string|null} iso - ISO 8601 date string or null.
 * @returns {string}
 */
function fmtDate(iso) {
  if (!iso) return '';
  return iso.slice(0, 10);
}

/**
 * Parse and validate a due date string.
 * Accepts YYYY-MM-DD only. Returns the string as-is if valid.
 *
 * @param {string} value - User-supplied date string.
 * @returns {{ ok: true, date: string } | { ok: false, error: string }}
 */
function parseDueDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return { ok: false, error: `invalid date format: '${value}' (expected YYYY-MM-DD)` };
  }
  const d = new Date(value + 'T00:00:00');
  if (isNaN(d.getTime())) {
    return { ok: false, error: `invalid date: '${value}'` };
  }
  return { ok: true, date: value };
}

/**
 * Validate a priority string.
 * Accepted values: low, normal, high.
 *
 * @param {string} value
 * @returns {{ ok: true } | { ok: false, error: string }}
 */
function validatePriority(value) {
  const valid = ['low', 'normal', 'high'];
  if (!valid.includes(value)) {
    return { ok: false, error: `invalid priority: '${value}' (expected low, normal, or high)` };
  }
  return { ok: true };
}

/**
 * Return true if a todo item is overdue.
 * An item is overdue when it has a due date, its status is open,
 * and the due date is strictly before today.
 *
 * @param {{ status: string, due: string|null }} todo
 * @returns {boolean}
 */
function isOverdue(todo) {
  if (todo.status !== 'open' || !todo.due) return false;
  const today = new Date().toISOString().slice(0, 10);
  return todo.due < today;
}

module.exports = { generateId, fmtDate, parseDueDate, validatePriority, isOverdue };
