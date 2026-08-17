const { SUPPORTED_TYPES } = require('./constants');
const { looksLikeEmail } = require('./email');
const { normalizeEmail, normalizeListId } = require('./normalize');
const { parseTimestamp, toIso } = require('./time');
const { orderedWarning } = require('./schema');

function validateRows(rows, warnings) {
  const valid = [];
  for (const row of rows) {
    const value = row.value || {};
    const eventId = typeof value.event_id === 'string' && value.event_id.trim() ? value.event_id.trim() : null;
    if (!eventId) {
      warnings.push(orderedWarning('missing_event_id', row.line, null, 'event_id'));
      continue;
    }
    if (typeof value.email !== 'string' || !value.email.trim()) {
      warnings.push(orderedWarning('missing_email', row.line, eventId, value.email));
      continue;
    }
    if (!looksLikeEmail(value.email)) {
      warnings.push(orderedWarning('invalid_email', row.line, eventId, value.email));
      continue;
    }
    if (typeof value.timestamp !== 'string') {
      warnings.push(orderedWarning('invalid_timestamp', row.line, eventId, value.timestamp));
      continue;
    }
    const timestamp = parseTimestamp(value.timestamp);
    if (!timestamp) {
      warnings.push(orderedWarning('invalid_timestamp', row.line, eventId, value.timestamp));
      continue;
    }
    const type = typeof value.type === 'string' ? value.type : '';
    if (!SUPPORTED_TYPES.has(type)) {
      warnings.push(orderedWarning('unknown_type', row.line, eventId, type));
      continue;
    }
    const listId = normalizeListId(value.list_id);
    if (type === 'unsubscribe' && !listId) {
      warnings.push(orderedWarning('missing_list', row.line, eventId, 'list_id'));
      continue;
    }
    const subtype = value.subtype || 'hard';
    if (type === 'bounce' && subtype !== 'hard' && subtype !== 'soft') {
      warnings.push(orderedWarning('unknown_bounce_subtype', row.line, eventId, subtype));
      continue;
    }
    let expiryDays = value.expiry_days;
    if (expiryDays !== undefined && (!Number.isInteger(expiryDays) || expiryDays < 0)) {
      warnings.push(orderedWarning('invalid_expiry_days', row.line, eventId, expiryDays));
      expiryDays = undefined;
    }
    valid.push({
      line: row.line,
      event_id: eventId,
      email: normalizeEmail(value.email),
      type,
      subtype,
      timestamp: toIso(timestamp),
      timestampMs: timestamp.getTime(),
      list_id: listId,
      expiry_days: expiryDays
    });
  }
  return valid;
}

module.exports = { validateRows };
