// Hand-written ambient declarations for tree.mjs, kept in sync manually.
// This file exists only so tsc --noEmit (run in CI via `bun run typecheck`)
// can resolve types for the exported functions.

export interface CopyAdditiveResult {
	copied: string[];
	replaced: string[];
	untouched: string[];
}

export function hashTree(dir: string): string;

/** `hashTree` for a directory, a content hash for a file, `''` for a missing or unreadable path. */
export function hashEntry(path: string): string;
export function copyAdditive(srcDir: string, destDir: string, options?: { overwrite?: string[] }): CopyAdditiveResult;
