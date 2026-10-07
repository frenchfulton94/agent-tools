import { pathToFileURL } from 'node:url';

/**
 * `-e`, `-p`, a short group holding either (`-pe`), and `--eval` / `--print` with or
 * without `=<code>`. Node 24 keeps each of these as one `execArgv` token, with the code in
 * the next token when it is not joined by `=`.
 */
const EVAL_FLAG = /^(?:-[a-zA-Z]*[ep][a-zA-Z]*|--(?:eval|print)(?:=[\s\S]*)?)$/;

/**
 * Whether the module at `moduleUrl` is the script node was started on, so its CLI block
 * should run.
 *
 * `argv[1]` alone cannot answer this. Setup imports these modules through
 * `node -e '…import(pathToFileURL(process.argv[1]).href)…' <module> …`, and under `-e`
 * argv[1] is the first argument after the code — the module itself. A guard that compares
 * only argv[1] runs the CLI on import and exits before the snippet's callback: verify
 * reports its I1 checks against empty hashes, and the config-facts snippets print the
 * artifact-id listing and exit 1. Started with an eval or print flag, node ran no script
 * file, so no module is main.
 */
export function isMain(moduleUrl, { argv = process.argv, execArgv = process.execArgv } = {}) {
	if (!argv[1] || moduleUrl !== pathToFileURL(argv[1]).href) return false;
	return !execArgv.some((flag) => EVAL_FLAG.test(flag));
}
