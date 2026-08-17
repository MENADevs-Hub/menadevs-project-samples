'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { readStore, writeStore, emptyStore } = require('../src/store');

function tempPath() {
  return path.join(os.tmpdir(), `todo-store-test-${Date.now()}-${Math.random().toString(36).slice(2)}.json`);
}

describe('emptyStore', () => {
  test('returns a valid store with version and empty todos', () => {
    const store = emptyStore();
    expect(store.version).toBe(1);
    expect(Array.isArray(store.todos)).toBe(true);
    expect(store.todos).toHaveLength(0);
  });
});

describe('readStore', () => {
  test('returns empty store when file does not exist', () => {
    const store = readStore('/no/such/file/todos.json');
    expect(store.todos).toHaveLength(0);
  });

  test('reads a valid store from disk', () => {
    const p = tempPath();
    const data = { version: 1, todos: [{ id: 'abc', title: 'Test' }] };
    fs.writeFileSync(p, JSON.stringify(data));
    const store = readStore(p);
    expect(store.todos).toHaveLength(1);
    expect(store.todos[0].id).toBe('abc');
    fs.unlinkSync(p);
  });

  test('returns empty store and backs up corrupted file', () => {
    const p = tempPath();
    fs.writeFileSync(p, 'not valid json {{{{');
    const store = readStore(p);
    expect(store.todos).toHaveLength(0);
    // Original file should be gone (renamed to backup)
    expect(fs.existsSync(p)).toBe(false);
    // Clean up backup
    const dir = path.dirname(p);
    const base = path.basename(p);
    const backups = fs.readdirSync(dir).filter(f => f.startsWith(base.replace('.json', '')));
    backups.forEach(b => fs.unlinkSync(path.join(dir, b)));
  });

  test('returns empty store for file with wrong schema', () => {
    const p = tempPath();
    fs.writeFileSync(p, JSON.stringify({ foo: 'bar' }));
    const store = readStore(p);
    expect(store.todos).toHaveLength(0);
    fs.unlinkSync(p);
  });
});

describe('writeStore', () => {
  test('writes store to disk and reads it back', () => {
    const p = tempPath();
    const store = { version: 1, todos: [{ id: 'x1', title: 'Hello' }] };
    writeStore(store, p);
    const read = JSON.parse(fs.readFileSync(p, 'utf8'));
    expect(read.todos[0].id).toBe('x1');
    fs.unlinkSync(p);
  });

  test('creates parent directory if it does not exist', () => {
    const dir = path.join(os.tmpdir(), `todo-test-dir-${Date.now()}`);
    const p = path.join(dir, 'nested', 'todos.json');
    writeStore(emptyStore(), p);
    expect(fs.existsSync(p)).toBe(true);
    fs.rmSync(dir, { recursive: true, force: true });
  });
});
