const { readJsonLines, writeReport } = require('./files');
const { validateRows } = require('./validate');
const { evaluate } = require('./evaluate');
const { buildReport } = require('./report');
const { parseTimestamp, toIso } = require('./time');
const { PlannerError } = require('./errors');

async function run({ eventsPath, asOf, outPath }) {
  const asOfDate = parseTimestamp(asOf);
  if (!asOfDate) throw new PlannerError(`Invalid --as-of timestamp: ${asOf}`);
  const asOfIso = toIso(asOfDate);
  const { rows, warnings } = readJsonLines(eventsPath);
  const validEvents = validateRows(rows, warnings);
  const state = evaluate(validEvents, asOfDate, warnings);
  const report = buildReport(state, asOfIso, warnings);
  writeReport(outPath, report);
  return report;
}

module.exports = { run };
