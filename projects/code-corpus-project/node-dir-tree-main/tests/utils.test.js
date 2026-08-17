'use strict';

const { fmtSize, isHidden, matchesIgnore } = require('../src/utils');

describe('fmtSize', () => {
  test('formats bytes', () => {
    expect(fmtSize(0)).toBe('0.0 B');
    expect(fmtSize(512)).toBe('512.0 B');
    expect(fmtSize(1023)).toBe('1023.0 B');
  });

  test('formats kilobytes', () => {
    expect(fmtSize(1024)).toBe('1.0 KB');
    expect(fmtSize(2048)).toBe('2.0 KB');
    expect(fmtSize(1536)).toBe('1.5 KB');
  });

  test('formats megabytes', () => {
    expect(fmtSize(1024 * 1024)).toBe('1.0 MB');
    expect(fmtSize(1024 * 1024 * 2.5)).toBe('2.5 MB');
  });

  test('formats gigabytes', () => {
    expect(fmtSize(1024 ** 3)).toBe('1.0 GB');
  });

  test('formats terabytes', () => {
    expect(fmtSize(1024 ** 4)).toBe('1.0 TB');
  });

  test('formats values beyond TB as TB', () => {
    expect(fmtSize(1024 ** 5)).toBe('1024.0 TB');
  });
});

describe('isHidden', () => {
  test('returns true for names starting with dot', () => {
    expect(isHidden('.git')).toBe(true);
    expect(isHidden('.env')).toBe(true);
    expect(isHidden('.')).toBe(true);
  });

  test('returns false for normal names', () => {
    expect(isHidden('src')).toBe(false);
    expect(isHidden('README.md')).toBe(false);
    expect(isHidden('node_modules')).toBe(false);
  });
});

describe('matchesIgnore', () => {
  test('returns false when patterns list is empty', () => {
    expect(matchesIgnore('anything', [])).toBe(false);
  });

  test('matches exact names', () => {
    expect(matchesIgnore('node_modules', ['node_modules'])).toBe(true);
    expect(matchesIgnore('src', ['node_modules'])).toBe(false);
  });

  test('matches * wildcard (any sequence)', () => {
    expect(matchesIgnore('test.js', ['*.js'])).toBe(true);
    expect(matchesIgnore('test.ts', ['*.js'])).toBe(false);
    expect(matchesIgnore('build', ['build*'])).toBe(true);
    expect(matchesIgnore('build-prod', ['build*'])).toBe(true);
  });

  test('matches ? wildcard (single character)', () => {
    expect(matchesIgnore('log1', ['log?'])).toBe(true);
    expect(matchesIgnore('log12', ['log?'])).toBe(false);
    expect(matchesIgnore('log', ['log?'])).toBe(false);
  });

  test('matches against multiple patterns (any match wins)', () => {
    expect(matchesIgnore('dist', ['node_modules', 'dist', '.cache'])).toBe(true);
    expect(matchesIgnore('src', ['node_modules', 'dist'])).toBe(false);
  });

  test('escapes regex special characters in patterns', () => {
    expect(matchesIgnore('a.b', ['a.b'])).toBe(true);
    expect(matchesIgnore('axb', ['a.b'])).toBe(false);
  });
});
