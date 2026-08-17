'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { buildTree, buildTreeData, runTree } = require('../src/tree');

/** Create a temp directory tree and return its root path. */
function makeTree(structure) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'dirtree-test-'));
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

afterEach(() => {
  // Jest cleans up temp dirs automatically; mkdtempSync dirs are in os.tmpdir()
});

describe('buildTree (text output)', () => {
  test('lists files and directories', () => {
    const root = makeTree({
      'file.txt': 'hello',
      'sub/nested.txt': 'world',
    });
    const opts = { maxDepth: null, ignorePatterns: [], showHidden: false, showSize: false };
    const lines = buildTree(root, opts, '', 1);
    const text = lines.join('\n');
    expect(text).toContain('sub/');
    expect(text).toContain('file.txt');
    expect(text).toContain('nested.txt');
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('depth limit stops recursion', () => {
    const root = makeTree({
      'a/b/deep.txt': 'deep',
    });
    const opts = { maxDepth: 1, ignorePatterns: [], showHidden: false, showSize: false };
    const lines = buildTree(root, opts, '', 1);
    const text = lines.join('\n');
    expect(text).toContain('a/');
    expect(text).not.toContain('b/');
    expect(text).not.toContain('deep.txt');
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('hidden files excluded by default', () => {
    const root = makeTree({
      '.hidden': 'secret',
      'visible.txt': 'shown',
    });
    const opts = { maxDepth: null, ignorePatterns: [], showHidden: false, showSize: false };
    const lines = buildTree(root, opts, '', 1);
    const text = lines.join('\n');
    expect(text).not.toContain('.hidden');
    expect(text).toContain('visible.txt');
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('hidden files included when showHidden is true', () => {
    const root = makeTree({
      '.hidden': 'secret',
      'visible.txt': 'shown',
    });
    const opts = { maxDepth: null, ignorePatterns: [], showHidden: true, showSize: false };
    const lines = buildTree(root, opts, '', 1);
    const text = lines.join('\n');
    expect(text).toContain('.hidden');
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('ignore pattern excludes matching entries', () => {
    const root = makeTree({
      'node_modules/pkg/index.js': '',
      'src/index.js': '',
    });
    const opts = { maxDepth: null, ignorePatterns: ['node_modules'], showHidden: false, showSize: false };
    const lines = buildTree(root, opts, '', 1);
    const text = lines.join('\n');
    expect(text).not.toContain('node_modules');
    expect(text).toContain('src/');
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('showSize appends human-readable size to files', () => {
    const root = makeTree({ 'data.bin': 'A'.repeat(1024) });
    const opts = { maxDepth: null, ignorePatterns: [], showHidden: false, showSize: true };
    const lines = buildTree(root, opts, '', 1);
    expect(lines.some(l => l.includes('data.bin') && l.includes('KB'))).toBe(true);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('uses correct ASCII connectors', () => {
    const root = makeTree({ 'a.txt': '1', 'b.txt': '2' });
    const opts = { maxDepth: null, ignorePatterns: [], showHidden: false, showSize: false };
    const lines = buildTree(root, opts, '', 1);
    expect(lines[lines.length - 1]).toMatch(/^└── /);
    expect(lines.slice(0, -1).every(l => l.startsWith('├── '))).toBe(true);
    fs.rmSync(root, { recursive: true, force: true });
  });
});

describe('buildTreeData (JSON output)', () => {
  test('returns root directory node with children', () => {
    const root = makeTree({ 'a.txt': 'hi', 'sub/b.txt': '' });
    const opts = { maxDepth: null, ignorePatterns: [], showHidden: false, showSize: false };
    const data = buildTreeData(root, opts, 1);
    expect(data.type).toBe('directory');
    expect(Array.isArray(data.children)).toBe(true);
    const names = data.children.map(c => c.name);
    expect(names).toContain('sub');
    expect(names).toContain('a.txt');
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('file nodes include size', () => {
    const root = makeTree({ 'x.txt': 'hello' });
    const opts = { maxDepth: null, ignorePatterns: [], showHidden: false, showSize: false };
    const data = buildTreeData(root, opts, 1);
    const file = data.children.find(c => c.name === 'x.txt');
    expect(file.type).toBe('file');
    expect(typeof file.size).toBe('number');
    expect(file.size).toBe(5);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('depth limit returns empty children for truncated dirs', () => {
    const root = makeTree({ 'a/b/c.txt': 'deep' });
    const opts = { maxDepth: 1, ignorePatterns: [], showHidden: false, showSize: false };
    const data = buildTreeData(root, opts, 1);
    const subA = data.children.find(c => c.name === 'a');
    expect(subA.children).toHaveLength(0);
    fs.rmSync(root, { recursive: true, force: true });
  });
});

describe('runTree (integration)', () => {
  test('returns 1 for non-existent path', () => {
    expect(runTree('/no/such/path/exists', {})).toBe(1);
  });

  test('returns 1 for a file path', () => {
    const root = makeTree({ 'only.txt': 'x' });
    expect(runTree(path.join(root, 'only.txt'), {})).toBe(1);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('returns 2 for invalid --depth value', () => {
    const root = makeTree({ 'f.txt': '' });
    expect(runTree(root, { depth: 'abc' })).toBe(2);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('returns 0 for valid directory (text mode)', () => {
    const root = makeTree({ 'f.txt': '' });
    expect(runTree(root, {})).toBe(0);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test('returns 0 for valid directory (json mode)', () => {
    const root = makeTree({ 'f.txt': '' });
    expect(runTree(root, { format: 'json' })).toBe(0);
    fs.rmSync(root, { recursive: true, force: true });
  });
});
