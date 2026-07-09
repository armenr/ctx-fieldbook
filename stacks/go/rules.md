---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-09
paths: ["**/*.go", "**/go.mod", "**/go.sum"]
---

# Go rules

The stack-specific concretion of the universal quality-gate discipline in `standing-rules-core.md`
(§Quality gates). Short on purpose — deep architecture lives in your project's own `reference/`. This
pack is the Go binding for the generic `{{BUILD_CMD}} / {{TEST_CMD}} / {{LINT_CMD}} / {{FMT_CMD}} /
{{PANIC_EQUIVALENT}} / {{CODE_INTEL_TOOL}}` seams.

> **Currency:** the commands below were checked against PRIMARY docs on 2026-07-03 — the go command
> reference (go.dev / pkg.go.dev/cmd/go, pkg.go.dev/cmd/gofmt), golangci-lint.run, and staticcheck.dev.
> Re-verify tool versions against current-year primary docs before adopting; never build from memory.

## The gate seams (fill the core scalars)

| Core scalar | Go command |
|---|---|
| `{{BUILD_CMD}}` | `go build ./...` |
| `{{TEST_CMD}}` | `go test ./...` (add `-race` for concurrent code — see below) |
| `{{LINT_CMD}}` | `go vet ./...` **and** `golangci-lint run` |
| `{{FMT_CMD}}` | `gofmt -l .` (check, non-empty output = fail) · `gofmt -w .` (apply) |

## Lint & format gates (strict by decision, not preference)

- **`go vet ./...` and `golangci-lint run` must both pass — a finding is a failure, not a suggestion**
  (mirrors the core "warnings are errors" posture). `go test` already runs a high-confidence `go vet`
  subset automatically and refuses to run the test binary if it trips, but run the FULL `go vet` and
  `golangci-lint run` as first-class gates anyway.
- **`golangci-lint` is the aggregate linter.** Its zero-config default set — `errcheck`, `govet`,
  `ineffassign`, `staticcheck`, `unused` — is the strict baseline; pin the version in a
  `.golangci.yml` / `.golangci.yaml` and in CI so local and CI agree — and make that versions-check
  the FIRST gate stage: verify `go version` and `golangci-lint version` against the pins (`go.mod`'s
  `go` / `toolchain` directives, the `.golangci.yml` pin) and FAIL on drift, rather than letting the
  later stages go vacuously green under a toolchain the pins don't describe. `staticcheck` may also be
  run standalone (`staticcheck ./...`). Do not disable a linter to get past a finding — investigate it.
- **Formatting is not optional: code MUST be gofmt-clean.** `gofmt` is canonical; `goimports`
  (golang.org/x/tools/cmd/goimports) is the superset that also repairs import grouping. CI checks with
  `gofmt -l .`; `golangci-lint fmt` is the v2 formatter entrypoint. The pre-commit hook runs the
  formatter + linter; **never `--no-verify`** to route around a failing gate.

## Error handling — the {{PANIC_EQUIVALENT}} rule for Go

In a Go library, `{{PANIC_EQUIVALENT}}` = **a naked `panic()`, an ignored `error` return, or an
unchecked type assertion that panics at runtime.** All three convert a caller's recoverable failure
into a process abort it cannot catch. Return a typed `error` instead.

- **Never ignore a returned `error`.** Every error-returning call has its error checked, or
  deliberately and visibly discarded (`_ = f()` **with a comment saying why**). This is the `errcheck`
  lint (default-on in `golangci-lint`) — do not disable it. Wrap to preserve the chain
  (`fmt.Errorf("doing X: %w", err)`); never swallow.
- **No `panic()` in library code.** `panic` is for a truly-unrecoverable invariant violation, not
  control flow or error reporting. Exported functions return `error`; only a `main` / CLI edge
  translates an error into an exit code. A recovered panic that hides a bug is worse than a returned error.
- **`defer`-ed cleanup that can fail must not silently drop its error** — on a writable resource,
  capture it (`defer func() { err = errors.Join(err, c.Close()) }()` with a named return) rather than a
  bare `defer c.Close()`.

## No unchecked type assertions

- **Use the comma-ok form:** `v, ok := x.(T)` and handle `!ok`. The single-result form `v := x.(T)`
  **panics** on a type mismatch — it is an unhandled-panic site under the {{PANIC_EQUIVALENT}} rule.
  In a type switch, cover the `default` case rather than assume exhaustiveness.

## Concurrency correctness

- **Run `go test -race ./...` for any package that spawns goroutines or shares state.** `go vet`
  catches some misuse (lock copies, misused `sync` types); the race detector catches data races `vet`
  cannot see. A behavior change to concurrent code OWES a `-race` test (core: "a behavior change owes a
  test that would fail without it").

## Dependency discipline

- **`go mod tidy` after any import change; commit `go.mod` AND `go.sum` together.** Scripted
  `go mod edit -require/-replace/...` bypasses tidy's reconciliation and is safety-gated (ask) — prefer
  `go get` / `go mod tidy`.
- **Currency-check before adding or bumping ANY module** (`standing-rules-core.md` §external deps):
  verify the latest stable version + deprecation status of the *exact* API you use against current-year
  primary docs, not memory. A published module version is effectively immutable (see the semver
  tag-push gate in `gate-fragment.sh`), so a bad add is expensive to walk back.

## Acceptance for any change here

- **A behavior change OWES a test that fails without it.** `go test` green is necessary, not sufficient.
- **IMPL → WIRED is the bar, not test-pass.** After it builds and tests pass, prove the new code is
  reachable from a production entrypoint (a `main` package's `main()`, an `init()`, a registered
  handler / command) and record IMPL/WIRED/DEFER in `traceability/`. Note the compiler only rejects
  unused *locals* and *imports* — an unused *exported* / package-level symbol builds clean, so
  reachability is on you + the linters. Prove it with `{{CODE_INTEL_TOOL}}` (for Go: gopls references /
  call hierarchy, with a grep-the-callers floor — see `code-intel.md`). Dead code that the `unused`
  linter / staticcheck `U1000` flags is a wiring failure, not noise.

## Related

- `code-intel.md` (the Go reachability prover menu) · `standing-rules-core.md` (§Quality gates,
  §IMPL→WIRED) · `../../base/*/agent-docs/CONVENTIONS.md` (the schema contract) ·
  `../generic/rules.template.md` (the interview-filled fallback)
