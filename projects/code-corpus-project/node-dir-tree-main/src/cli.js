#!/usr/bin/env node
'use strict';

/**
 * CLI entry point for dirtree.
 *
 * Subcommands:
 *   tree     - print a visual directory tree
 *   summary  - print file/directory counts and total size
 *
 * Exit codes:
 *   0  success
 *   1  path does not exist or is not a directory
 *   2  invalid arguments
 */

const { Command } = require('commander');
const { version } = require('../package.json');

const program = new Command();

program
  .name('dirtree')
  .description('Print directory trees with depth limiting, ignore patterns, size display, and JSON output')
  .version(version);

/** Collector for repeatable --ignore options. */
function collect(val, prev) {
  return prev.concat([val]);
}

program
  .command('tree <path>')
  .description('Print a visual directory tree')
  .option('--depth <n>', 'Max depth to recurse (default: unlimited)')
  .option('--ignore <pattern>', 'Glob pattern to exclude, repeatable', collect, [])
  .option('--hidden', 'Include hidden files and directories')
  .option('--size', 'Show file size next to each entry')
  .option('--format <format>', 'Output format: text or json', 'text')
  .action((dirPath, opts) => {
    const { runTree } = require('./tree');
    process.exit(runTree(dirPath, opts));
  });

program
  .command('summary <path>')
  .description('Print file/directory counts and total size')
  .option('--depth <n>', 'Max depth to recurse (default: unlimited)')
  .option('--ignore <pattern>', 'Glob pattern to exclude, repeatable', collect, [])
  .option('--hidden', 'Include hidden files and directories')
  .option('--format <format>', 'Output format: text or json', 'text')
  .action((dirPath, opts) => {
    const { runSummary } = require('./summary');
    process.exit(runSummary(dirPath, opts));
  });

program.parse();
