#!/usr/bin/env node
// Keeps package.json's engines.node floor truthful: it must not be lower
// than the strictest Node minimum required by the locked dependency tree
// (the max of semver.minVersion() over every engines.node entry in
// package-lock.json).
//
// Usage:
//   node scripts/check-node-engines.mjs          # check: exit 1 if the floor is stale
//   node scripts/check-node-engines.mjs --fix    # fix: rewrite engines.node to the tree floor

import { compare, gt, minVersion } from 'semver';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const pkgPath = join(root, 'package.json');
const lockPath = join(root, 'package-lock.json');

const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
const lock = JSON.parse(readFileSync(lockPath, 'utf8'));

// [minVersion, [packages]] for every locked package declaring engines.node,
// sorted by minimum, strictest last.
const minimums = new Map();
for (const [name, meta] of Object.entries(lock.packages)) {
  const range = meta?.engines?.node;
  if (!range) continue;
  const min = minVersion(range).version;
  if (!minimums.has(min)) minimums.set(min, []);
  minimums.get(min).push({ name: name || '(root)', range });
}
let treeFloor = '0.0.0';
for (const min of minimums.keys()) {
  if (gt(min, treeFloor)) treeFloor = min;
}

const declared = pkg.engines?.node;
if (!declared) {
  console.error('package.json declares no engines.node');
  process.exit(1);
}
const declaredMin = minVersion(declared).version;

if (gt(treeFloor, declaredMin)) {
  const offenders = [];
  for (const [min, pkgs] of minimums) {
    if (gt(min, declaredMin)) offenders.push(...pkgs.map((p) => ({ ...p, min })));
  }
  offenders.sort((a, b) => compare(b.min, a.min));
  console.error(
    `engines.node "${declared}" (minimum ${declaredMin}) is below the ` +
      `dependency tree's strictest minimum ${treeFloor}:`,
  );
  for (const { name, range, min } of offenders) {
    console.error(`  ${name} requires engines.node ${range} (minimum ${min})`);
  }
  if (!process.argv.includes('--fix')) {
    console.error('Run with --fix to rewrite engines.node to >=' + treeFloor);
    process.exit(1);
  }
  pkg.engines.node = `>=${treeFloor}`;
  writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n');
  console.log(`bumped engines.node: ${declared} -> >=${treeFloor}`);
} else {
  console.log(
    `ok: engines.node ${declared} (minimum ${declaredMin}) meets the tree minimum ${treeFloor}`,
  );
}
