'use strict';

/**
 * Core tree-building logic for the dirtree tree command.
 *
 * Implements a two-pass approach: filter entries first, then render
 * ASCII connectors based on whether each entry is the last in its group.
 * Symlinks are labelled and never followed. Permission errors are reported
 * to stderr and the affected directory is skipped without stopping the walk.
 */

const fs = require('fs');
const path = require('path');
const { fmtSize, isHidden, matchesIgnore } = require('./utils');

/**
 * Filter and stat all entries in dirPath, returning an array of entry objects.
 * Entries that cannot be stat'd are warned about and excluded.
 *
 * @param {string} dirPath
 * @param {object} opts
 * @returns {{ name: string, fullPath: string, stat: fs.Stats }[]}
 */
function readEntries(dirPath, opts) {
  const { ignorePatterns, showHidden } = opts;

  let names;
  try {
    names = fs.readdirSync(dirPath);
  } catch (err) {
    const reason = err.code === 'EACCES' || err.code === 'EPERM'
      ? 'permission denied'
      : err.message;
    console.error(`Warning: cannot read directory ${dirPath}: ${reason}`);
    return [];
  }

  // Apply name-based filters
  names = names.filter(name => {
    if (!showHidden && isHidden(name)) return false;
    if (matchesIgnore(name, ignorePatterns)) return false;
    return true;
  });

  // Stat each entry once; warn and skip entries that cannot be stat'd
  const entries = names.map(name => {
    const fullPath = path.join(dirPath, name);
    try {
      const stat = fs.lstatSync(fullPath);
      return { name, fullPath, stat };
    } catch (err) {
      console.error(`Warning: cannot stat ${fullPath}: ${err.message}`);
      return null;
    }
  }).filter(Boolean);

  // Directories first, then files; each group sorted alphabetically
  entries.sort((a, b) => {
    const aDir = a.stat.isDirectory();
    const bDir = b.stat.isDirectory();
    if (aDir && !bDir) return -1;
    if (!aDir && bDir) return 1;
    return a.name.localeCompare(b.name);
  });

  return entries;
}

/**
 * Recursively build an array of ASCII tree lines for dirPath.
 *
 * @param {string} dirPath - Directory to list.
 * @param {object} opts - Rendering options.
 * @param {number|null} opts.maxDepth - Max depth below root (null = unlimited).
 * @param {string[]} opts.ignorePatterns - Glob patterns to exclude.
 * @param {boolean} opts.showHidden - Include names that start with ".".
 * @param {boolean} opts.showSize - Append formatted size to file entries.
 * @param {string} prefix - ASCII connector prefix accumulated from parent calls.
 * @param {number} depth - Current depth (1 = root's immediate children).
 * @returns {string[]} Formatted tree lines, one per filesystem entry.
 */
function buildTree(dirPath, opts, prefix, depth) {
  const { maxDepth, showSize } = opts;

  if (maxDepth !== null && depth > maxDepth) return [];

  const entries = readEntries(dirPath, opts);
  const lines = [];

  entries.forEach(({ name, fullPath, stat }, index) => {
    const isLast = index === entries.length - 1;
    const connector = isLast ? '└── ' : '├── ';
    const directory = stat.isDirectory();
    const symlink = stat.isSymbolicLink();

    let label;
    if (symlink) {
      label = `${name} [symlink]`;
    } else if (directory) {
      label = `${name}/`;
    } else {
      label = showSize ? `${name} (${fmtSize(stat.size)})` : name;
    }

    lines.push(`${prefix}${connector}${label}`);

    if (directory) {
      const childPrefix = prefix + (isLast ? '    ' : '│   ');
      lines.push(...buildTree(fullPath, opts, childPrefix, depth + 1));
    }
  });

  return lines;
}

/**
 * Recursively build a nested JSON-friendly node for dirPath.
 *
 * @param {string} dirPath
 * @param {object} opts
 * @param {number} depth
 * @returns {{ name: string, type: string, children?: Array, size?: number }}
 */
function buildTreeData(dirPath, opts, depth) {
  const { maxDepth } = opts;
  const node = { name: path.basename(dirPath), type: 'directory', children: [] };

  if (maxDepth !== null && depth > maxDepth) return node;

  const entries = readEntries(dirPath, opts);

  for (const { name, fullPath, stat } of entries) {
    if (stat.isSymbolicLink()) {
      node.children.push({ name, type: 'symlink' });
    } else if (stat.isDirectory()) {
      node.children.push(buildTreeData(fullPath, opts, depth + 1));
    } else {
      node.children.push({ name, type: 'file', size: stat.size });
    }
  }

  return node;
}

/**
 * Entry point for the tree subcommand.
 *
 * Validates the path, parses options, and renders the tree as text or JSON.
 *
 * @param {string} dirPath - Directory to display.
 * @param {object} cliOpts - Parsed commander options.
 * @returns {number} Exit code: 0 = success, 1 = bad path, 2 = bad args.
 */
function runTree(dirPath, cliOpts) {
  const resolved = path.resolve(dirPath);

  try {
    const stat = fs.statSync(resolved);
    if (!stat.isDirectory()) {
      console.error(`Error: path is not a directory: ${dirPath}`);
      return 1;
    }
  } catch {
    console.error(`Error: path does not exist: ${dirPath}`);
    return 1;
  }

  let maxDepth = null;
  if (cliOpts.depth !== undefined) {
    const n = parseInt(cliOpts.depth, 10);
    if (isNaN(n) || n < 0) {
      console.error('Error: --depth must be a non-negative integer');
      return 2;
    }
    maxDepth = n;
  }

  const opts = {
    maxDepth,
    ignorePatterns: cliOpts.ignore || [],
    showHidden: cliOpts.hidden || false,
    showSize: cliOpts.size || false,
  };

  if (cliOpts.format === 'json') {
    const data = buildTreeData(resolved, opts, 1);
    console.log(JSON.stringify(data, null, 2));
    return 0;
  }

  // Default: text output
  console.log(`${path.basename(resolved)}/`);
  const lines = buildTree(resolved, opts, '', 1);
  lines.forEach(line => console.log(line));

  return 0;
}

module.exports = { runTree, buildTree, buildTreeData };
