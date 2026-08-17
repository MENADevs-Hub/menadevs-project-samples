const path = require("path");

function absolutePath(value, cwd = process.cwd()) {
  if (!value) return value;
  return path.isAbsolute(value) ? value : path.join(cwd, value);
}

module.exports = { absolutePath };
