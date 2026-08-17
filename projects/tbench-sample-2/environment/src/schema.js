function orderedWarning(code, line, eventId, detail) {
  return { code, line, event_id: eventId ?? null, detail: String(detail ?? "") };
}

function reason(code, scope, eventId, since, expiresAt) {
  return { code, scope, event_id: eventId, since, expires_at: expiresAt };
}

module.exports = { orderedWarning, reason };
