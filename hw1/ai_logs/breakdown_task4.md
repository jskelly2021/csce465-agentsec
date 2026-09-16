# Task 4 Conversation Export

**Course:** CSCE 465/765 — Computer & Network Security  
**Assignment:** Homework 1 — Build and Threat-Model an AI Agent  
**Reference:** `HW1.pdf`

---

## User

Breakdown Task 4 into actionable steps. What do I need to create? What do I need to save and what are my deliverables?

---

## Assistant

Task 4 is really **two separate deliverables bundled together**:

1. **Threat-model the webpage-summary workflow**
2. **Analyze one real OpenClaw security advisory**

You do **not** need to discover or exploit a new vulnerability for Task 4—that's the optional bonus.

## What you need to create

I’d structure Task 4 like this:

```text
hw1/
├── threat-model.md
├── advisory-analysis.md
├── attack-surface-map.pdf
└── evidence/
    ├── task4-exec-policy.txt
    ├── task4-diagram.png
    └── ...any other useful screenshots/evidence
```

Then the important parts from those files get incorporated into your final `report.pdf`.

---

# Part A — Threat Model

### Step 1: Save your current exec policy

Run:

```bash
openclaw exec-policy show
```

Save it:

```bash
openclaw exec-policy show > evidence/task4-exec-policy.txt
```

This matters because the assignment specifically requires the **effective exec-approval policy** to appear as a control—or as a missing control—on the skill/tool-decision boundary.

Given what you've already been investigating in Task 3, this is where you discuss things like:

```text
security=full
ask=off
```

and what that means when the model proposes an execution.

---

# Step 2: Map the actual webpage-summary workflow

Your diagram should represent the workflow you actually used in Task 3.

Because OpenClaw blocks loopback `web_fetch`, your indirect experiment is roughly:

```text
Local Webpage Server
        │
        │ adversarial.html
        ▼
 User / curl / browser
        │
        │ pasted as "retrieved external content"
        ▼
 OpenClaw Gateway
        │
        ▼
   Agent Context
        │
        ▼
 Model / Ollama
        │
        │ proposed action
        ▼
 Skill / Tool Decision
        │
        ▼
 Shell / File Operation
        │
        ▼
    VM Operating System
```

That's an important detail: **the webpage server doesn't directly instruct the shell.** Its data enters the user prompt, becomes part of the agent context, and may then be interpreted by the model as an instruction.

Your diagram must explicitly include all eight components required by the assignment:

- User or Web UI
- OpenClaw Gateway
- Model provider or Ollama
- Agent context
- Skill/tool decision
- Shell or file operation
- Local webpage server
- VM operating system

---

# Step 3: Identify at least four assets

I'd put these in `threat-model.md` and label them `A1`, `A2`, etc. Then reuse those labels in the diagram.

For example:

```markdown
## Assets

- A1 — Integrity of files inside the course workspace
- A2 — Authority to execute shell commands
- A3 — OpenClaw configuration and security policy
- A4 — Agent context and control instructions
- A5 — Audit logs and experiment evidence
```

You technically only need **four**, but five is fine.

Think of an asset as **something you care about protecting**.

---

# Step 4: Identify at least three principals

A principal is basically an actor/process operating with some identity or authority.

For your setup:

```markdown
## Principals

- P1 — Student/user
- P2 — OpenClaw agent/Gateway
- P3 — Model provider or local Ollama model
- P4 — VM operating system/tool process
```

Three are required.

---

# Step 5: Identify at least four trust boundaries

This is one of the most important parts.

A trust boundary is a place where data moves between components with **different levels of trust or authority**.

Good ones for your experiment:

```text
TB1: Local webpage → user
     Untrusted webpage content enters your workflow.

TB2: User → OpenClaw Gateway
     User-controlled/control-channel input enters the agent.

TB3: Agent context/model → skill/tool decision
     Model-generated intent may become an actionable operation.

TB4: Skill/tool decision → operating system
     Agent-generated action crosses into real OS authority.

TB5: Gateway → remote model provider
     Only applicable if you're using an API model.
```

If you're using Ollama locally, you don't really need TB5. Four are enough.

---

# Step 6: Define six threats

This is where I'd use numbered threats like `T1–T6`.

You want threats that actually correspond to your architecture rather than generic cybersecurity vocabulary.

For example:

| ID | Threat |
|---|---|
| T1 | Malicious webpage text is interpreted as an agent instruction |
| T2 | Model proposes a shell operation that the user did not authorize |
| T3 | Tool input is manipulated to execute arbitrary shell commands |
| T4 | Tool writes outside the intended marker location |
| T5 | The `safe-marker` skill itself is modified/tampered with |
| T6 | Sensitive configuration or credentials are exposed to a model/tool |

Then give **one preventive or detective control for every threat**.

Something like:

| Threat | Control |
|---|---|
| T1 | Treat retrieved webpage content as untrusted data; preserve provenance |
| T2 | Exec approval/authorization check at tool boundary |
| T3 | `safe_marker.sh` accepts one fixed argument and executes no user-supplied command |
| T4 | Fixed output path + filesystem permissions |
| T5 | Git history/file permissions/integrity checking |
| T6 | No real secrets in the VM; least-privilege credentials/config permissions |

For **T2**, explicitly discuss your real `exec-policy`.

For example, if yours says:

```text
security=full
ask=off
```

you may conclude that the approval layer does **not prompt a human before execution**, so in this experiment it is a weaker/missing authorization control rather than pretending it's a control that doesn't exist.

That's exactly the kind of reasoning they're asking for.

---

# Step 7: Draw the diagram

Create:

```text
attack-surface-map.pdf
```

I would use numbered labels rather than trying to cram paragraphs into the boxes:

```text
[T1]
Local Web Server
      │
      │ Untrusted HTML
      ▼
────── TB1 ──────
      │
    User P1
      │
      ▼
────── TB2 ──────
 OpenClaw Gateway P2
      │
 Agent Context [A4]
      │
      ▼
 Model/Ollama P3
      │
      │ Tool proposal
      ▼
────── TB3 ──────
 Skill / Tool Decision
   [exec policy]
      │
      ▼
────── TB4 ──────
 Shell / File Operation
      │
      ▼
 VM OS / Filesystem [A1]
```

Then have a legend beside/below it:

```text
T1 — indirect prompt injection
T2 — unauthorized tool execution
...
```

and similarly for `A1`, `P1`, `TB1`, etc.

The assignment asks for **one readable diagram**, so clarity matters more than making it look fancy.

---

# Part B — Security Advisory Analysis

This is a completely separate section of Task 4.

## Step 8: Pick one current OpenClaw advisory

The homework directs you to:

```text
OpenClaw GitHub
→ Security
→ Advisories
```

and says that the **patch diff is one of the most useful artifacts**, because it lets you identify what the vulnerable code actually did and what changed.

Pick one advisory from your instructor's approved shortlist/current OpenClaw advisories.

You are **analyzing an existing vulnerability**, not finding your own.

---

# Step 9: Collect evidence before writing

For the advisory you select, find:

```text
GHSA identifier
Affected version(s)
Severity
Advisory description
Vulnerable source/component
Fix commit or PR
Actual code diff
```

Don't rely solely on the advisory's title.

The professor specifically wants you reasoning from evidence rather than simply repeating labels.

The patch is especially useful for figuring out:

```text
attacker input
      ↓
vulnerable code path
      ↓
missing/incorrect security check
      ↓
impact
      ↓
patched behavior
```

---

# Step 10: Answer the seven required advisory questions

Create:

```text
advisory-analysis.md
```

I'd use this skeleton:

```markdown
# Task 4 Advisory Analysis

## Advisory

GHSA-XXXX-XXXX-XXXX

## Vulnerable Component

...

## Attacker-Controlled Input

...

## Preconditions

...

## Root Cause

...

## Impact

...

## Fix

...

## Regression Test

...

## Role of Prompt Injection

Prompt injection is [required / helpful / irrelevant] because ...
```

The assignment explicitly requires all of those points.

---

# Step 11: Write the 500–700 word analysis

Your final advisory write-up must be **500–700 words**.

The biggest distinction to keep clear is:

**Attacker-controlled input**
> What does the attacker get to provide?

versus

**Root cause**
> What mistake in the program causes that input to become dangerous?

For example, don't say:

> "The root cause was malicious input."

That's the input, not the root cause.

A root cause is more like:

> "The application passed an attacker-controlled value into X without checking Y."

or:

> "Authorization was performed before a redirect but was not re-evaluated against the final destination."

Exact answer depends on whichever advisory you choose.

---

# Step 12: Design one regression test

You don't necessarily need to implement the whole upstream test suite.

You need to explain a test demonstrating that:

```text
Before patch:
malicious input → vulnerable behavior

After patch:
same malicious input → rejected/sanitized/safe behavior
```

For example:

```markdown
A regression test should construct ______ using attacker-controlled
______. The test should verify that OpenClaw rejects the operation
rather than allowing ______.
```

Make it specific enough that a developer could reasonably implement it.

---

# Step 13: Classify the role of prompt injection

This is a required question and probably one the professor cares about a lot.

Choose one:

```text
Required
Helpful
Irrelevant
```

Don't assume every AI-agent vulnerability is prompt injection.

For example:

- If exploitability requires convincing the model to perform an operation → prompt injection might be **required or helpful**.
- If a malicious HTTP request can directly exploit a bug in the Gateway regardless of the model → prompt injection is probably **irrelevant**.

Explain **why**.

---

# What should be saved?

By the end of Task 4, I'd make sure you have:

```text
hw1/
├── threat-model.md
│   ├── architecture/workflow description
│   ├── assets
│   ├── principals
│   ├── trust boundaries
│   ├── six threats
│   └── controls
│
├── advisory-analysis.md
│   └── 500–700 word advisory analysis
│
├── attack-surface-map.pdf
│   └── labeled data-flow diagram
│
└── evidence/
    ├── task4-exec-policy.txt
    ├── task4-diagram.png
    └── optional advisory/reference screenshots
```

You should also make meaningful Git commits as you go because Git history is part of the overall grading.

For example:

```bash
git add threat-model.md evidence/task4-exec-policy.txt
git commit -m "Document Task 4 threat model"

git add attack-surface-map.pdf
git commit -m "Add Task 4 data flow diagram"

git add advisory-analysis.md
git commit -m "Add OpenClaw advisory analysis"
```

---

# What goes into `report.pdf`?

Task 4's portion of the final report needs:

```text
Task 4
├── Data-flow diagram
├── Assets
├── Principals
├── Trust boundaries
├── Six threats
├── Control for each threat
├── Discussion of effective exec policy
└── 500–700 word advisory analysis
```

The assignment specifically says the diagram can be **embedded or referenced**, but I'd embed it directly into the report so the grader doesn't have to jump around.

Also include a screenshot showing the diagram on your VM, because the assignment requires screenshots demonstrating that the work actually ran/existed in the VM; screenshots supplement rather than replace your raw evidence.

---

## Your Task 4 checklist

If I were you, I'd work through it in this exact order:

```text
[ ] 1. Run openclaw exec-policy show
[ ] 2. Save output to evidence/task4-exec-policy.txt

[ ] 3. Write down the actual webpage-summary data flow
[ ] 4. Identify 4+ assets
[ ] 5. Identify 3+ principals
[ ] 6. Identify 4+ trust boundaries
[ ] 7. Identify 6 threats
[ ] 8. Assign >=1 control to every threat
[ ] 9. Explain exec-policy at the tool boundary

[ ] 10. Create the data-flow diagram
[ ] 11. Export it as attack-surface-map.pdf
[ ] 12. Save screenshot/evidence of it

[ ] 13. Choose an approved OpenClaw advisory
[ ] 14. Read the advisory
[ ] 15. Read the fix PR/commit/diff
[ ] 16. Identify attacker-controlled input
[ ] 17. Identify preconditions
[ ] 18. Identify root cause
[ ] 19. Identify impact
[ ] 20. Explain the fix
[ ] 21. Design one regression test
[ ] 22. Decide required/helpful/irrelevant for prompt injection
[ ] 23. Write 500–700 words in advisory-analysis.md

[ ] 24. Put Task 4 material into report.pdf
[ ] 25. Commit everything to Git
```

The **first thing I'd do now** is the threat model rather than the advisory. Your Task 3 work has already given you almost everything you need: you know the data path, the direct-vs-indirect distinction, the `safe-marker` boundary, and your actual exec policy. Task 4 is basically asking you to zoom out and draw the security architecture around the experiment you just performed.

---

## User

Export and format our entire conversation so far as a clean Markdown (.md) code block or downloadable file.