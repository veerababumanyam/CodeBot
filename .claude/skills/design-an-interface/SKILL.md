---
name: design-an-interface
description: Generate multiple radically different interface designs for a module using parallel sub-agents. Use when user wants to design an API, explore interface options, compare module shapes, or mentions "design it twice". Invoke this skill whenever the user is creating a new module, library, SDK, or service boundary and hasn't yet committed to a specific interface shape — even if they don't explicitly say "design it twice."
---

# Design an Interface

Based on "Design It Twice" from John Ousterhout's *A Philosophy of Software Design*: your first idea is unlikely to be the best. Generate multiple radically different designs, then compare.

## Workflow

### 1. Gather Requirements

Before designing, understand:

- What problem does this module solve?
- Who are the callers? (other modules, external users, tests)
- What are the key operations?
- Any constraints? (performance, compatibility, existing patterns)
- What should be hidden inside vs exposed?

Ask: "What does this module need to do? Who will use it?"

### 2. Generate Designs (Parallel Sub-Agents)

Spawn 3+ sub-agents simultaneously using the Agent tool. Each must produce a **radically different** approach — not minor variations of the same idea.

**Prompt template for each sub-agent:**

```
Design an interface for: [module description]

Requirements: [gathered requirements]

Constraints for this design: [assign a different constraint to each agent]
- Agent 1: "Minimize method count — aim for 1-3 methods max"
- Agent 2: "Maximize flexibility — support many use cases"
- Agent 3: "Optimize for the most common case"
- Agent 4 (optional): "Take inspiration from [specific paradigm/library]"

Output format:
1. Interface signature (types/methods)
2. Usage example (how caller uses it)
3. What this design hides internally
4. Trade-offs of this approach
```

The key insight: by forcing radically different constraints, you prevent convergence on a single "obvious" design and discover trade-offs you wouldn't have noticed otherwise.

### 3. Present Designs

Show each design with:

1. **Interface signature** — types, methods, params
2. **Usage examples** — how callers actually use it in practice
3. **What it hides** — complexity kept internal

Present designs sequentially so the user can absorb each approach before comparison.

### 4. Compare Designs

After showing all designs, compare them on these dimensions from Ousterhout:

- **Interface simplicity**: fewer methods, simpler params = easier to learn and use correctly
- **General-purpose vs specialized**: flexibility vs focus — general-purpose modules are often *simpler* because they solve many problems with fewer concepts
- **Implementation efficiency**: does the interface shape allow efficient internals, or does it force awkward implementation?
- **Depth**: small interface hiding significant complexity = deep module (good); large interface with thin implementation = shallow module (avoid)
- **Ease of correct use** vs **ease of misuse**: can a caller get it wrong? How?

Discuss trade-offs in prose, not tables. Highlight where designs diverge most — that's where the interesting decisions live.

### 5. Synthesize

Often the best design combines insights from multiple options. Ask:

- "Which design best fits your primary use case?"
- "Any elements from other designs worth incorporating?"
- "What surprised you about any of these approaches?"

## Evaluation Criteria (from Ousterhout)

**Deep modules** have small, simple interfaces that hide significant implementation complexity. This is the gold standard. A deep module gives callers enormous power through a tiny surface area.

**Shallow modules** have large, complex interfaces relative to the functionality they provide. Every method the caller must learn is a cost — if the interface is as complex as the implementation, the module hasn't earned its keep.

**Information hiding** is the core mechanism: each module should encapsulate design decisions (data formats, algorithms, error handling strategies) that callers don't need to know about. If changing an internal detail forces callers to change, the abstraction is leaking.

## Anti-Patterns

- Don't let sub-agents produce similar designs — enforce radical difference via distinct constraints
- Don't skip comparison — the value is in contrast, not in any single design
- Don't implement — this skill is purely about interface shape and trade-offs
- Don't evaluate based on implementation effort — a harder-to-implement design might be far better for callers
- Don't default to the most "flexible" design — flexibility has a cost in interface complexity
