/**
 * rust-check-gate.test.ts — pins the rust plugin's Stop gate.
 *
 * The gate keeps a session from ending while `cargo check` fails after Rust edits. It runs
 * the real script, against real fixture crates and the real cargo, and pins: what `track`
 * records, that a located compile error blocks and quotes the error, that warnings and
 * clean builds pass, that the block count is capped so a crate broken before the session
 * cannot hold it forever, and that every environment failure — no cargo, a file outside
 * any crate — fails open. RUST_CHECK_GATE_DEBUG=1 prints internal errors, and every case
 * asserts stderr is empty, so a fail-open internal error cannot pass as "allow".
 *
 * Skips cleanly when perl or cargo is unavailable.
 */

import { afterAll, beforeAll, describe, expect, test } from 'bun:test';
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const GATE = join(import.meta.dir, '../plugins/rust/scripts/rust-check-gate.pl');
const hasPerl = spawnSync('perl', ['-v']).status === 0;
const hasCargo = spawnSync('cargo', ['--version']).status === 0;

let ROOT = '';
let DATA = '';
let TARGET = '';
let SESSION_N = 0;

const GOOD = 'pub fn add(a: i32, b: i32) -> i32 {\n    a + b\n}\n';
const WARN = 'pub fn add(a: i32, b: i32) -> i32 {\n    let unused = 1;\n    a + b\n}\n';
const BAD = 'pub fn add(a: i32, b: i32) -> i32 {\n    let s: i32 = "x";\n    a + b + s\n}\n';

function crate(dir: string, name: string, lib: string): string {
	mkdirSync(join(dir, 'src'), { recursive: true });
	writeFileSync(
		join(dir, 'Cargo.toml'),
		`[package]\nname = "${name}"\nversion = "0.1.0"\nedition = "2024"\n`,
	);
	writeFileSync(join(dir, 'src/lib.rs'), lib);
	return dir;
}

beforeAll(() => {
	ROOT = realpathSync(mkdtempSync(join(tmpdir(), 'rust-gate-')));
	DATA = join(ROOT, 'plugin-data');
	TARGET = join(ROOT, 'target-shared'); // one target dir keeps the suite fast
});

afterAll(() => {
	if (ROOT) rmSync(ROOT, { recursive: true, force: true });
});

function env(extra: Record<string, string> = {}) {
	return {
		PATH: process.env.PATH ?? '',
		HOME: process.env.HOME ?? ROOT,
		CLAUDE_PLUGIN_DATA: DATA,
		CARGO_TARGET_DIR: TARGET,
		RUST_CHECK_GATE_DEBUG: '1',
		...extra,
	};
}

function run(mode: 'track' | 'stop', payload: unknown, extra: Record<string, string> = {}) {
	const r = spawnSync('/usr/bin/perl', [GATE, mode], {
		input: typeof payload === 'string' ? payload : JSON.stringify(payload),
		encoding: 'utf8',
		env: env(extra),
		timeout: 120_000,
	});
	expect(r.stderr).toBe('');
	expect(r.status).toBe(0);
	const out = r.stdout.trim();
	return out ? JSON.parse(out) : null;
}

function session() {
	return `s${++SESSION_N}`;
}

function edit(s: string, file: string, cwd = ROOT, tool = 'Edit') {
	return run('track', { session_id: s, tool_name: tool, tool_input: { file_path: file }, cwd });
}

function stop(s: string, active = false, extra: Record<string, string> = {}) {
	return run('stop', { session_id: s, cwd: ROOT, stop_hook_active: active }, extra);
}

const marker = (s: string) => join(DATA, 'rust-check-gate', `${s}.edited`);

describe.skipIf(!hasPerl || !hasCargo)('rust-check-gate', () => {
	describe('track', () => {
		test('records .rs and Cargo.toml edits, one per line', () => {
			const s = session();
			edit(s, '/p/src/lib.rs');
			edit(s, '/p/Cargo.toml', ROOT, 'Write');
			edit(s, '/p/build.rs', ROOT, 'MultiEdit');
			expect(readFileSync(marker(s), 'utf8')).toBe('/p/src/lib.rs\n/p/Cargo.toml\n/p/build.rs\n');
		});
		test('ignores other files, build output, and dependency sources', () => {
			const s = session();
			for (const f of ['/p/README.md', '/p/Cargo.lock', '/p/target/debug/build/x/out/gen.rs', `${process.env.HOME}/.cargo/registry/src/x/lib.rs`]) {
				edit(s, f);
			}
			expect(existsSync(marker(s))).toBe(false);
		});
		test('stays silent on a malformed payload', () => {
			expect(run('track', 'not json')).toBeNull();
			expect(run('track', '{}')).toBeNull();
		});
	});

	describe('stop', () => {
		test('does nothing when the session edited no Rust', () => {
			expect(stop(session())).toBeNull();
		});

		test('blocks on a compile error and quotes it with file and line', () => {
			const dir = crate(join(ROOT, 'bad'), 'bad_crate', BAD);
			const s = session();
			edit(s, join(dir, 'src/lib.rs'));
			const out = stop(s);
			expect(out.decision).toBe('block');
			expect(out.reason).toContain('[rust check gate]');
			expect(out.reason).toMatch(/src\/lib\.rs:2:\d+: error\[E0308\]/);
			expect(existsSync(marker(s))).toBe(true); // re-checked at the next stop
		});

		test('passes once the error is fixed, and forgets the session', () => {
			const dir = crate(join(ROOT, 'fixed'), 'fixed_crate', BAD);
			const s = session();
			edit(s, join(dir, 'src/lib.rs'));
			expect(stop(s).decision).toBe('block');
			writeFileSync(join(dir, 'src/lib.rs'), GOOD);
			expect(stop(s, true)).toBeNull();
			expect(existsSync(marker(s))).toBe(false);
		});

		test('warnings never block', () => {
			const dir = crate(join(ROOT, 'warn'), 'warn_crate', WARN);
			const s = session();
			edit(s, join(dir, 'src/lib.rs'));
			expect(stop(s)).toBeNull();
		});

		test('a relative path resolves against the payload cwd', () => {
			crate(join(ROOT, 'rel'), 'rel_crate', BAD);
			const s = session();
			edit(s, 'rel/src/lib.rs', ROOT);
			expect(stop(s).decision).toBe('block');
		});

		test('stops blocking after two attempts and says so', () => {
			const dir = crate(join(ROOT, 'stuck'), 'stuck_crate', BAD);
			const s = session();
			edit(s, join(dir, 'src/lib.rs'));
			expect(stop(s).reason).toContain('it will block at most 1 more time.');
			expect(stop(s, true).reason).toContain('the next stop is allowed even if the build still fails');
			const third = stop(s, true);
			expect(third.decision).toBeUndefined();
			expect(third.systemMessage).toContain('still fails after 2 attempts');
			expect(existsSync(marker(s))).toBe(false);
		});

		test('checks the whole workspace from an edit in one member', () => {
			const ws = join(ROOT, 'ws');
			mkdirSync(ws, { recursive: true });
			writeFileSync(join(ws, 'Cargo.toml'), '[workspace]\nresolver = "3"\nmembers = ["a", "b"]\n');
			crate(join(ws, 'a'), 'ws_a', GOOD);
			crate(join(ws, 'b'), 'ws_b', BAD);
			const s = session();
			edit(s, join(ws, 'a/src/lib.rs'));
			const out = stop(s);
			expect(out.decision).toBe('block');
			expect(out.reason).toContain(join(ws, 'Cargo.toml'));
		});

		test('a file outside any crate passes and is forgotten', () => {
			const loose = join(ROOT, 'loose');
			mkdirSync(loose, { recursive: true });
			writeFileSync(join(loose, 'scratch.rs'), 'fn main( {}');
			const s = session();
			edit(s, join(loose, 'scratch.rs'));
			expect(stop(s)).toBeNull();
			expect(existsSync(marker(s))).toBe(false);
		});

		test('fails open with a notice when cargo is not on PATH', () => {
			const dir = crate(join(ROOT, 'nocargo'), 'nocargo_crate', BAD);
			const s = session();
			edit(s, join(dir, 'src/lib.rs'));
			const out = stop(s, false, { PATH: '/usr/bin:/bin' });
			// Without cargo the workspace cannot be located either, so the manifest itself is checked.
			expect(out.decision).toBeUndefined();
			expect(out.systemMessage).toContain('Could not check the Rust build');
		});

		test('RUST_CHECK_GATE=0 turns it off', () => {
			const dir = crate(join(ROOT, 'off'), 'off_crate', BAD);
			const s = session();
			edit(s, join(dir, 'src/lib.rs'));
			expect(stop(s, false, { RUST_CHECK_GATE: '0' })).toBeNull();
		});

		test('stays silent on a malformed payload', () => {
			expect(run('stop', 'not json')).toBeNull();
		});
	});
});
