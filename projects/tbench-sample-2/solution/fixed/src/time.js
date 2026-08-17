function parseTimestamp(value) {
  if (typeof value !== 'string') return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date;
}

function toIso(date) {
  return date.toISOString();
}

function addDays(date, days) {
  return new Date(date.getTime() + Number(days) * 24 * 60 * 60 * 1000);
}

function isActiveAt(reason, asOfDate) {
  if (!reason.expires_at) return true;
  return asOfDate.getTime() < new Date(reason.expires_at).getTime();
}

module.exports = { parseTimestamp, toIso, addDays, isActiveAt };
