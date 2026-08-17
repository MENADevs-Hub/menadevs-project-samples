'use strict';

const { generateId, fmtDate, parseDueDate, validatePriority, isOverdue } = require('../src/utils');

describe('generateId', () => {
  test('returns an 8-character hex string', () => {
    const id = generateId();
    expect(id).toMatch(/^[0-9a-f]{8}$/);
  });

  test('returns a different value each call', () => {
    const ids = new Set(Array.from({ length: 20 }, () => generateId()));
    expect(ids.size).toBe(20);
  });
});

describe('fmtDate', () => {
  test('returns empty string for null', () => {
    expect(fmtDate(null)).toBe('');
  });

  test('returns YYYY-MM-DD portion of ISO string', () => {
    expect(fmtDate('2026-07-01T00:00:00.000Z')).toBe('2026-07-01');
  });

  test('returns date string as-is when already YYYY-MM-DD', () => {
    expect(fmtDate('2026-12-31')).toBe('2026-12-31');
  });
});

describe('parseDueDate', () => {
  test('accepts a valid YYYY-MM-DD date', () => {
    const result = parseDueDate('2026-07-01');
    expect(result.ok).toBe(true);
    expect(result.date).toBe('2026-07-01');
  });

  test('rejects wrong format (DD-MM-YYYY)', () => {
    const result = parseDueDate('01-07-2026');
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/expected YYYY-MM-DD/);
  });

  test('rejects text strings', () => {
    expect(parseDueDate('tomorrow').ok).toBe(false);
  });

  test('rejects invalid calendar dates', () => {
    expect(parseDueDate('2026-13-01').ok).toBe(false);
  });

  test('rejects empty string', () => {
    expect(parseDueDate('').ok).toBe(false);
  });
});

describe('validatePriority', () => {
  test('accepts low, normal, high', () => {
    expect(validatePriority('low').ok).toBe(true);
    expect(validatePriority('normal').ok).toBe(true);
    expect(validatePriority('high').ok).toBe(true);
  });

  test('rejects unknown values', () => {
    expect(validatePriority('urgent').ok).toBe(false);
    expect(validatePriority('').ok).toBe(false);
    expect(validatePriority('HIGH').ok).toBe(false);
  });
});

describe('isOverdue', () => {
  test('returns false for done items with past due date', () => {
    expect(isOverdue({ status: 'done', due: '2020-01-01' })).toBe(false);
  });

  test('returns false for open items with no due date', () => {
    expect(isOverdue({ status: 'open', due: null })).toBe(false);
  });

  test('returns true for open items with past due date', () => {
    expect(isOverdue({ status: 'open', due: '2020-01-01' })).toBe(true);
  });

  test('returns false for open items with future due date', () => {
    expect(isOverdue({ status: 'open', due: '2099-12-31' })).toBe(false);
  });
});
