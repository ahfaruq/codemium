# Codemium Product Requirements Document

## Product definition

Codemium is a **host-agnostic persistent coding-intelligence layer** for AI coding agents. It makes an agent behave increasingly like an engineer who has worked on the same repository for months: durable project knowledge is reused, only the relevant project slice is activated for each task, changes stay scoped, testing follows risk, and unchanged understanding is not repeatedly paid for.

Codemium is not a wrapper around one vendor, model family, or prompt syntax. OpenAI Codex is the reference adapter; Claude Code, Gemini CLI, Cursor, OpenCode, and future hosts consume the same engineering contract through host-native surfaces.

## North-star outcome

As project complexity grows:

```text
Durable project knowledge   ↑↑↑
Project understanding       ↑↑
Correctness                 >= baseline
Architecture consistency    >= baseline

Active task context         bounded
Repeated discovery          ↓↓↓
Unrelated changes           → 0
Token/context waste         ↓↓↓
```

Resource efficiency only counts as a win after correctness, security, testing adequacy, architecture consistency, and scope integrity meet the quality floor.

## Positioning

> **The senior engineer who already knows your codebase.**

Codemium optimizes **minimum justified engineering**, not minimum LOC.

## Host architecture

```text
                         CODEMIUM CORE
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
     Project Brain     Repository/Task Core   Shared Policy
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
        ┌───────────┬─────────┼─────────┬───────────┐
        │           │         │         │           │
      Codex       Claude    Gemini    Cursor     OpenCode
        │           │         │         │           │
  @Codemium  /codemium:cm    /cm       /cm      cm skill
```

A host adapter may change invocation syntax, plugin/extension layout, model controls, and tool plumbing. It must not fork Codemium's durable project-state semantics or weaken its engineering/safety invariants.

## Supported-host policy

- **Stable**: host integration is the reference implementation and exercised by repository fixtures plus actual-host validation for the release line.
- **Beta**: packaging follows the host's documented native surface and repository CI validates the bundle, but actual-host runtime validation is still required before Stable promotion.
- **Planned**: no installable adapter should be advertised as working.

Current release target:

| Host | Status | Primary invocation |
| --- | --- | --- |
| OpenAI Codex | Stable | `@Codemium` |
| Claude Code | Beta | `/codemium:cm` or skill auto-selection |
| Gemini CLI | Beta | `/cm` |
| Cursor | Beta | `/cm` / Agent Skill UI |
| OpenCode | Beta | skill tool/auto-selection, `/cm` where exposed |

## User experience

Codemium should expose the most natural host-level identity available. On OpenAI Codex, the primary product UX is the installed plugin mention **`@Codemium`**. The portable internal Agent Skill identifier remains **`cm`** for direct skill invocation and non-plugin hosts.

Typical Codex usage should be natural language:

```text
@Codemium review this repository before making changes
@Codemium fix the profile save bug
@Codemium deeply investigate this intermittent queue failure
@Codemium safely change this authentication flow and verify the impact
```

Codemium automatically classifies the task and selects the smallest safe depth. Users should not need to learn internal task/depth syntax for ordinary use.

Advanced direct skill invocation remains available:

```text
$cm
$cm fast
$cm deep
$cm critical
```

Other hosts retain their native surfaces:

- Codex: `@Codemium ...` primary; `$cm ...` direct Agent Skill fallback.
- Claude Code: `/codemium:cm ...`.
- Gemini CLI: `/cm ...`.
- Cursor: `/cm` where the Agent Skill slash UI is available.
- OpenCode: native skill loading; slash exposure when supported.

Plain `cm` semantics mean automatic task classification and automatic depth. NORMAL is intentionally not required as a typed modifier.

## Task axis

Codemium classifies work as:

- BUILD
- FIX
- TEST
- REFACTOR
- REVIEW
- MIGRATION
- SECURITY

Task type changes engineering policy, not just wording.

## Depth axis

- **FAST** — narrow, obvious, localized, low-risk work.
- **NORMAL** — ordinary project-aware engineering.
- **DEEP** — complex, intermittent, concurrent, distributed, performance-sensitive, cross-boundary, or materially uncertain work.
- **CRITICAL** — trust-boundary/security, authentication/authorization, payments, migrations, secrets, production data, destructive operations, deployment/infrastructure, or breaking public interfaces.

A user override may increase depth but cannot lower the minimum safe depth.

## Portable reasoning classes

Reasoning is separated into a vendor-neutral class:

| Depth | Preferred class | Minimum class |
| --- | --- | --- |
| FAST | economy | economy |
| NORMAL | balanced | economy |
| DEEP | strong | balanced |
| CRITICAL | frontier | strong |

Host adapters may map these classes only when the host exposes documented, safe, confirmable controls.

The Codex adapter currently maps economy/balanced/strong/frontier to `low`/`medium`/`high`/`xhigh` when supported. Other adapters must not invent equivalent vendor controls.

## Project Brain

Codemium durable state lives in:

```text
.codemium/
```

It may contain:

- Project Charter;
- architecture boundaries;
- Decision Ledger;
- Constraint Registry;
- Interface Registry;
- Pattern Registry;
- Known Bug Registry;
- repository/test intelligence;
- active task contract;
- deterministic cache/telemetry.

Project Brain is not a conversation transcript and must not store secrets.

## Repository Intelligence

Build deterministic or low-cost maps before broad narrative reading:

- files;
- symbols;
- imports/dependencies;
- likely callers/references where available;
- source-to-test relationships;
- changed files/symbols;
- repository state identity.

The model should consume selected evidence, not crawl the repository blindly.

## Working Set Engine

Each task gets a bounded Working Set containing only facts/code likely to affect the decision.

Preferred retrieval order:

1. active task contract;
2. relevant durable project facts;
3. repository map/symbols;
4. exact candidate code regions;
5. relevant tests/runtime evidence;
6. deeper history only for a named unresolved question.

Context expansion is progressive and evidence-triggered.

## Read-once / delta-first behavior

If an artifact's relevant state identity has not changed, reuse extracted understanding. When it changes, inspect the delta/changed symbols before rereading the whole artifact.

Equivalent deterministic reads, searches, and verification should be reused when validity is provable.

## Engineering doctrine

After understanding the actual requirement:

```text
need?
→ existing project solution?
→ standard library?
→ native framework/platform?
→ existing dependency?
→ local simple implementation?
→ new abstraction/dependency
```

A shorter diff is not automatically better. The winning change is the smallest change that is correct for the current architecture, interfaces, risk, and required testing.

## Scope Guard

Every changed hunk should be attributable to:

- DIRECT — requested behavior;
- DEPENDENCY — necessary supporting change;
- CLEANUP — code made obsolete specifically by this change;
- TEST — evidence for changed behavior.

Default-disallowed opportunistic work:

- unrelated formatting;
- adjacent refactoring;
- style modernization;
- unrelated renaming/comments;
- deleting pre-existing dead code;
- speculative architecture changes.

Adjacent issues should be reported, not silently fixed.

## Test Intelligence

Production-code minimalism never implies minimal tests.

Testing depth follows:

- behavior surface;
- failure modes;
- boundaries;
- security/data risk;
- blast radius;
- historical regressions;
- existing project test patterns.

Verification ranges from focused syntax/unit checks through subsystem/integration/runtime verification as justified.

## Change Impact

Before completion, identify affected callers/dependents, interfaces, background workers/events, database/public surfaces, and relevant tests where practical. Blast radius determines verification depth.

## Stop Engine

Stop when all required gates pass:

```text
objective satisfied
acceptance satisfied
verification sufficient
scope clean
architecture/security preserved
material uncertainty resolved
required review complete
```

Additional inspection after these gates requires a named unresolved risk that the next operation can reduce.

## Host adapter contract

Every supported adapter must preserve:

1. task classification;
2. safety-bounded depth;
3. shared `.codemium/` state;
4. bounded context/working sets;
5. minimum justified engineering;
6. scope integrity;
7. risk-aware testing;
8. deterministic reuse where valid;
9. explicit stop conditions;
10. honest host/model-control reporting.

## Distribution architecture

### Codex

Codex plugin lives under `plugins/codemium/`, including the canonical deterministic engine and Agent Skills. The primary product invocation is `@Codemium`; direct `$cm` invocation remains available for advanced/compatibility use.

### Claude Code

The repository root is the Claude plugin root. `.claude-plugin/plugin.json`, `skills/cm/SKILL.md`, and `commands/cm.md` are auto-discovered. This lets the skill reference the canonical engine inside the same installed plugin bundle.

### Gemini CLI

The repository root contains `gemini-extension.json`, `GEMINI.md`, and `commands/cm.toml`.

### Cursor / OpenCode

A portable Agent Skill bundle is installed by `scripts/install_host.py`. The installer copies the portable `SKILL.md`, canonical engine, and references into the host's documented skill directory. It manages only Codemium-owned directories and refuses unrecognized overwrite/removal without explicit `--force`.

## Doctor / validation

`scripts/doctor.py` validates cross-host manifests, version synchronization, native invocation contracts, portable-skill packaging, and engine completeness. It also reports which host binaries are locally available.

Repository CI runs the deterministic verifier and doctor on every main push/pull request.

## Functional requirements

- FR-001 — initialize portable Project Brain.
- FR-002 — build lightweight repository/test intelligence.
- FR-003 — compile task + safe depth contracts.
- FR-004 — generate bounded Working Sets.
- FR-005 — expand context only for material uncertainty.
- FR-006 — preserve/reuse unchanged understanding where identity is valid.
- FR-007 — enforce scoped diffs.
- FR-008 — map impact to sufficient verification.
- FR-009 — preserve architecture/constraint/interface knowledge.
- FR-010 — detect/avoid duplicate deterministic work.
- FR-011 — stop after sufficient proof.
- FR-012 — keep reasoning semantics model/vendor-independent.
- FR-013 — provide native Codex, Claude Code, Gemini CLI, Cursor, and OpenCode distribution surfaces.
- FR-014 — keep adapter versions synchronized with repository VERSION.
- FR-015 — provide safe install/uninstall for portable Agent Skill hosts.
- FR-016 — never claim host reasoning changes or token savings without evidence.
- FR-017 — expose `@Codemium` as the primary Codex plugin UX while preserving direct internal skill invocation.

## Quality order

1. Safety and data integrity
2. Correctness
3. Architecture/interface consistency
4. Verification adequacy
5. Scope integrity
6. Context/token/latency efficiency
7. Code volume

Optimization that lowers a higher-ranked quality dimension is a failure.

## Benchmarking

The benchmark engine remains evidence-gated. Public efficiency claims require measured agent runs under controlled, comparable conditions and must not substitute synthetic/demo numbers for real performance.

Competitive/ablation data is not part of Codemium's public README until measured publication criteria are met.

## Non-goals

Codemium is not:

- a minimum-LOC contest;
- a license to under-test;
- a generic multi-agent bureaucracy;
- a replacement for CI;
- a promise that one model/reasoning level is best forever;
- a vendor-specific project-memory format;
- a reason to preload an entire repository;
- permission to edit unrelated code.

## v0.6 release definition

v0.6 is complete when:

- Codex exposes `@Codemium` as the primary installed-plugin invocation while retaining `$cm` as the direct skill path;
- Claude repository-root plugin includes shared core access;
- Gemini extension manifests/command validate;
- Cursor/OpenCode portable Agent Skill installation is safe and documented;
- shared reasoning classes are vendor-neutral;
- README/HOSTS/INSTALL/PRD agree on host status and invocation;
- CI verifies versions/layout, portable installer behavior, engine fixtures, and hidden benchmark publication gate;
- repository doctor reports a clean layout.
