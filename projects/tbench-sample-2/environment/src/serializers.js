function writeJsonStable(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

module.exports = { writeJsonStable };
