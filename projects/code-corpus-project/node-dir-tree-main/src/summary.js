'use strict';

/**
 * Summary command: aggregate file/directory counts and total size.
 *
 * Walks the directory tree applying the same filters as the tree command
 * (depth, ignore patterns, hidden files) and returns total counts and
 * cumulative size without rendering any visual output.
 */

const fs = require('fs');
const path = require('path');
const { fmtSize, isHidden, matchesIgnore } = require('./utils');

/**
 * Recursively accumulate counts and total size for dirPath.
 *
 * @param {string} dirPath - Directory to walk.
 * @param {object} opts - Walk options.
 * @param {number|null} opts.maxDepth - Max depth below root (null = unlimited).
 * @param {string[]} opts.ignorePatterns - Glob patterns to exclude.
 * @param {boolean} opts.showHidden - Include hidden entries.
 * @param {number} depth - Current depth (1 = root's immediate children).
 * @returns {{ files: number, dirs: number, size: number }}
 */
function buildSummary(dirPath, opts, depth) {
  const { maxDepth, ignorePatterns, showHidden } = opts;

  if (maxDepth !== null && depth > maxDepth) {
    return { files: 0, dirs: 0, size: 0 };
  }

  let names;
  try {
    names = fs.readdirSync(dirPath);
  } catch (err) {
    const reason = err.code === 'EACCES' || err.code === 'EPERM'
      ? 'permission denied'
      : err.message;
    console.error(`Warning: cannot read directory ${dirPath}: ${reason}`);
    return { files: 0, dirs: 0, size: 0 };
  }

  names = names.filter(name => {
    if (!showHidden && isHidden(name)) return false;
    if (matchesIgnore(name, ignorePatterns)) return false;
    return true;
  });

  let files = 0;
  let dirs = 0;
  let size = 0;

  for (const name of names) {
    const fullPath = path.join(dirPath, name);
    let stat;
    try {
      stat = fs.lstatSync(fullPath);
    } catch (err) {
      console.error(`Warning: cannot stat ${fullPath}: ${err.message}`);
      continue;
    }

    if (stat.isDirectory()) {
      dirs++;
      const sub = buildSummary(fullPath, opts, depth + 1);
      files += sub.files;
      dirs += sub.dirs;
      size += sub.size;
    } else {
      // Treat symlinks and regular files the same for counting purposes
      files++;
      size += stat.size;
    }
  }

  return { files, dirs, size };
}

/**
 * Entry point for the summary subcommand.
 *
 * Validates the path, walks the tree, and prints counts and total size
 * as text or JSON.
 *
 * @param {string} dirPath - Directory to summarise.
 * @param {object} cliOpts - Parsed commander options.
 * @returns {number} Exit code: 0 = success, 1 = bad path, 2 = bad args.
 */
function runSummary(dirPath, cliOpts) {
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
  };

  const result = buildSummary(resolved, opts, 1);

  if (cliOpts.format === 'json') {
    console.log(JSON.stringify({
      path: resolved,
      files: result.files,
      directories: result.dirs,
      total_size: result.size,
      total_size_human: fmtSize(result.size),
    }, null, 2));
    return 0;
  }

  // Default: text output
  console.log(`Directory:   ${resolved}`);
  console.log(`Files:       ${result.files}`);
  console.log(`Directories: ${result.dirs}`);
  console.log(`Total size:  ${fmtSize(result.size)}`);

  return 0;
}

module.exports = { runSummary, buildSummary };
