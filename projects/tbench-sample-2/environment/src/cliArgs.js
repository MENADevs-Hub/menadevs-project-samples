const { PlannerError } = require('./errors');

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (!key.startsWith('--')) {
      throw new PlannerError(`Unexpected argument: ${key}`);
    }
    const value = argv[i + 1];
    if (!value || value.startsWith('--')) {
      throw new PlannerError(`Missing value for ${key}`);
    }
    args[key.slice(2)] = value;
    i += 1;
  }
  if (!args.events) throw new PlannerError('Missing --events');
  if (!args['as-of']) throw new PlannerError('Missing --as-of');
  if (!args.out) throw new PlannerError('Missing --out');
  return { eventsPath: args.events, asOf: args['as-of'], outPath: args.out };
}

module.exports = { parseArgs };
