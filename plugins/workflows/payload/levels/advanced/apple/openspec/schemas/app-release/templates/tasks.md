<!-- Each step ends with the observable signal proving it worked. A code
defect discovered here stops the release and spawns a bugfix change. -->

- [ ] Archive the release build — signal: archive succeeds with the release configuration
- [ ] Upload — signal: build appears in App Store Connect processing
- [ ] TestFlight internal — signal: installs and launches on a physical device
- [ ] TestFlight external (when used) — signal: external build approved and installable
- [ ] Submit for review — signal: review state transitions to In Review
