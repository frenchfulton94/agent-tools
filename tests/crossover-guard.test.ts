/**
 * crossover-guard.test.ts — pins the crossover plugin's PreToolUse guard.
 *
 * The guard is the only thing standing between a non-interactive `rm -rf` or
 * `cxbottle --delete` and a bottle's installed applications, licences, and saves:
 * cxbottle's own confirmation does not appear without a terminal (measured on
 * CrossOver 25.1.1 — the bottle is deleted, exit 0). So this suite runs the real
 * script against a fixture home folder and pins three things per command: the
 * decision, a clean exit, and no internal error. The guard fails open by design, so
 * an internal error would otherwise pass every "allow" case silently;
 * CROSSOVER_GUARD_DEBUG=1 makes it print the error, and every case asserts stderr
 * is empty.
 *
 * The allow cases are as load-bearing as the deny cases. A guard that fires on
 * `echo "rm -rf …"`, on removing a symlink, or on `find ~ -name .DS_Store -delete`
 * gets switched off, and then it protects nothing.
 *
 * Skips cleanly when perl is unavailable. The plist case runs on macOS only, since
 * it needs plutil to write a binary plist the way `defaults write` does.
 */

import { afterAll, beforeAll, describe, expect, test } from 'bun:test';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, realpathSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const GUARD = join(import.meta.dir, '../plugins/crossover/scripts/crossover-guard.pl');
const hasPerl = spawnSync('perl', ['-v'], { encoding: 'utf8' }).status === 0;
const hasPlutil = process.platform === 'darwin' && spawnSync('/usr/bin/plutil', ['-help']).status !== null;

let HOME = '';
let EMPTY_HOME = '';
let ROOT = '';
const SUPPORT = 'Library/Application Support/CrossOver';

function bottle(root: string, name: string): string {
	const b = join(root, name);
	mkdirSync(join(b, 'drive_c/Program Files/Game'), { recursive: true });
	mkdirSync(join(b, 'drive_c/users/crossover/Saves'), { recursive: true });
	mkdirSync(join(b, 'dosdevices'), { recursive: true });
	writeFileSync(join(b, 'cxbottle.conf'), '[Bottle]\n"Template" = "win10_64"\n');
	writeFileSync(join(b, 'system.reg'), 'WINE REGISTRY Version 2\n');
	writeFileSync(join(b, 'user.reg'), 'WINE REGISTRY Version 2\n');
	writeFileSync(join(b, 'drive_c/Program Files/Game/game.exe'), '');
	writeFileSync(join(b, 'drive_c/users/crossover/Saves/slot1.sav'), '');
	return b;
}

beforeAll(() => {
	// realpath: macOS tmpdir is /var/... -> /private/var/..., and the guard compares both.
	HOME = realpathSync(mkdtempSync(join(tmpdir(), 'cxguard-home-')));
	EMPTY_HOME = realpathSync(mkdtempSync(join(tmpdir(), 'cxguard-empty-')));
	ROOT = join(HOME, SUPPORT, 'Bottles');
	bottle(ROOT, 'Steam');
	bottle(ROOT, 'Office 2016');
	mkdirSync(join(ROOT, 'notabottle/drive_c'), { recursive: true });
	mkdirSync(join(EMPTY_HOME, SUPPORT, 'Bottles'), { recursive: true });

	// A second root named by CX_BOTTLE_PATH in a (renamed) app bundle's CrossOver.conf.
	const etc = join(HOME, 'Applications/CrossOver8.app/Contents/SharedSupport/CrossOver/etc');
	mkdirSync(etc, { recursive: true });
	writeFileSync(
		join(etc, 'CrossOver.conf'),
		[
			';; "CX_BOTTLE_PATH" = "/commented/out"',
			'[BottleDefaults]',
			'[EnvironmentVariables]',
			'"CX_BOTTLE_PATH"="${HOME}/AltBottles"',
			'',
		].join('\n'),
	);
	bottle(join(HOME, 'AltBottles'), 'Alt');

	// A third root named only by the environment.
	bottle(join(HOME, 'EnvBottles'), 'Envy');

	// A fourth named by BottleDir in the preferences plist, written binary as `defaults` does.
	bottle(join(HOME, 'PlistBottles'), 'Plisty');
	if (hasPlutil) {
		const prefs = join(HOME, 'Library/Preferences');
		mkdirSync(prefs, { recursive: true });
		const plist = join(prefs, 'com.codeweavers.CrossOver.plist');
		writeFileSync(
			plist,
			`<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>BottleDir</key><string>${join(HOME, 'PlistBottles')}</string>
<key>SUEnableAutomaticChecks</key><true/>
</dict></plist>`,
		);
		spawnSync('/usr/bin/plutil', ['-convert', 'binary1', plist]);
	}

	symlinkSync(join(ROOT, 'Steam'), join(HOME, 'steam-link'));
});

afterAll(() => {
	if (HOME) rmSync(HOME, { recursive: true, force: true });
	if (EMPTY_HOME) rmSync(EMPTY_HOME, { recursive: true, force: true });
});

type Decision = 'allow' | 'ask' | 'deny';

function run(command: string, opts: { cwd?: string; home?: string; env?: Record<string, string>; raw?: string } = {}) {
	const payload =
		opts.raw ?? JSON.stringify({ tool_name: 'Bash', tool_input: { command }, cwd: opts.cwd ?? '/tmp' });
	const env: Record<string, string> = {
		PATH: process.env.PATH ?? '/usr/bin:/bin',
		HOME: opts.home ?? HOME,
		USER: process.env.USER ?? 'tester',
		CROSSOVER_GUARD_DEBUG: '1',
		...opts.env,
	};
	const r = spawnSync('perl', [GUARD], { input: payload, encoding: 'utf8', env });
	let decision: Decision = 'allow';
	let reason = '';
	if (r.stdout.trim()) {
		const out = JSON.parse(r.stdout);
		decision = out.hookSpecificOutput.permissionDecision;
		reason = out.hookSpecificOutput.permissionDecisionReason;
	}
	return { decision, reason, status: r.status, stderr: r.stderr };
}

function expectDecision(command: string, want: Decision, opts: Parameters<typeof run>[1] = {}) {
	const r = run(command, opts);
	expect(r.stderr).toBe('');
	expect(r.status).toBe(0);
	expect({ command, decision: r.decision }).toEqual({ command, decision: want });
	return r;
}

const B = () => `"$HOME/${SUPPORT}/Bottles"`;
const STEAM = () => `"$HOME/${SUPPORT}/Bottles/Steam"`;

describe.skipIf(!hasPerl)('crossover guard: deny raw deletion of a bottle', () => {
	const cases: [string, () => string, Parameters<typeof run>[1]?][] = [
		['quoted $HOME path', () => `rm -rf ${STEAM()}`],
		['backslash-escaped spaces and ~', () => `rm -rf ~/Library/Application\\ Support/CrossOver/Bottles/Steam`],
		['relative after cd', () => `cd ${B()} && rm -r Steam`],
		['relative to the payload cwd', () => 'rm -rf Steam', { cwd: '' }],
		['the C: drive', () => `rm -rf ${STEAM().slice(0, -1)}/drive_c"`],
		['a top-level C: drive folder', () => `rm -rf ${STEAM().slice(0, -1)}/drive_c/users"`],
		['a glob over the bottle folder', () => `rm -rf ${B()}/*`],
		['a glob over the C: drive', () => `cd ${STEAM()}/drive_c && rm -rf ./*`],
		['an ancestor of the bottle folder', () => `rm -rf ~/Library/Application\\ Support/CrossOver`],
		['the home folder', () => 'rm -rf ~'],
		['a registry file, non-recursive', () => `rm ${STEAM().slice(0, -1)}/system.reg"`],
		['cxbottle.conf via unlink', () => `unlink ${STEAM().slice(0, -1)}/cxbottle.conf"`],
		['sudo wrapper', () => `sudo -u root rm -rf ${STEAM()}`],
		['env and nice wrappers', () => `env -i nice -n 5 rm -rf ${STEAM()}`],
		['absolute rm path', () => `/bin/rm -rf ${STEAM()}`],
		['bash -c', () => `bash -c 'rm -rf ${STEAM()}'`],
		['eval of a single-quoted string', () => "eval 'rm -rf ~/Library/Application\\ Support/CrossOver/Bottles/Steam'"],
		['second statement', () => `echo cleaning && rm -rf ${STEAM()}`],
		['after a comment line', () => `# tidy up\nrm -rf ${STEAM()}`],
		['inside a one-line loop body', () => `for i in 1; do rm -rf ${STEAM()}; done`],
		['different case', () => `rm -rf "$HOME/library/application support/crossover/bottles/STEAM"`],
		['dot-dot collapsing back to the bottle', () => `rm -rf ${STEAM().slice(0, -1)}/drive_c/.."`],
		['bottle name with a space', () => `rm -rf "$HOME/${SUPPORT}/Bottles/Office 2016"`],
		['-- end of options', () => `rm -rf -- ${STEAM()}`],
		['-R and -fr spellings', () => `rm -fR ${STEAM()}`],
		['--recursive', () => `rm --recursive --force ${STEAM()}`],
		['symlink followed by a trailing slash', () => 'rm -rf ~/steam-link/'],
		['root from CX_BOTTLE_PATH in CrossOver.conf', () => 'rm -rf ~/AltBottles/Alt'],
		['root from the environment', () => 'rm -rf ~/EnvBottles/Envy', { env: { CX_BOTTLE_PATH: '' } }],
		['redirections do not hide the target', () => `rm -rf ${STEAM()} 2>/dev/null >&2`],
	];
	for (const [name, cmd, opts] of cases) {
		test(name, () => {
			const o = { ...opts };
			if (o.cwd === '') o.cwd = ROOT;
			if (o.env && 'CX_BOTTLE_PATH' in o.env) o.env = { CX_BOTTLE_PATH: join(HOME, 'EnvBottles') };
			const r = expectDecision(cmd(), 'deny', o);
			expect(r.reason).toStartWith('[crossover] ');
			expect(r.reason).toContain('--tar');
		});
	}

	test.skipIf(!hasPlutil)('root from BottleDir in a binary preferences plist', () => {
		expectDecision('rm -rf ~/PlistBottles/Plisty', 'deny');
	});

	test('deny outranks ask in the same command', () => {
		expectDecision(`cxbottle --bottle Steam --delete; rm -rf ${STEAM()}`, 'deny');
	});
});

describe.skipIf(!hasPerl)('crossover guard: ask before a delete a human should confirm', () => {
	const cases: [string, () => string][] = [
		['cxbottle --delete', () => 'cxbottle --bottle Steam --delete'],
		['full path and --force', () => '/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/cxbottle --bottle=Steam --delete --force'],
		['via a $CX variable', () => '"$CX/cxbottle" --bottle Steam --delete'],
		['bottle from an inline CX_BOTTLE', () => 'CX_BOTTLE=Steam cxbottle --delete'],
		['cxuninstall', () => 'cxuninstall --force'],
		['launching the Removal Tool', () => 'open ~/Downloads/CrossOver_RemovalTool.app'],
		['find -delete inside a bottle', () => `find ${STEAM()}/drive_c -name '*.tmp' -delete`],
		['find -exec rm inside a bottle', () => `find ${STEAM()} -name '*.log' -exec rm {} \\;`],
		['find from the bottle folder', () => `find ${B()} -name '*.log' -delete`],
		['rsync --delete into a bottle', () => `rsync -a --delete ./backup/ ${STEAM().slice(0, -1)}/drive_c/users/"`],
		['an unresolvable $WINEPREFIX', () => 'rm -rf "$WINEPREFIX"'],
		['command substitution', () => `rm -rf "$(ls -d ${B()}/S*)"`],
		['xargs supplies the targets', () => `ls -d ${B()}/* | xargs -I {} rm -rf {}`],
		['a loop variable', () => `for b in Steam; do rm -rf ${B().slice(0, -1)}/$b"; done`],
		['an unmatched quote', () => `rm -rf "${'$'}HOME/${SUPPORT}/Bottles/Steam`],
	];
	for (const [name, cmd] of cases) {
		test(name, () => {
			const r = expectDecision(cmd(), 'ask');
			expect(r.reason).toStartWith('[crossover] ');
		});
	}

	test('the cxbottle reason names the bottle and how to archive it', () => {
		const r = run('cxbottle --bottle "Office 2016" --delete');
		expect(r.decision).toBe('ask');
		expect(r.reason).toContain('"Office 2016"');
		expect(r.reason).toContain("cxbottle --bottle 'Office 2016' --tar ~/Office_2016.cxarchive");
	});
});

describe.skipIf(!hasPerl)('crossover guard: allow everything else', () => {
	const cases: [string, () => string, Parameters<typeof run>[1]?][] = [
		['listing bottles', () => `ls -la ${B()}`],
		['archiving a bottle', () => 'cxbottle --bottle Steam --tar ~/Steam.cxarchive'],
		['removing menus (recreated by --install)', () => 'cxbottle --bottle Steam --removeall'],
		['cxbottle help', () => 'cxbottle --help'],
		['cxuninstall help', () => 'cxuninstall --help'],
		['deleting one game folder inside Program Files', () => `rm -rf ${STEAM().slice(0, -1)}/drive_c/Program Files/Game"`],
		['deleting one save file', () => `rm ${STEAM().slice(0, -1)}/drive_c/users/crossover/Saves/slot1.sav"`],
		['an ordinary recursive delete', () => 'rm -rf node_modules dist', { cwd: '/tmp' }],
		['a directory without cxbottle.conf', () => `rm -rf ${B().slice(0, -1)}/notabottle"`],
		['removing a symlink to a bottle', () => 'rm -rf ~/steam-link'],
		['rm inside a grep pattern', () => `grep -rn "rm -rf ${'$'}HOME/${SUPPORT}/Bottles/Steam" .`],
		['rm inside an echo', () => `echo "rm -rf ${'$'}HOME/${SUPPORT}/Bottles/Steam"`],
		['filtered find from the home folder', () => 'find ~ -name .DS_Store -delete'],
		['find without a delete action', () => `find ${STEAM()} -name '*.log'`],
		['downloading and unzipping the Removal Tool', () => 'curl -LO https://example.invalid/CrossOver_RemovalTool.zip && unzip CrossOver_RemovalTool.zip'],
		['an unresolvable target on an unrelated command', () => 'rm -rf "$TMPDIR/build"'],
		['moving a bottle (reversible)', () => `mv ${STEAM()} ~/Desktop/`],
		['prefilter word in a commit message', () => 'git commit -m "find and fix the rsync bug"'],
		['redirect target is not an rm argument', () => 'rm -f /tmp/x.log 2>/dev/null'],
		['rsync without --delete', () => `rsync -a ./backup/ ${STEAM()}/`],
		['no bottles exist anywhere', () => `rm -rf "$HOME/${SUPPORT}"`, { home: 'EMPTY' }],
	];
	for (const [name, cmd, opts] of cases) {
		test(name, () => {
			const o = { ...opts };
			if (o.home === 'EMPTY') o.home = EMPTY_HOME;
			expectDecision(cmd(), 'allow', o);
		});
	}

	test('a non-Bash tool', () => {
		const raw = JSON.stringify({ tool_name: 'Write', tool_input: { file_path: '/x', content: 'rm -rf ~' } });
		expect(run('', { raw })).toMatchObject({ decision: 'allow', status: 0, stderr: '' });
	});

	test('a malformed payload fails open', () => {
		expect(run('', { raw: '{not json' })).toMatchObject({ decision: 'allow', status: 0, stderr: '' });
	});
});
