function looksLikeEmail(value) {
  return typeof value === "string" && /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value.trim());
}

module.exports = { looksLikeEmail };
