function debug() {
  if (process.env.SUPPRESSION_DEBUG === "1") {
    console.error(...arguments);
  }
}

module.exports = { debug };
