# Trigger battery: using-crossover-mac

## Should trigger (10)

1. "I installed Quicken in CrossOver but there's no icon for it anywhere."
2. "Elden Ring launches to a black screen in CrossOver 25 — which graphics option should I try?"
3. "How do I uninstall just Office from my bottle without losing my other programs?"
4. "My Windows game on the Mac won't let me use Option as Alt for keyboard shortcuts."
5. "CrossOver says my bottle has expired but I paid for the license last month."
6. "Can you read this .cxlog and tell me why the installer dies?"
7. "Where are my bottles stored? I want to move them to my external SSD."
8. "This Windows accounting program shows dates in US format but I'm in Australia. It's running on my MacBook without Parallels."
9. "Valorant won't start under CrossOver, is there a setting for the anti-cheat?"
10. "Set up Heroic so I can play my Epic games through CrossOver."

## Should not trigger (10) — near-misses

1. "My Windows 11 VM in Parallels is slow, how do I give it more RAM?" (real Windows in a VM; none of this applies)
2. "How do I install Wine with Homebrew on my Mac?" (plain Wine, not CrossOver's tools or bottles)
3. "Whisky won't open my game's .exe anymore." (a different Wine wrapper with different paths and settings)
4. "Port my DirectX 12 game to Metal using Apple's Game Porting Toolkit." (developer porting work, not running an app in CrossOver)
5. "Set up Boot Camp on my Intel Mac." (native Windows install)
6. "What's the best gaming controller for macOS?" (purchasing advice, no CrossOver)
7. "My Steam games on macOS won't launch since updating to Sequoia." (native Mac Steam, nothing about Windows apps)
8. "Write a Windows batch script that renames files." (Windows scripting with no Mac or CrossOver involved)
9. "Configure Wine prefixes on my Ubuntu server for a headless app." (Linux Wine)
10. "How do I map a network drive in Windows 11?" (Windows itself, not a bottle's drive letters)

## Notes on the negatives

Negatives 2–4 and 9 are the hard ones. They share the engine (Wine) or the goal (Windows software on a Mac), but CrossOver's bottles, `cxbottle` command, Advanced Settings, and support boundaries do not transfer to them. A description that over-triggers on "Wine" or "run a Windows game on Mac" will catch them.
