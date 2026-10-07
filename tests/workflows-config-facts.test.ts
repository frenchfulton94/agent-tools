import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
// @ts-expect-error untyped .mjs module
import { splitRetiredConfig } from '../plugins/workflows/scripts/config-facts.mjs';

const RETIRED = {
	rules: { design: ['Confirm the Seams table with the user before marking this artifact done.'] },
	guidance: { apply: ['On a UI slice, run the impeccable detector before review and fix what it reports.'] },
};

describe('splitRetiredConfig', () => {
	test('drops a rule the previous level shipped, matched after trimming, and keeps the rest', () => {
		const out = splitRetiredConfig(
			{ rules: { design: ['  Confirm the Seams table with the user before marking this artifact done. ', 'Prefer adapters.'] } },
			RETIRED,
		);
		expect(out.rules).toEqual({
			kept: { design: ['Prefer adapters.'] },
			dropped: { design: ['  Confirm the Seams table with the user before marking this artifact done. '] },
		});
	});

	test('keeps a rule that differs from the shipped text by one word', () => {
		const edited = 'Confirm the Seams table with the team before marking this artifact done.';
		expect(splitRetiredConfig({ rules: { design: [edited] } }, RETIRED).rules).toEqual({
			kept: { design: [edited] },
			dropped: {},
		});
	});

	test('keeps shipped text the user moved under another artifact id', () => {
		const moved = { tasks: ['Confirm the Seams table with the user before marking this artifact done.'] };
		expect(splitRetiredConfig({ rules: moved }, RETIRED).rules).toEqual({ kept: moved, dropped: {} });
	});

	test('an id whose every rule is dropped leaves kept, so nothing carries an empty list', () => {
		const out = splitRetiredConfig(
			{ rules: { design: ['Confirm the Seams table with the user before marking this artifact done.'] } },
			RETIRED,
		);
		expect(out.rules.kept).toEqual({});
	});

	test('drops operations guidance the previous level shipped, per operation', () => {
		const guidance = {
			apply: ['On a UI slice, run the impeccable detector before review and fix what it reports.', 'Run the e2e suite.'],
			archive: ['On a UI slice, run the impeccable detector before review and fix what it reports.'],
		};
		expect(splitRetiredConfig({ guidance }, RETIRED).guidance).toEqual({
			kept: {
				apply: ['Run the e2e suite.'],
				archive: ['On a UI slice, run the impeccable detector before review and fix what it reports.'],
			},
			dropped: { apply: ['On a UI slice, run the impeccable detector before review and fix what it reports.'] },
		});
	});

	test('a level with no retired config drops nothing', () => {
		const config = { rules: { design: ['x'] }, guidance: { apply: ['y'] } };
		for (const retired of [undefined, null, {}]) {
			expect(splitRetiredConfig(config, retired)).toEqual({
				rules: { kept: { design: ['x'] }, dropped: {} },
				guidance: { kept: { apply: ['y'] }, dropped: {} },
			});
		}
	});

	test("reads the minimal level's retired.json config in the shape it ships", () => {
		const retired = JSON.parse(
			readFileSync(join(import.meta.dir, '..', 'plugins', 'workflows', 'payload', 'levels', 'minimal', 'retired.json'), 'utf8'),
		);
		const out = splitRetiredConfig({ rules: retired.config.rules, guidance: retired.config.guidance }, retired.config);
		expect(out.rules.kept).toEqual({});
		expect(out.guidance.kept).toEqual({});
	});
});
