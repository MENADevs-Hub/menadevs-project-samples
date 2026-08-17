'use strict';

const { addTodo, filterTodos, runDone, runDelete, runExport, runStats, fmtTodo } = require('../src/todos');
const { emptyStore } = require('../src/store');

function makeStore(...items) {
  const store = emptyStore();
  for (const item of items) {
    addTodo(store, item.title, item);
  }
  return store;
}

describe('addTodo', () => {
  test('adds an item with all fields', () => {
    const store = emptyStore();
    const result = addTodo(store, 'Buy milk', { project: 'home', priority: 'high', due: '2026-07-01', tag: ['errand'] });
    expect(result.ok).toBe(true);
    expect(store.todos).toHaveLength(1);
    const item = store.todos[0];
    expect(item.title).toBe('Buy milk');
    expect(item.project).toBe('home');
    expect(item.priority).toBe('high');
    expect(item.due).toBe('2026-07-01');
    expect(item.tags).toEqual(['errand']);
    expect(item.status).toBe('open');
    expect(item.completed_at).toBeNull();
  });

  test('uses normal priority by default', () => {
    const store = emptyStore();
    addTodo(store, 'Task', {});
    expect(store.todos[0].priority).toBe('normal');
  });

  test('returns error for empty title', () => {
    const store = emptyStore();
    const result = addTodo(store, '  ', {});
    expect(result.ok).toBe(false);
    expect(result.code).toBe(2);
  });

  test('returns error for invalid priority', () => {
    const store = emptyStore();
    const result = addTodo(store, 'Task', { priority: 'urgent' });
    expect(result.ok).toBe(false);
    expect(result.code).toBe(2);
  });

  test('returns error for invalid due date', () => {
    const store = emptyStore();
    const result = addTodo(store, 'Task', { due: 'next-week' });
    expect(result.ok).toBe(false);
    expect(result.code).toBe(2);
  });
});

describe('filterTodos', () => {
  test('returns open items by default', () => {
    const store = makeStore({ title: 'A' }, { title: 'B' });
    runDone(store, store.todos[0].id);
    const result = filterTodos(store, {});
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe('B');
  });

  test('filters by project', () => {
    const store = makeStore(
      { title: 'A', project: 'work' },
      { title: 'B', project: 'home' }
    );
    const result = filterTodos(store, { status: 'all', project: 'work' });
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe('A');
  });

  test('filters by priority', () => {
    const store = makeStore(
      { title: 'A', priority: 'high' },
      { title: 'B', priority: 'low' }
    );
    const result = filterTodos(store, { status: 'all', priority: 'high' });
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe('A');
  });

  test('filters by tag', () => {
    const store = makeStore(
      { title: 'A', tag: ['urgent'] },
      { title: 'B', tag: ['later'] }
    );
    const result = filterTodos(store, { status: 'all', tag: 'urgent' });
    expect(result).toHaveLength(1);
  });

  test('filters overdue items', () => {
    const store = makeStore(
      { title: 'Past', due: '2020-01-01' },
      { title: 'Future', due: '2099-01-01' }
    );
    const result = filterTodos(store, { overdue: true });
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe('Past');
  });
});

describe('runDone', () => {
  test('marks item as done and sets completed_at', () => {
    const store = makeStore({ title: 'Task' });
    const id = store.todos[0].id;
    const result = runDone(store, id);
    expect(result.ok).toBe(true);
    expect(store.todos[0].status).toBe('done');
    expect(store.todos[0].completed_at).toBeTruthy();
  });

  test('supports prefix match', () => {
    const store = makeStore({ title: 'Task' });
    const prefix = store.todos[0].id.slice(0, 4);
    const result = runDone(store, prefix);
    expect(result.ok).toBe(true);
  });

  test('returns error code 1 for unknown id', () => {
    const store = emptyStore();
    const result = runDone(store, 'zzzzzzzz');
    expect(result.ok).toBe(false);
    expect(result.code).toBe(1);
  });

  test('returns error if already done', () => {
    const store = makeStore({ title: 'Task' });
    const id = store.todos[0].id;
    runDone(store, id);
    const result = runDone(store, id);
    expect(result.ok).toBe(false);
  });
});

describe('runDelete', () => {
  test('removes item from store', () => {
    const store = makeStore({ title: 'Task' });
    const id = store.todos[0].id;
    const result = runDelete(store, id);
    expect(result.ok).toBe(true);
    expect(store.todos).toHaveLength(0);
  });

  test('returns error code 1 for unknown id', () => {
    const store = emptyStore();
    const result = runDelete(store, 'zzzzzzzz');
    expect(result.ok).toBe(false);
    expect(result.code).toBe(1);
  });
});

describe('runExport', () => {
  test('returns 0 for JSON export to stdout', () => {
    const store = makeStore({ title: 'Task' });
    const code = runExport(store, { format: 'json', status: 'all' });
    expect(code).toBe(0);
  });

  test('returns 0 for CSV export to stdout', () => {
    const store = makeStore({ title: 'Task', tag: ['a', 'b'] });
    const code = runExport(store, { format: 'csv', status: 'all' });
    expect(code).toBe(0);
  });

  test('returns 2 for invalid format', () => {
    const store = emptyStore();
    const code = runExport(store, { format: 'xml', status: 'all' });
    expect(code).toBe(2);
  });
});

describe('runStats', () => {
  test('returns 0 for text output', () => {
    const store = makeStore({ title: 'A', project: 'work', priority: 'high' });
    expect(runStats(store, {})).toBe(0);
  });

  test('returns 0 for JSON output', () => {
    const store = makeStore({ title: 'A', project: 'work' });
    expect(runStats(store, { format: 'json' })).toBe(0);
  });

  test('scopes stats to a project', () => {
    const store = makeStore(
      { title: 'A', project: 'work' },
      { title: 'B', project: 'home' }
    );
    // Should not throw even when scoped
    expect(runStats(store, { project: 'work', format: 'json' })).toBe(0);
  });
});

describe('fmtTodo', () => {
  test('renders open item', () => {
    const store = makeStore({ title: 'Buy milk' });
    const line = fmtTodo(store.todos[0]);
    expect(line).toContain('[ ]');
    expect(line).toContain('Buy milk');
  });

  test('renders done item', () => {
    const store = makeStore({ title: 'Done task' });
    runDone(store, store.todos[0].id);
    const line = fmtTodo(store.todos[0]);
    expect(line).toContain('[x]');
  });

  test('renders project, tags, priority, and due date', () => {
    const store = makeStore({ title: 'T', project: 'work', priority: 'high', due: '2026-07-01', tag: ['urgent'] });
    const line = fmtTodo(store.todos[0]);
    expect(line).toContain('@work');
    expect(line).toContain('[high]');
    expect(line).toContain('due:2026-07-01');
    expect(line).toContain('#urgent');
  });
});
