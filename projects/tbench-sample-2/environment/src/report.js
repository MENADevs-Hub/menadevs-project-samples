const { REASON_ORDER } = require('./constants');
const { isActiveAt } = require('./time');

function reasonRank(code) {
  const index = REASON_ORDER.indexOf(code);
  return index === -1 ? REASON_ORDER.length : index;
}

function sortReasons(reasons) {
  return reasons.slice().sort((a, b) => {
    return reasonRank(a.code) - reasonRank(b.code)
      || a.scope.localeCompare(b.scope)
      || a.since.localeCompare(b.since)
      || a.event_id.localeCompare(b.event_id);
  });
}

function sortWarnings(warnings) {
  return warnings.slice().sort((a, b) => {
    return a.line - b.line
      || a.code.localeCompare(b.code)
      || String(a.event_id ?? '').localeCompare(String(b.event_id ?? ''));
  });
}

function buildReport(state, asOfIso, warnings) {
  const asOfDate = new Date(asOfIso);
  const recipients = Array.from(state.recipients.entries())
    .map(([email, reasons]) => {
      const activeReasons = sortReasons(reasons.filter((current) => isActiveAt(current, asOfDate)));
      return { email, suppressed: activeReasons.length > 0, reasons: activeReasons };
    })
    .sort((a, b) => a.email.localeCompare(b.email));

  const activeReasonCounts = { complaint: 0, hard_bounce: 0, soft_bounce: 0, unsubscribe: 0 };
  for (const recipient of recipients) {
    for (const reason of recipient.reasons) {
      activeReasonCounts[reason.code] += 1;
    }
  }

  const sortedWarnings = sortWarnings(warnings);
  return {
    as_of: asOfIso,
    summary: {
      total_recipients: recipients.length,
      suppressed_recipients: recipients.filter((recipient) => recipient.suppressed).length,
      warning_count: sortedWarnings.length,
      active_reason_counts: activeReasonCounts
    },
    recipients,
    warnings: sortedWarnings
  };
}

module.exports = { buildReport, sortReasons, sortWarnings };
