#!/usr/bin/env node
const { parseArgs } = require('../src/cliArgs');
const { run } = require('../src/index');

async function main() {
  const args = parseArgs(process.argv.slice(2));
  await run(args);
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
