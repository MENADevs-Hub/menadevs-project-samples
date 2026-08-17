const DEFAULT_WINDOWS = Object.freeze({
  hard_bounce: 180,
  soft_bounce: 14
});

const REASON_ORDER = Object.freeze([
  "complaint",
  "hard_bounce",
  "soft_bounce",
  "unsubscribe"
]);

const SUPPORTED_TYPES = new Set(["bounce", "complaint", "unsubscribe", "resubscribe"]);

module.exports = { DEFAULT_WINDOWS, REASON_ORDER, SUPPORTED_TYPES };
