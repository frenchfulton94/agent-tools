#!/bin/bash
# Prints the help and man-page lines that direct-distribution.md relies on for
# each command spelling (ruling P34). Read-only: it signs, submits, and
# changes nothing.
#
#   help-check.sh > help.log 2>&1
set -uo pipefail
man_text() { man -P cat "$1" 2>/dev/null | col -b; }

echo "Machine: $(sysctl -n machdep.cpu.brand_string), macOS $(sw_vers -productVersion) $(sw_vers -buildVersion), $(xcodebuild -version | head -1) ($(xcodebuild -version | tail -1))"
echo "Date: $(date '+%Y-%m-%d %H:%M %Z')"
echo "Active developer directory: $(xcode-select -p)"

show() {   # show <title> <grep -E pattern> <command...>
  local title="$1" pat="$2"
  shift 2
  echo
  echo "## $title"
  echo "\$ $* 2>&1 | grep -n -E '$pat'"
  "$@" 2>&1 | grep -n -E -- "$pat"
}

show "notarytool version" '.' xcrun notarytool --version
show "notarytool subcommands" '^  (store-credentials|submit|info|wait|history|log) ' xcrun notarytool --help
show "notarytool store-credentials" 'USAGE|<profile-name>|--apple-id|--team-id|--password|--key |--key-id|--issuer|Required for Team|Do not provide|--validate|--keychain <' xcrun notarytool store-credentials --help
show "notarytool submit" 'USAGE|keychain-profile|--wait|--timeout|continue processing|output-format|--webhook|s3-acceleration|--force' xcrun notarytool submit --help
show "notarytool log" 'USAGE|pretty printed|output-format|<output-path>|default: stdout' xcrun notarytool log --help
show "notarytool history" 'USAGE|OVERVIEW' xcrun notarytool history --help
show "stapler usage" 'Usage|Supported file formats|bundles, and signed' xcrun stapler

echo
echo "## codesign(1)"
echo "\$ man codesign | col -b | grep -n -E '<flags below>'"
man_text codesign | grep -n -E -- '--check-notarization|^     --deep|DEPRECATED for signing|-f, --force|existing signature|--force-library-entitlements|non-main-executables|as of macOS 15.0|-o, --options|^     runtime|hardened runtime environment|ignore the|--entitlements path|--xml or --der|Use "-" as the path|^     --strict|--strict=all|--timestamp \[=URL\]|default server provided by Apple|signing operation will fail|system-specific default|special value none|-i, --identifier|-r, --requirements|-s, --sign'

echo "\$ man codesign | col -b | grep -n -A4 -E -- '^     --force-library-entitlements|^     --deep '"
man_text codesign | grep -n -A4 -E -- '^     --force-library-entitlements|^     --deep '

echo
echo "## spctl(8)"
echo "\$ man spctl | col -b | grep -n -E '<flags below>'"
man_text spctl | grep -n -E -- '-a, --assess|-t, --type|execute to assess|install to assess|package, and open|default is to assess|-v, --verbose|--raw|As of MacOS 15.0|state of the assessment subsystem|exit code is three|exits zero|Exit code two'

show "syspolicy_check subcommands" '^  (distribution|notary-submission) ' syspolicy_check --help
show "syspolicy_check distribution" 'USAGE|Gatekeeper|--json' syspolicy_check help distribution
show "syspolicy_check notary-submission" 'USAGE|--json' syspolicy_check help notary-submission

show "hdiutil create" 'WARNING|Usage|-srcfolder|-volname|-format|^	    -ov|-fs <' hdiutil create -help
echo
echo "## hdiutil(1) deprecation notice"
echo "\$ man hdiutil | col -b | grep -n -E 'DEPRECATION|preferred interface|create -srcfolder'"
man_text hdiutil | grep -n -E -- 'DEPRECATION NOTICE|preferred interface|create -srcfolder'
show "diskutil image create from" 'USAGE|--format|ULFO unless|--volumeName' diskutil image create from
show "hdiutil verify" 'Usage' hdiutil verify -help

echo
echo "## ditto(1)"
echo "\$ man ditto | col -b | grep -n -E '<flags below>'"
man_text ditto | grep -n -E -- '^     -c |^     -k |--keepParent|ditto -c -k'

show "pkgbuild usage" 'Usage' pkgbuild
echo
echo "## pkgbuild(1)"
echo "\$ man pkgbuild | col -b | grep -n -E '<flags below>'"
man_text pkgbuild | grep -n -E -- '^     --sign|^     --timestamp|^     --keychain|^     --identifier|^     --version|^     --install-location|^     --scripts|by default when signing with a Developer ID'
show "productbuild usage" 'Usage' productbuild
echo
echo "## productbuild(1)"
echo "\$ man productbuild | col -b | grep -n -E '<flags below>'"
man_text productbuild | grep -n -E -- '^     --sign|^     --timestamp|^     --keychain|^     --component component-path|^     --synthesize|^     --distribution|^     --package-path'
show "productsign usage" 'Usage' productsign

echo
echo "## pkgutil(1)"
echo "\$ man pkgutil | col -b | grep -n -E -- '--check-signature'"
man_text pkgutil | grep -n -E -- '--check-signature|certificate chain'

echo
echo "## security(1) find-identity"
echo "\$ man security | col -b | grep -n -E 'find-identity|-p policy|-v  '"
man_text security | grep -n -E -- 'find-identity \[|Specify policy to evaluate|Show valid identities only'

echo
echo "## Developer ID identity check (read-only; names redacted after the certificate type)"
echo "\$ security find-identity -v -p codesigning"
security find-identity -v -p codesigning | sed -E 's/^ *[0-9]+\) [0-9A-F]{40} "([^:"]+):[^"]*"/  \1: <name redacted>/'
echo "\$ security find-identity -v    # installer identities are hidden by -p codesigning"
security find-identity -v | sed -E 's/^ *[0-9]+\) [0-9A-F]{40} "([^:"]+):[^"]*"/  \1: <name redacted>/'
echo "Developer ID Application identities: $(security find-identity -v -p codesigning | grep -c 'Developer ID Application')"
echo "Developer ID Installer identities: $(security find-identity -v | grep -c 'Developer ID Installer')"

echo
echo "## plutil"
echo "\$ plutil -help 2>&1 | grep -n -E -- '-lint|-convert|-extract'"
plutil -help 2>&1 | grep -n -E -- '^ *-lint|^ *-convert|^ *-extract'
