const { orderedWarning } = require('./schema');
const { SuppressionState } = require('./state');

function dedupeEvents(events, warnings) {
  const seen = new Set();
  const kept = [];
  for (const event of events) {
    if (seen.has(event.event_id)) {
      warnings.push(orderedWarning('duplicate_event', event.line, event.event_id, event.event_id));
      continue;
    }
    seen.add(event.event_id);
    kept.push(event);
  }
  return kept;
}

function evaluate(events, asOfDate, warnings) {
  const state = new SuppressionState();
  const asOfMs = asOfDate.getTime();
  const deduped = dedupeEvents(events, warnings)
    .filter((event) => {
      if (event.timestampMs > asOfMs) {
        return false;
      }
      return true;
    })
    .sort((a, b) => a.line - b.line);

  for (const event of deduped) {
    state.apply(event);
  }
  return state;
}

module.exports = { evaluate };
