'use strict';

/**
 * Core todo business logic: add, list, done, delete, export, stats.
 *
 * All functions accept a store object (from readStore), mutate it in memory,
 * and return it. The caller is responsible for writing it back with writeStore.
 */

const { generateId, fmtDate, parseDueDate, validatePriority, isOverdue } = require('./utils');

/**
 * Add a new todo item to the store.
 *
 * @param {{ version: number, todos: object[] }} store
 * @param {string} title
 * @param {object} opts
 * @param {string} [opts.project]
 * @param {string} [opts.priority]
 * @param {string} [opts.due]
 * @param {string[]} [opts.tag]
 * @returns {{ ok: true, store: object, item: object } | { ok: false, code: number, error: string }}
 */
function addTodo(store, title, opts) {
  if (!title || !title.trim()) {
    return { ok: false, code: 2, error: 'title cannot be empty' };
  }

  const priority = opts.priority || 'normal';
  const priorityResult = validatePriority(priority);
  if (!priorityResult.ok) {
    return { ok: false, code: 2, error: priorityResult.error };
  }

  let due = null;
  if (opts.due) {
    const dateResult = parseDueDate(opts.due);
    if (!dateResult.ok) {
      return { ok: false, code: 2, error: dateResult.error };
    }
    due = dateResult.date;
  }

  const item = {
    id: generateId(),
    title: title.trim(),
    status: 'open',
    project: opts.project || null,
    priority,
    tags: opts.tag || [],
    due,
    created_at: new Date().toISOString(),
    completed_at: null,
  };

  store.todos.push(item);
  return { ok: true, store, item };
}

/**
 * Filter todos by the given criteria.
 *
 * @param {{ version: number, todos: object[] }} store
 * @param {object} opts
 * @param {string} [opts.status]   - 'open', 'done', or 'all' (default: 'open')
 * @param {string} [opts.project]
 * @param {string} [opts.priority]
 * @param {string} [opts.tag]
 * @param {boolean} [opts.overdue]
 * @returns {object[]}
 */
function filterTodos(store, opts) {
  const status = opts.status || 'open';

  return store.todos.filter(t => {
    if (status !== 'all' && t.status !== status) return false;
    if (opts.project && t.project !== opts.project) return false;
    if (opts.priority && t.priority !== opts.priority) return false;
    if (opts.tag && !t.tags.includes(opts.tag)) return false;
    if (opts.overdue && !isOverdue(t)) return false;
    return true;
  });
}

/**
 * Render a single todo item as a formatted text line.
 *
 * @param {object} item
 * @returns {string}
 */
function fmtTodo(item) {
  const status = item.status === 'done' ? '[x]' : '[ ]';
  const priority = item.priority !== 'normal' ? ` [${item.priority}]` : '';
  const project = item.project ? ` @${item.project}` : '';
  const tags = item.tags.length > 0 ? ` #${item.tags.join(' #')}` : '';
  const due = item.due ? ` due:${fmtDate(item.due)}` : '';
  const overdue = isOverdue(item) ? ' OVERDUE' : '';
  return `${status} ${item.id}  ${item.title}${priority}${project}${tags}${due}${overdue}`;
}

/**
 * List todos with optional filters and output format.
 *
 * Prints to stdout. Returns exit code.
 *
 * @param {{ version: number, todos: object[] }} store
 * @param {object} opts
 * @returns {number} Exit code.
 */
function runList(store, opts) {
  const items = filterTodos(store, opts);

  if (opts.format === 'json') {
    console.log(JSON.stringify(items, null, 2));
    return 0;
  }

  if (items.length === 0) {
    console.log('No todos found.');
    return 0;
  }

  items.forEach(item => console.log(fmtTodo(item)));
  return 0;
}

/**
 * Add a todo and print confirmation.
 *
 * @param {{ version: number, todos: object[] }} store
 * @param {string} title
 * @param {object} opts
 * @returns {{ ok: boolean, code: number, store?: object }}
 */
function runAdd(store, title, opts) {
  const result = addTodo(store, title, opts);
  if (!result.ok) {
    console.error(`Error: ${result.error}`);
    return { ok: false, code: result.code };
  }
  console.log(`Added: ${result.item.id}  ${result.item.title}`);
  return { ok: true, code: 0, store: result.store };
}

/**
 * Find exactly one todo by full ID or unambiguous prefix.
 *
 * @param {{ version: number, todos: object[] }} store
 * @param {string} id - Full ID or prefix.
 * @returns {{ ok: true, item: object, index: number } | { ok: false, code: number, error: string }}
 */
function findById(store, id) {
  if (!id || !id.trim()) {
    return { ok: false, code: 2, error: 'id cannot be empty' };
  }
  const matches = store.todos
    .map((item, index) => ({ item, index }))
    .filter(({ item }) => item.id.startsWith(id.trim()));

  if (matches.length === 0) {
    return { ok: false, code: 1, error: `no todo found with id: '${id}'` };
  }
  if (matches.length > 1) {
    return { ok: false, code: 1, error: `ambiguous id '${id}' matches ${matches.length} todos` };
  }
  return { ok: true, item: matches[0].item, index: matches[0].index };
}

/**
 * Mark a todo as done and record the completion timestamp.
 *
 * @param {{ version: number, todos: object[] }} store
 * @param {string} id
 * @returns {{ ok: boolean, code: number, store?: object }}
 */
function runDone(store, id) {
  const result = findById(store, id);
  if (!result.ok) {
    console.error(`Error: ${result.error}`);
    return { ok: false, code: result.code };
  }

  const item = result.item;
  if (item.status === 'done') {
    console.error(`Error: todo '${item.id}' is already done`);
    return { ok: false, code: 1 };
  }

  item.status = 'done';
  item.completed_at = new Date().toISOString();
  console.log(`Done: ${item.id}  ${item.title}`);
  return { ok: true, code: 0, store };
}

/**
 * Permanently delete a todo from the store.
 *
 * @param {{ version: number, todos: object[] }} store
 * @param {string} id
 * @returns {{ ok: boolean, code: number, store?: object }}
 */
function runDelete(store, id) {
  const result = findById(store, id);
  if (!result.ok) {
    console.error(`Error: ${result.error}`);
    return { ok: false, code: result.code };
  }

  const item = result.item;
  store.todos.splice(result.index, 1);
  console.log(`Deleted: ${item.id}  ${item.title}`);
  return { ok: true, code: 0, store };
}

/**
 * Export todos to JSON or CSV.
 *
 * @param {{ version: number, todos: object[] }} store
 * @param {object} opts
 * @param {string} [opts.format] - 'json' or 'csv' (default: 'json')
 * @param {string} [opts.status] - 'open', 'done', or 'all' (default: 'all')
 * @param {string} [opts.output] - File path to write to instead of stdout.
 * @returns {number} Exit code.
 */
function runExport(store, opts) {
  const fs = require('fs');

  const format = opts.format || 'json';
  if (!['json', 'csv'].includes(format)) {
    console.error(`Error: invalid export format: '${format}' (expected json or csv)`);
    return 2;
  }

  const items = filterTodos(store, { status: opts.status || 'all' });

  let output;
  if (format === 'csv') {
    const header = 'id,title,status,project,priority,tags,due,created_at,completed_at';
    const rows = items.map(t => [
      t.id,
      `"${t.title.replace(/"/g, '""')}"`,
      t.status,
      t.project || '',
      t.priority,
      t.tags.join('|'),
      t.due || '',
      t.created_at,
      t.completed_at || '',
    ].join(','));
    output = [header, ...rows].join('\n') + '\n';
  } else {
    output = JSON.stringify(items, null, 2) + '\n';
  }

  if (opts.output) {
    try {
      fs.writeFileSync(opts.output, output, 'utf8');
      console.log(`Exported ${items.length} item(s) to ${opts.output}`);
    } catch (err) {
      console.error(`Error: cannot write to ${opts.output}: ${err.message}`);
      return 1;
    }
  } else {
    process.stdout.write(output);
  }

  return 0;
}

/**
 * Print counts and breakdowns by project and priority.
 *
 * @param {{ version: number, todos: object[] }} store
 * @param {object} opts
 * @param {string} [opts.project] - Scope stats to one project.
 * @param {string} [opts.format]  - 'text' or 'json' (default: 'text')
 * @returns {number} Exit code.
 */
function runStats(store, opts) {
  let todos = store.todos;
  if (opts.project) {
    todos = todos.filter(t => t.project === opts.project);
  }

  const total = todos.length;
  const open = todos.filter(t => t.status === 'open').length;
  const done = todos.filter(t => t.status === 'done').length;
  const overdue = todos.filter(t => isOverdue(t)).length;

  const byProject = {};
  const byPriority = { low: 0, normal: 0, high: 0 };

  for (const t of todos) {
    const proj = t.project || '(none)';
    byProject[proj] = (byProject[proj] || 0) + 1;
    byPriority[t.priority] = (byPriority[t.priority] || 0) + 1;
  }

  if (opts.format === 'json') {
    console.log(JSON.stringify({ total, open, done, overdue, by_project: byProject, by_priority: byPriority }, null, 2));
    return 0;
  }

  console.log(`Total:    ${total}`);
  console.log(`Open:     ${open}`);
  console.log(`Done:     ${done}`);
  console.log(`Overdue:  ${overdue}`);

  if (Object.keys(byProject).length > 0) {
    console.log('\nBy project:');
    for (const [proj, count] of Object.entries(byProject).sort()) {
      console.log(`  ${proj}: ${count}`);
    }
  }

  console.log('\nBy priority:');
  for (const level of ['high', 'normal', 'low']) {
    console.log(`  ${level}: ${byPriority[level] || 0}`);
  }

  return 0;
}

module.exports = { addTodo, filterTodos, fmtTodo, runAdd, runList, runDone, runDelete, runExport, runStats };
