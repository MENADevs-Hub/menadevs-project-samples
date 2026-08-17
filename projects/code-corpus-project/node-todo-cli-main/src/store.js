'use strict';

/**
 * Persistent JSON storage for todo items.
 *
 * Reads and writes a single JSON file. If the file is missing it is created
 * on first write. If the file exists but is not valid JSON, the corrupted
 * file is renamed to a timestamped backup and a fresh empty store is used.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const DEFAULT_STORAGE_PATH = path.join(os.homedir(), '.todo-cli', 'todos.json');

const SCHEMA_VERSION = 1;

/** Return a blank, valid store object. */
function emptyStore() {
  return { version: SCHEMA_VERSION, todos: [] };
}

/**
 * Validate that obj looks like a well-formed store.
 * Returns true only if version and todos array are present.
 *
 * @param {unknown} obj
 * @returns {boolean}
 */
function isValidStore(obj) {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    typeof obj.version === 'number' &&
    Array.isArray(obj.todos)
  );
}

/**
 * Read the store from disk.
 *
 * Missing file → returns an empty store (no warning).
 * Corrupt file → backs up the file, warns to stderr, returns empty store.
 *
 * @param {string} [storagePath] - Override the default storage path.
 * @returns {{ version: number, todos: object[] }}
 */
function readStore(storagePath) {
  const filePath = storagePath || DEFAULT_STORAGE_PATH;

  if (!fs.existsSync(filePath)) {
    return emptyStore();
  }

  let raw;
  try {
    raw = fs.readFileSync(filePath, 'utf8');
  } catch (err) {
    console.error(`Warning: cannot read storage file ${filePath}: ${err.message}`);
    return emptyStore();
  }

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    const backup = `${filePath}.bak-${Date.now()}`;
    try {
      fs.renameSync(filePath, backup);
      console.error(`Warning: storage file was corrupted. Backup saved to ${backup}. Starting fresh.`);
    } catch {
      console.error('Warning: storage file was corrupted and could not be backed up. Starting fresh.');
    }
    return emptyStore();
  }

  if (!isValidStore(parsed)) {
    console.error('Warning: storage file has unexpected format. Starting fresh.');
    return emptyStore();
  }

  return parsed;
}

/**
 * Write the store to disk, creating the directory if needed.
 *
 * @param {{ version: number, todos: object[] }} store
 * @param {string} [storagePath] - Override the default storage path.
 * @returns {void}
 */
function writeStore(store, storagePath) {
  const filePath = storagePath || DEFAULT_STORAGE_PATH;
  const dir = path.dirname(filePath);

  try {
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(filePath, JSON.stringify(store, null, 2) + '\n', 'utf8');
  } catch (err) {
    console.error(`Error: cannot write storage file ${filePath}: ${err.message}`);
    process.exit(1);
  }
}

module.exports = { readStore, writeStore, emptyStore, DEFAULT_STORAGE_PATH };
