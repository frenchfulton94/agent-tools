// tests/workflows-minimal-flows.test.ts
import { describe, expect, test } from 'bun:test';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

/**
 * The minimal level is pinned to one release of mattpocock-skills. The two lists are the
 * upstream plugin manifest's skills split by each SKILL.md's `disable-model-invocation`, at
 * the version below. Re-checking the level against a new release means updating this
 * object and every schema's "Written against" stamp together.
 */
const ROSTER = {
	version: '1.3.1',
	modelInvoked: [
		'tdd', 'diagnosing-bugs', 'domain-modeling', 'codebase-design', 'code-review', 'prototype',
		'research', 'pr', 'wizard', 'grilling', 'writing-for-agents',
	],
	userInvoked: [
		'ask-matt', 'grill-with-docs', 'grill-me', 'implement', 'implement-spec',
		'improve-codebase-architecture', 'retro', 'setup-matt-pocock-skills', 'to-spec', 'to-tickets',
		'triage', 'wayfinder', 'handoff', 'to-questionnaire', 'teach', 'wait-what',
	],
};

/** Harness built-ins a flow may offer the human; every other command is a Pocock skill, OpenSpec, or impeccable. */
const HARNESS_COMMANDS = new Set(['clear', 'compact', 'model', 'effort']);
/** Names upstream renamed or this level retired. Their presence means an instruction rotted. */
const RETIRED_TERMS = ['CONTEXT.md', 'CONTEXT-MAP.md', 'to-prd', 'to-issues', '/diagnose', 'mattpocock-bridge'];

const LEVELS = join(import.meta.dir, '..', 'plugins', 'workflows', 'payload', 'levels');
const MINIMAL = join(LEVELS, 'minimal');
const SCHEMAS = join(MINIMAL, 'openspec', 'schemas');
const AGENTS = join(MINIMAL, 'agents');

const subdirs = (d: string): string[] =>
	existsSync(d) ? readdirSync(d).filter((n) => statSync(join(d, n)).isDirectory()).sort() : [];
const filesUnder = (d: string): string[] =>
	readdirSync(d).flatMap((n) => {
		const p = join(d, n);
		return statSync(p).isDirectory() ? filesUnder(p) : [p];
	});

interface Artifact {
	id: string;
	generates: string;
	template: string;
	instruction: string;
	requires?: string[];
}
interface Schema {
	name: string;
	version: number;
	description: string;
	artifacts: Artifact[];
	apply: { requires: string[]; tracks: string; instruction: string };
}

const readSchema = (name: string): Schema =>
	Bun.YAML.parse(readFileSync(join(SCHEMAS, name, 'schema.yaml'), 'utf8')) as Schema;
const textOf = (paths: string[]): string => paths.map((p) => readFileSync(p, 'utf8')).join('\n');
const schemaText = (name: string): string => textOf(filesUnder(join(SCHEMAS, name)));

/** Every skill a text calls, read from the one phrasing minimal schemas may use. */
function skillCalls(text: string): string[] {
	const flat = text.replace(/\s+/g, ' ');
	const calls: string[] = [];
	for (const m of flat.matchAll(/[Cc]all the Skill tool (?:with|twice, for|three times, for) ((?:"[a-z0-9-]+"(?:,? (?:and )?)?)+)/g)) {
		for (const n of m[1].matchAll(/"([a-z0-9-]+)"/g)) calls.push(n[1]);
	}
	return calls;
}

/**
 * Every slash command a text offers. The lookbehind rejects path separators (`docs/adr`,
 * `<change>/research`, `https://`) so only a command a person would type is returned.
 */
function slashCommands(text: string): string[] {
	return [...text.matchAll(/(?<![\w/.:<>\]-])\/([a-z][a-z0-9-]*(?::[a-z0-9-]+)?)/g)].map((m) => m[1]);
}

function isAllowedCommand(cmd: string): boolean {
	const bare = cmd.replace(/^mattpocock-skills:/, '');
	return (
		ROSTER.userInvoked.includes(bare) || cmd.startsWith('opsx:') || HARNESS_COMMANDS.has(cmd) || cmd === 'impeccable'
	);
}

const flows = subdirs(SCHEMAS).filter((n) => n.endsWith('-flow'));

describe('the scanners themselves', () => {
	test('skillCalls reads one and two-skill calls, across line breaks', () => {
		expect(skillCalls('Call the Skill tool twice, for "grilling" and\n      "domain-modeling". Then call the Skill tool with "tdd".')).toEqual([
			'grilling',
			'domain-modeling',
			'tdd',
		]);
	});

	test('slashCommands finds commands and ignores paths and URLs', () => {
		expect(
			slashCommands('Offer `/retro`, then /opsx:apply <change>. Not docs/adr/, <change>/research/, or https://x.dev/a.'),
		).toEqual(['retro', 'opsx:apply']);
	});
});

describe('minimal schema and agent names stay disjoint from the other levels', () => {
	test('no name a minimal schema or agent uses is shipped by standard or advanced', () => {
		const others = new Set<string>();
		for (const level of ['standard', 'advanced', join('advanced', 'apple')]) {
			for (const s of subdirs(join(LEVELS, level, 'openspec', 'schemas'))) others.add(s);
			const agents = join(LEVELS, level, 'agents');
			if (existsSync(agents)) for (const a of readdirSync(agents)) others.add(a);
		}
		const mine = [...subdirs(SCHEMAS), ...(existsSync(AGENTS) ? readdirSync(AGENTS) : [])];
		expect(mine.filter((n) => others.has(n))).toEqual([]);
	});
});

test('bugfix-flow keeps its name and its diagnose artifact, so in-flight changes resolve', () => {
	expect(flows).toContain('bugfix-flow');
	expect(readSchema('bugfix-flow').artifacts[0].id).toBe('diagnose');
});

describe.each(flows)('%s', (name) => {
	const schema = readSchema(name);
	const ids = schema.artifacts.map((a) => a.id);

	test('name matches its directory', () => {
		expect(schema.name).toBe(name);
	});

	test('description stamps the roster version', () => {
		expect(schema.description).toContain(`Written against mattpocock-skills ${ROSTER.version}.`);
	});

	test('artifact ids are unique', () => {
		expect(new Set(ids).size).toBe(ids.length);
	});

	test('each artifact requires only artifacts declared before it, so the graph is acyclic', () => {
		const seen = new Set<string>();
		for (const a of schema.artifacts) {
			expect((a.requires ?? []).filter((r) => !seen.has(r))).toEqual([]);
			seen.add(a.id);
		}
	});

	test('every referenced template exists', () => {
		const missing = schema.artifacts.filter((a) => !existsSync(join(SCHEMAS, name, 'templates', a.template)));
		expect(missing.map((a) => a.template)).toEqual([]);
	});

	test('apply requires declared artifacts and tracks a generated file', () => {
		expect(schema.apply.requires.filter((r) => !ids.includes(r))).toEqual([]);
		expect(schema.artifacts.map((a) => a.generates)).toContain(schema.apply.tracks);
	});

	test('a specs artifact, when present, generates under specs/', () => {
		const specs = schema.artifacts.find((a) => a.id === 'specs');
		if (specs) expect(specs.generates).toBe('specs/**/*.md');
	});

	test('every checkbox in a template uses the exact "- [ ] " form', () => {
		const bad: string[] = [];
		for (const p of filesUnder(join(SCHEMAS, name, 'templates'))) {
			for (const line of readFileSync(p, 'utf8').split('\n')) {
				if (/^\s*[-*]\s*\[/.test(line) && !/^- \[ \] /.test(line)) bad.push(`${relative(SCHEMAS, p)}: ${line}`);
			}
		}
		expect(bad).toEqual([]);
	});

	test('calls only model-invoked Pocock skills, in the canonical phrasing', () => {
		const text = schemaText(name);
		expect(skillCalls(text).filter((s) => !ROSTER.modelInvoked.includes(s))).toEqual([]);
		expect(text.match(/\binvoke\b/gi) ?? []).toEqual([]);
		expect(text.match(/Skill tool with "impeccable"/g) ?? []).toEqual([]);
	});

	test('offers only Pocock user-invoked commands, OpenSpec, harness built-ins, or impeccable', () => {
		expect(slashCommands(schemaText(name)).filter((c) => !isAllowedCommand(c))).toEqual([]);
	});

	test('names no retired term', () => {
		const text = schemaText(name);
		expect(RETIRED_TERMS.filter((t) => text.includes(t))).toEqual([]);
	});
});
