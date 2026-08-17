'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { buildSummary, runSummary } = require('../src/summary');

/** Create a temp directory tree and return its root path. */
function makeTree(structure) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'dirtree-summary-test-'));
  for (const [rel, content] of Object.entries(structure)) {
    const full = path.join(root, rel);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    if (content === null) {
      fs.mkdirSync(full, { recursive: true });
    } else {
      fs.writeFileSync(full, content);
    }
  }
  return root;
}

describe('buildSummary', () => {
  test('counts files and directories correctly', () => {
    const root = makeTree({
      'a.txt': '12345',     // 5 bytes
      'b.txt': '12',        // 2 bytes
      'sub/c.txt': '123',   // 3 bytes
    });
    const opts = { maxDepth: null, ignorePatterns: [], showHidden: false };
    const result = buildSummary(root, opts, 1);
    expect(result.files).toBe(3);
    expect(result.dirs).toBe(1);
    expect(result.size).toBe(10);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('depth 1 does not recurse into subdirectories', () => {
    const root = makeTree({
      'top.txt': 'hi',
      'sub/deep.txt': 'deep content',
    });
    const opts = { maxDepth: 1, ignorePatterns: [], showHidden: false };
    const result = buildSummary(root, opts, 1);
    expect(result.files).toBe(1);
    expect(result.dirs).toBe(1);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('hidden files excluded by default', () => {
    const root = makeTree({
      '.hidden': 'secret',
      'visible.txt': 'ok',
    });
    const opts = { maxDepth: null, ignorePatterns: [], showHidden: false };
    const result = buildSummary(root, opts, 1);
    expect(result.files).toBe(1);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('hidden files included when showHidden is true', () => {
    const root = makeTree({
      '.hidden': 'secret',
      'visible.txt': 'ok',
    });
    const opts = { maxDepth: null, ignorePatterns: [], showHidden: true };
    const result = buildSummary(root, opts, 1);
    expect(result.files).toBe(2);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('ignore patterns exclude matching entries', () => {
    const root = makeTree({
      'node_modules/pkg/a.js': '',
      'src/index.js': '',
    });
    const opts = { maxDepth: null, ignorePatterns: ['node_modules'], showHidden: false };
    const result = buildSummary(root, opts, 1);
    expect(result.files).toBe(1);
    expect(result.dirs).toBe(1);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('empty directory returns zero counts', () => {
    const root = makeTree({});
    const opts = { maxDepth: null, ignorePatterns: [], showHidden: false };
    const result = buildSummary(root, opts, 1);
    expect(result.files).toBe(0);
    expect(result.dirs).toBe(0);
    expect(result.size).toBe(0);
    fs.rmSync(root, { recursive: true, force: true });
  });
});

describe('runSummary (integration)', () => {
  test('returns 1 for non-existent path', () => {
    expect(runSummary('/no/such/path/exists', {})).toBe(1);
  });

  test('returns 1 for a file path', () => {
    const root = makeTree({ 'only.txt': 'x' });
    expect(runSummary(path.join(root, 'only.txt'), {})).toBe(1);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('returns 2 for invalid --depth value', () => {
    const root = makeTree({ 'f.txt': '' });
    expect(runSummary(root, { depth: 'bad' })).toBe(2);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('returns 0 for valid directory (text mode)', () => {
    const root = makeTree({ 'f.txt': 'hello' });
    expect(runSummary(root, {})).toBe(0);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('returns 0 for valid directory (json mode)', () => {
    const root = makeTree({ 'f.txt': 'hello' });
    expect(runSummary(root, { format: 'json' })).toBe(0);
    fs.rmSync(root, { recursive: true, force: true });
  });
});
