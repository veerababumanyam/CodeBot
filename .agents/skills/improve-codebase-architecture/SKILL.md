---
name: improve-codebase-architecture
description: Analyze a codebase for architectural friction — shallow modules, leaky abstractions, coupled components, and unnecessary complexity — then propose concrete refactoring actions as GitHub issue RFCs. Use this skill whenever the user asks to improve code quality, reduce complexity, find architectural problems, audit module boundaries, or mentions concepts like "deep modules", "information hiding", "module depth", or "design it twice". Also use when the user says things like "this code feels messy" or "I want to clean this up" or "what should I refactor next".
---

# Improve Codebase Architecture

Systematically explore a codebase for architectural friction, guided by principles from John Ousterhout's *A Philosophy of Software Design*. Produces actionable GitHub issue RFCs for each improvement.

## Philosophy

Good software is built from **deep modules** — modules with simple interfaces that hide significant complexity. Architectural friction comes from the opposite: shallow modules, leaky abstractions, coupled components that force changes to ripple across the codebase, and "pass-through" layers that add interface surface without hiding anything.

This skill doesn't just find code smells — it identifies *structural* problems in how modules relate to each other and proposes refactorings that make the system deeper and simpler.

## Workflow

### Phase 1: Codebase Survey

Use the Agent tool with `subagent_type: "Explore"` to map the codebase structure:

1. **Identify module boundaries** — packages, services, libraries, major classes
2. **Map dependency flow** — which modules depend on which, where are the tight couplings
3. **Measure interface surface** — count public methods/exports per module
4. **Spot pass-through layers** — modules that mostly delegate to another module without adding value

Focus on the *architecture*, not individual functions. Read module-level overviews and public interfaces, not every line of implementation.

### Phase 2: Classify Dependencies

For each significant module relationship, classify it using these categories:

| Category | Description | Signal |
|----------|-------------|--------|
| **Deep** | Small interface, hides significant complexity | Good — leave alone |
| **Shallow** | Large interface relative to what it does | Candidate for merging or deepening |
| **Leaky** | Internal details bleed into the interface | Needs abstraction boundary repair |
| **Pass-through** | Mostly forwards calls to another module | Candidate for elimination |
| **Tightly coupled** | Changes in one force changes in the other | Needs interface redesign |
| **Classitis** | Many tiny classes/modules that could be one | Merge into fewer, deeper modules |

### Phase 3: Prioritize Improvements

Rank findings by **impact / effort**:

- **High impact**: problems in modules touched frequently, or that force changes to ripple across many files
- **Low effort**: problems solvable by merging modules, removing pass-through layers, or consolidating interfaces
- **Quick wins**: shallow wrappers that can be deleted, redundant abstractions, unnecessary indirection

Present the top 5-10 findings to the user with a brief explanation of each before writing issues.

### Phase 4: Generate Issue RFCs

For each approved improvement, create a GitHub issue (using `gh issue create`) with this structure:

```markdown
## Problem

[What architectural friction exists and where. Include file paths.]

## Analysis

[Why this is a problem — which Ousterhout principle it violates and what concrete harm it causes (ripple changes, cognitive load, redundant code)]

## Proposed Refactoring

[Specific steps to improve the architecture. Be concrete about what moves where.]

## Trade-offs

[What gets better, what might get temporarily worse, migration concerns]

## Affected Files

- `path/to/file1.py`
- `path/to/file2.py`

## Labels

architecture, refactoring, [severity: low|medium|high]
```

If `gh` is not available, write the issues as markdown files in a `docs/architecture-rfcs/` directory instead.

### Phase 5: Summary Report

Present a summary to the user:

1. **Architecture health score** — qualitative assessment (healthy / some friction / significant friction / needs major restructuring)
2. **Top findings** — numbered list with one-line descriptions
3. **Dependency map** — which modules are deep (good) vs shallow/leaky (need work)
4. **Recommended order** — which refactorings to do first based on dependency chain

## Key Principles (Reference)

These are the core ideas from Ousterhout that guide the analysis:

**Complexity is anything that makes software hard to understand or modify.** It manifests as:
- Change amplification (one change requires many edits)
- Cognitive load (too much to keep in your head)
- Unknown unknowns (not obvious what needs to change)

**Deep modules** are the antidote: they provide powerful functionality through simple interfaces. Unix file I/O is the classic example — `open`, `read`, `write`, `close` hide enormous complexity.

**Information hiding** means each module encapsulates decisions that other modules don't need to know about. When this fails, you get "information leakage" — the same knowledge duplicated across module boundaries.

**Pass-through methods** are a red flag: if a method does nothing except call another method with similar arguments, the module boundary isn't earning its keep.

**Classitis** — the tendency to create many small classes — often produces shallow modules. Sometimes fewer, deeper modules are better than many thin ones.

## Anti-Patterns to Avoid

- Don't report style issues (naming, formatting) — focus on structural/architectural problems
- Don't suggest refactorings that only rearrange code without making modules deeper
- Don't create issues for theoretical problems — every finding should point to concrete files and concrete harm
- Don't suggest adding abstraction layers — the default should be to *remove* unnecessary layers, not add more
