/**
 * rust-guard.test.ts — pins the rust plugin's PreToolUse registry guard.
 *
 * `cargo publish` has no confirmation step: the upload happens when the command runs,
 * and a published version can never be overwritten or deleted. So this suite runs the
 * real script and pins, per command, the decision and that no internal error occurred.
 * The guard fails open by design, so an internal error would otherwise pass every
 * "allow" case silently; RUST_GUARD_DEBUG=1 makes it print the error, and every case
 * asserts stderr is empty.
 *
 * The allow cases are as load-bearing as the ask cases. A guard that fires on
 * `cargo publish --dry-run`, on `grep "cargo publish"`, or on `cargo owner --list`
 * gets switched off, and then it protects nothing.
 *
 * The alias cases run against a fixture project whose `.cargo/config.toml` defines
 * aliases, and a fixture CARGO_HOME, because cargo resolves aliases from both (and
 * from CARGO_ALIAS_<NAME>) before it picks a subcommand — measured on cargo 1.97.1.
 */

import { afterAll, beforeAll, describe, expect, test } from 'bun:test';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const GUARD = join(import.meta.dir, '../plugins/rust/scripts/cargo-registry-guard.pl');
const hasPerl = spawnSync('perl', ['-v'], { encoding: 'utf8' }).status === 0;

let ROOT = '';
let PROJECT = '';
let NESTED = '';
let CARGO_HOME = '';

beforeAll(() => {
	ROOT = realpathSync(mkdtempSync(join(tmpdir(), 'rust-guard-')));
	PROJECT = join(ROOT, 'project');
	NESTED = join(PROJECT, 'crates/core');
	CARGO_HOME = join(ROOT, 'cargo-home');
	mkdirSync(join(PROJECT, '.cargo'), { recursive: true });
	mkdirSync(NESTED, { recursive: true });
	mkdirSync(CARGO_HOME, { recursive: true });
	writeFileSync(
		join(PROJECT, '.cargo/config.toml'),
		[
			'[build]',
			'jobs = 4',
			'',
			'[alias]',
			'rel = "publish --registry internal"',
			'ship = ["publish", "--workspace"]',
			'check-pub = "publish --dry-run"',
			'xt = "run --package xtask --"',
			'build = "publish"   # shadows a built-in, so cargo ignores it',
			'',
		].join('\n'),
	);
	writeFileSync(join(CARGO_HOME, 'config.toml'), '[alias]\nhome-pub = "publish"\n');
});

afterAll(() => {
	if (ROOT) rmSync(ROOT, { recursive: true, force: true });
});

type Decision = 'ask' | 'allow';

function run(command: string, cwd = ROOT, env: Record<string, string> = {}) {
	const payload = JSON.stringify({ tool_name: 'Bash', tool_input: { command }, cwd });
	const r = spawnSync('perl', [GUARD], {
		input: payload,
		encoding: 'utf8',
		env: { PATH: process.env.PATH ?? '', HOME: ROOT, CARGO_HOME, RUST_GUARD_DEBUG: '1', ...env },
	});
	const out = r.stdout.trim();
	const decision: Decision = out ? JSON.parse(out).hookSpecificOutput.permissionDecision : 'allow';
	return { decision, status: r.status, stderr: r.stderr, out };
}

function expectDecision(command: string, want: Decision, cwd?: string, env?: Record<string, string>) {
	const r = run(command, cwd, env);
	expect(r.stderr).toBe('');
	expect(r.status).toBe(0);
	expect(r.decision).toBe(want);
	return r;
}

const ASK: string[] = [
	'cargo publish',
	'cargo publish --allow-dirty',
	'cargo publish -p my-crate',
	'cargo publish --workspace',
	'cargo publish --registry internal',
	'cargo publish --no-verify',
	'cargo publish -Fnetwork', // -F takes a value; the n is not --dry-run
	'cargo +nightly publish',
	'cargo +1.97 --locked --config net.retry=5 publish',
	'cargo -Z unstable-options publish',
	'cargo --color always publish',
	'cargo -v publish',
	'/usr/local/bin/cargo publish',
	'~/.cargo/bin/cargo publish',
	'cargo.exe publish',
	'cargo-publish',
	'CARGO_REGISTRY_TOKEN=x cargo publish',
	'sudo -E cargo publish',
	'env RUSTFLAGS= cargo publish',
	'time cargo publish',
	'cargo test && cargo publish',
	'cargo build; cargo publish',
	'cargo publish --dry-run && cargo publish',
	'git tag v1.0.0 && git push --tags && cargo publish',
	'cargo publish || true',
	'cargo publish 2>&1 | tee publish.log',
	'(cd crates/core && cargo publish)',
	'bash -c "cargo publish"',
	"sh -c 'cargo publish --workspace'",
	'eval cargo publish',
	'echo $(cargo publish)',
	'echo `cargo publish`',
	'cargo publish \\\n  --allow-dirty',
	'for c in a b; do cargo publish -p $c; done',
	'cargo yank --version 1.0.0 my-crate',
	'cargo yank my-crate@1.0.0',
	'cargo yank --version 1.0.0 --undo my-crate',
	'cargo owner --add github:org:team my-crate',
	'cargo owner -a someone my-crate',
	'cargo owner --remove someone my-crate',
	'cargo owner -r someone my-crate',
	'cargo owner --add=someone my-crate',
	'CARGO_ALIAS_SHIP=publish cargo ship',
	'cargo-yank --version 1.0.0 my-crate',
];

const ALLOW: string[] = [
	'cargo publish --dry-run',
	'cargo publish -n',
	'cargo publish -qn',
	'cargo publish -vn --allow-dirty',
	'cargo publish --dry-run --workspace',
	'cargo publish --help',
	'cargo publish -h',
	'cargo help publish',
	'cargo package',
	'cargo package --list',
	'cargo build --release',
	'cargo test --workspace',
	'cargo owner --list my-crate',
	'cargo owner -l my-crate',
	'cargo yank --help',
	'cargo search serde',
	'cargo login --help',
	'echo "cargo publish"',
	"echo 'run cargo publish when ready'",
	'grep -rn "cargo publish" docs/',
	'rg "cargo yank" .',
	'git commit -m "prepare for cargo publish"',
	'cat RELEASING.md # explains cargo publish',
	'cargo xt dist', // a project alias for `run`
	'cargo release patch', // a third-party subcommand: out of scope, documented
	'cargo $SUB', // unevaluated variable: documented limit
	'ls ~/.cargo/registry',
	'',
];

describe.skipIf(!hasPerl)('cargo-registry-guard', () => {
	describe('asks before a registry change', () => {
		for (const command of ASK) {
			test(JSON.stringify(command), () => {
				const r = expectDecision(command, 'ask');
				expect(r.out).toContain('[rust]');
			});
		}
	});

	describe('allows everything else', () => {
		for (const command of ALLOW) {
			test(JSON.stringify(command), () => expectDecision(command, 'allow'));
		}
	});

	describe('aliases', () => {
		test('a project alias for publish asks', () => {
			expectDecision('cargo rel', 'ask', PROJECT);
		});
		test('an array alias for publish asks, and names the workspace', () => {
			const r = expectDecision('cargo ship', 'ask', PROJECT);
			expect(r.out).toContain('every publishable package in the workspace');
		});
		test('a project alias is found from a nested directory', () => {
			expectDecision('cargo rel', 'ask', NESTED);
		});
		test('cd into the project before the alias is followed', () => {
			expectDecision(`cd ${PROJECT} && cargo rel`, 'ask', ROOT);
		});
		test('an alias carrying --dry-run is allowed', () => {
			expectDecision('cargo check-pub', 'allow', PROJECT);
		});
		test('an alias shadowing a built-in is ignored, as cargo ignores it', () => {
			expectDecision('cargo build', 'allow', PROJECT);
		});
		test('the same alias outside the project resolves to nothing', () => {
			expectDecision('cargo rel', 'allow', ROOT);
		});
		test('an alias in CARGO_HOME applies everywhere', () => {
			expectDecision('cargo home-pub', 'ask', ROOT);
		});
		test('an alias in the process environment applies', () => {
			expectDecision('cargo envpub', 'ask', ROOT, { CARGO_ALIAS_ENVPUB: 'publish' });
		});
	});

	describe('the reason names the target registry', () => {
		test('default registry', () => {
			expect(run('cargo publish').out).toContain('crates.io');
		});
		test('--registry', () => {
			expect(run('cargo publish --registry internal').out).toContain('`internal` registry');
		});
		test('an alias carrying --registry', () => {
			expect(run('cargo rel', PROJECT).out).toContain('`internal` registry');
		});
	});

	describe('fails open on malformed input', () => {
		for (const input of ['', 'not json', '{"tool_name":"Bash"}', '{"tool_name":"Edit","tool_input":{}}']) {
			test(JSON.stringify(input), () => {
				const r = spawnSync('perl', [GUARD], { input, encoding: 'utf8', env: { RUST_GUARD_DEBUG: '1' } });
				expect(r.status).toBe(0);
				expect(r.stdout).toBe('');
				expect(r.stderr).toBe('');
			});
		}
	});
});
