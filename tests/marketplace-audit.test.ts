/**
 * marketplace-audit.test.ts — gate on the sweep's catalog findings.
 *
 * The sweep does two jobs, and they carry different authority. Its own catalog checks — plugin
 * READMEs, the README's skills column, the marketplace-level schema — are this repository's rules,
 * so a finding there fails the build. The findings it collects by delegating to the four vendored
 * validators are advisory: they are Tier 0 lints over prose, and what they surface — body length,
 * a reference file with no table of contents, an asset nested two levels down — is a judgement
 * call an author may have made deliberately. Gating on those turns every such call into a build
 * failure someone has to argue with.
 *
 * Note that `validate_skill.ts` run directly against a plugin-shipped skill reports missing
 * `scripts/…` files that do exist at the plugin root. The sweep already suppresses that case, so
 * these findings are advisory for the judgement reason above, not because the tool is wrong.
 *
 * The delegated findings are still printed, so a real one is visible rather than swallowed.
 */

import { expect, test } from 'bun:test';
import { join } from 'node:path';

const ROOT = join(import.meta.dir, '..');
const AUDIT = join(
	ROOT,
	'plugins/meta-skills/skills/maintaining-plugin-marketplaces/scripts/audit_marketplace.ts',
);

/** Validator filenames the sweep stamps onto findings it did not raise itself. */
const DELEGATED = new Set([
	'validate_skill.ts',
	'validate_plugin.ts',
	'validate_agent.ts',
	'validate_hooks.ts',
]);

type Finding = { message: string; severity: string; source: string };

test('the sweep reports no catalog-level errors or warnings', async () => {
	const proc = Bun.spawn(['bun', AUDIT, ROOT, '--strict', '--json'], {
		stdout: 'pipe',
		stderr: 'pipe',
	});
	const [stdout, stderr] = await Promise.all([
		new Response(proc.stdout).text(),
		new Response(proc.stderr).text(),
	]);
	await proc.exited;

	let findings: Finding[];
	try {
		findings = (JSON.parse(stdout) as { findings?: Finding[] }).findings ?? [];
	} catch {
		throw new Error(`audit_marketplace.ts did not emit JSON.\nstdout:\n${stdout}\nstderr:\n${stderr}`);
	}

	const delegated = findings.filter((f) => DELEGATED.has(f.source));
	const catalog = findings.filter((f) => !DELEGATED.has(f.source) && f.severity !== 'note');

	if (delegated.length > 0) {
		console.log(
			`\n${delegated.length} advisory finding(s) from the vendored validators:\n` +
				delegated.map((f) => `  ${f.severity} ${f.source}: ${f.message}`).join('\n'),
		);
	}

	expect(catalog.map((f) => `${f.severity}: ${f.message}`)).toEqual([]);
});
