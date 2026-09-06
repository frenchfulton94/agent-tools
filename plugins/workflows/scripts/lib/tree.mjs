import { createHash } from 'node:crypto';
import { cpSync, existsSync, readdirSync, readFileSync, renameSync, rmSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

function filesUnder(dir, base = dir, acc = []) {
	for (const entry of readdirSync(dir)) {
		const p = join(dir, entry);
		if (statSync(p).isDirectory()) filesUnder(p, base, acc);
		else acc.push(relative(base, p));
	}
	return acc;
}

/**
 * Stable hash over relative paths and contents. Paths are sorted so directory read
 * order cannot change the result, and the path is hashed alongside the content so a
 * rename is detected even when every byte is identical.
 */
export function hashTree(dir) {
	if (!existsSync(dir)) return '';
	const h = createHash('sha256');
	// Sorted so a filesystem whose readdir order is not lexicographic cannot change the
	// hash of an unchanged tree. Not covered by a test: every platform available here
	// already returns sorted order, so a regression would be invisible to one.
	for (const rel of filesUnder(dir).sort()) {
		h.update(rel);
		h.update('\0');
		h.update(readFileSync(join(dir, rel)));
		h.update('\0');
	}
	return h.digest('hex');
}

/**
 * `hashTree` for a directory, a plain content hash for a file, `''` for neither.
 *
 * The ownership record (`scripts/record.mjs`) has to hash a schema — a directory — and a
 * subagent — a single `.md` file — with one function, because the question it answers is
 * the same for both: is what is on disk still byte-for-byte what this plugin put there,
 * or has the user edited it? A file and a directory hash into different namespaces here
 * (a file's hash omits the path framing `hashTree` applies), which is harmless: a name is
 * only ever compared against its own recorded hash, never across kinds.
 */
export function hashEntry(path) {
	if (!existsSync(path)) return '';
	try {
		if (statSync(path).isDirectory()) return hashTree(path);
		return createHash('sha256').update(readFileSync(path)).digest('hex');
	} catch {
		// Unreadable is not "unchanged": an empty hash can never equal a recorded one, so a
		// permission-restricted entry is treated as a collision rather than as ours to replace.
		return '';
	}
}

/**
 * Additive by default: an entry already present in the destination is left exactly as
 * it is unless its name appears in `overwrite`. That default is what makes I2 hold —
 * a same-name replacement has to be an explicit, reported decision.
 */
export function copyAdditive(srcDir, destDir, { overwrite = [] } = {}) {
	const allowed = new Set(overwrite);
	const copied = [];
	const replaced = [];
	const untouched = [];

	for (const name of readdirSync(srcDir).sort()) {
		const from = join(srcDir, name);
		const to = join(destDir, name);
		if (!existsSync(to)) {
			cpSync(from, to, { recursive: true });
			copied.push(name);
		} else if (allowed.has(name)) {
			const staged = `${to}.workflows-staged`;
			try {
				rmSync(staged, { recursive: true, force: true });
				cpSync(from, staged, { recursive: true }); // if this throws, `to` is untouched
				rmSync(to, { recursive: true, force: true });
				renameSync(staged, to);
				replaced.push(name);
			} finally {
				rmSync(staged, { recursive: true, force: true });
			}
		} else {
			untouched.push(name);
		}
	}

	return { copied, replaced, untouched };
}
