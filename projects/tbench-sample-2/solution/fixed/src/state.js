const { DEFAULT_WINDOWS } = require('./constants');
const { reason } = require('./schema');
const { addDays, toIso } = require('./time');

function hasOwn(object, key) {
  return Object.prototype.hasOwnProperty.call(object, key);
}

function expirationFor(event, code, timestampDate) {
  let days;
  if (hasOwn(event, 'expiry_days') && event.expiry_days !== undefined) {
    days = event.expiry_days;
  } else {
    days = DEFAULT_WINDOWS[code];
  }
  if (days === undefined) return null;
  return toIso(addDays(timestampDate, days));
}

class SuppressionState {
  constructor() {
    this.recipients = new Map();
  }

  ensure(email) {
    if (!this.recipients.has(email)) this.recipients.set(email, []);
    return this.recipients.get(email);
  }

  addReason(email, nextReason) {
    const reasons = this.ensure(email);
    const kept = reasons.filter((current) => !(current.code === nextReason.code && current.scope === nextReason.scope));
    kept.push(nextReason);
    this.recipients.set(email, kept);
  }

  clearForResubscribe(email, listId) {
    const reasons = this.ensure(email);
    const kept = reasons.filter((current) => {
      if (current.code === 'complaint') return true;
      if (current.code === 'hard_bounce') return true;
      if (current.code === 'soft_bounce') return false;
      if (current.code === 'unsubscribe' && (!listId || current.scope === `list:${listId}`)) return false;
      return true;
    });
    this.recipients.set(email, kept);
  }

  apply(event) {
    const timestampDate = new Date(event.timestamp);
    this.ensure(event.email);
    if (event.type === 'complaint') {
      this.addReason(event.email, reason('complaint', 'global', event.event_id, event.timestamp, null));
    } else if (event.type === 'bounce') {
      const code = event.subtype === 'soft' ? 'soft_bounce' : 'hard_bounce';
      this.addReason(event.email, reason(code, 'global', event.event_id, event.timestamp, expirationFor(event, code, timestampDate)));
    } else if (event.type === 'unsubscribe') {
      this.addReason(event.email, reason('unsubscribe', `list:${event.list_id}`, event.event_id, event.timestamp, expirationFor(event, 'unsubscribe', timestampDate)));
    } else if (event.type === 'resubscribe') {
      this.clearForResubscribe(event.email, event.list_id);
    }
  }
}

module.exports = { SuppressionState };
