const fs = require('fs');
const path = require('path');
const { orderedWarning } = require('./schema');

function readJsonLines(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const rows = [];
  const warnings = [];
  const lines = content.split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    const text = lines[index];
    if (text.trim() === '') continue;
    try {
      rows.push({ line: index + 1, value: JSON.parse(text) });
    } catch (error) {
      warnings.push(orderedWarning('invalid_json', index + 1, null, text));
    }
  }
  return { rows, warnings };
}

function writeReport(filePath, report) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
}

module.exports = { readJsonLines, writeReport };
