#!/usr/bin/env node
'use strict';

/**
 * CLI entry point for the todo manager.
 *
 * Subcommands:
 *   add     - Create a new todo item
 *   list    - List todos with optional filters
 *   done    - Mark a todo as complete
 *   delete  - Remove a todo permanently
 *   export  - Export todos to JSON or CSV
 *   stats   - Show counts and breakdowns
 *
 * Exit codes:
 *   0  success
 *   1  item not found, path error, or storage failure
 *   2  invalid arguments (bad date, bad priority, bad format)
 */

const { Command } = require('commander');
const { version } = require('../package.json');

const program = new Command();

program
  .name('todo')
  .description('CLI todo manager with projects, tags, priorities, due dates, and export')
  .version(version)
  .option('--storage <path>', 'Override default storage file path');

/** Collector for repeatable --tag options. */
function collect(val, prev) {
  return prev.concat([val]);
}

program
  .command('add <title>')
  .description('Add a new todo item')
  .option('--project <name>', 'Assign to a project')
  .option('--priority <level>', 'Priority: low, normal, or high (default: normal)', 'normal')
  .option('--due <date>', 'Due date in YYYY-MM-DD format')
  .option('--tag <tag>', 'Tag, repeatable', collect, [])
  .action((title, opts, cmd) => {
    const storage = cmd.parent.opts().storage;
    const { readStore, writeStore } = require('./store');
    const { runAdd } = require('./todos');
    const store = readStore(storage);
    const result = runAdd(store, title, opts);
    if (result.ok) writeStore(result.store, storage);
    process.exit(result.code);
  });

program
  .command('list')
  .description('List todos with optional filters')
  .option('--status <status>', 'Filter by status: open, done, or all (default: open)', 'open')
  .option('--project <name>', 'Filter by project')
  .option('--priority <level>', 'Filter by priority')
  .option('--tag <tag>', 'Filter by tag')
  .option('--overdue', 'Show only overdue items')
  .option('--format <format>', 'Output format: text or json (default: text)', 'text')
  .action((opts, cmd) => {
    const storage = cmd.parent.opts().storage;
    const { readStore } = require('./store');
    const { runList } = require('./todos');
    const store = readStore(storage);
    process.exit(runList(store, opts));
  });

program
  .command('done <id>')
  .description('Mark a todo as complete (prefix match allowed)')
  .action((id, _opts, cmd) => {
    const storage = cmd.parent.opts().storage;
    const { readStore, writeStore } = require('./store');
    const { runDone } = require('./todos');
    const store = readStore(storage);
    const result = runDone(store, id);
    if (result.ok) writeStore(result.store, storage);
    process.exit(result.code);
  });

program
  .command('delete <id>')
  .description('Delete a todo permanently (prefix match allowed)')
  .action((id, _opts, cmd) => {
    const storage = cmd.parent.opts().storage;
    const { readStore, writeStore } = require('./store');
    const { runDelete } = require('./todos');
    const store = readStore(storage);
    const result = runDelete(store, id);
    if (result.ok) writeStore(result.store, storage);
    process.exit(result.code);
  });

program
  .command('export')
  .description('Export todos to JSON or CSV')
  .option('--format <format>', 'Output format: json or csv (default: json)', 'json')
  .option('--status <status>', 'Which items to export: open, done, or all (default: all)', 'all')
  .option('--output <file>', 'Write to file instead of stdout')
  .action((opts, cmd) => {
    const storage = cmd.parent.opts().storage;
    const { readStore } = require('./store');
    const { runExport } = require('./todos');
    const store = readStore(storage);
    process.exit(runExport(store, opts));
  });

program
  .command('stats')
  .description('Show counts and breakdowns by project and priority')
  .option('--project <name>', 'Scope stats to one project')
  .option('--format <format>', 'Output format: text or json (default: text)', 'text')
  .action((opts, cmd) => {
    const storage = cmd.parent.opts().storage;
    const { readStore } = require('./store');
    const { runStats } = require('./todos');
    const store = readStore(storage);
    process.exit(runStats(store, opts));
  });

program.parse();
