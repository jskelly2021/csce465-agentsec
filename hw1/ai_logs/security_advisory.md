# OpenClaw Security Advisory Discussion

## User

I need help identifying security advisories for openclaw. I want to write my analysis on a security vulnerability that I understand enough. Look through potential options.

## Assistant

I looked through the assignment requirements and a solid spread of OpenClaw advisories. For **Task 4**, you want something with a clean causal chain you can explain yourself: **attacker input → vulnerable code → security boundary failure → impact → patch → regression test**. That maps almost exactly to what your professor asks for.

One weird thing I noticed: the PDF says “pick one advisory from the shortlist below,” but the rendered PDF never actually includes a shortlist. It jumps directly to the Bonus Task section. So if there’s a separate Canvas/LMS shortlist, check that before committing; otherwise, the PDF says a different current advisory needs instructor approval.

Here are the options I think are most worth considering:

| Advisory | Core idea | Difficulty | Prompt injection? | My take for your report |
|---|---|---:|---|---|
| **GHSA-qrq5-wjgg-rvqw — Plugin Installation Path Traversal** | Malicious `package.json` name causes installation outside the extensions folder | **Easy** | Irrelevant | **Excellent choice** |
| **GHSA-p25h-9q54-ffvw — Zip Slip TAR Extraction** | `../../` paths inside an archive escape the extraction folder | **Very easy** | Irrelevant | **Probably easiest overall** |
| **GHSA-r39h-4c2p-3jxp — `setup-api.js` loaded from CWD** | OpenClaw accidentally treats the current repo as trusted executable code | **Easy–medium** | Irrelevant | **Best “interesting” choice** |
| **GHSA-wfp2-v9c7-fh79 — Attachment SSRF** | Attacker-controlled URL makes OpenClaw fetch internal resources | **Medium** | Helpful, not required | Very good agent-security topic |
| **GHSA-56pc-6hvp-4gv4 — `$include` arbitrary file read** | Config path traversal reads files outside intended directory | **Easy** | Irrelevant | Clean but somewhat basic |
| **GHSA-vffc-f7r7-rx2w — systemd newline injection** | Newline in env value injects a systemd directive / command | **Medium** | Irrelevant | Good if you like command injection |
| **GHSA-rv39-79c4-7459 — Gateway device identity bypass** | Code trusts presence of token before it has actually been validated | **Medium–hard** | Irrelevant | Good security concept, more architecture to learn |
| **GHSA-g27f-9qjv-22pm — Log poisoning** | HTTP/WebSocket headers become indirect LLM instructions through logs | **Medium** | **Central** | Interesting but harder to argue impact cleanly |

### The three I'd focus on

**1. Plugin installation path traversal — GHSA-qrq5-wjgg-rvqw**

This is probably the safest choice based on what you've already been working through. OpenClaw used the plugin's `package.json` `name` to derive its installation directory. A crafted scoped name could produce `..`, causing the destination to escape the extensions directory. Exploitation requires the victim to install attacker-controlled plugin content. The fix validates the derived installation path and rejects traversal/reserved identifiers.

The whole vulnerability can almost be drawn as:

```text
Attacker controls plugin
        ↓
package.json
name = "@malicious/.."
        ↓
OpenClaw derives directory name
        ↓
path.join(extensionsDir, "..")
        ↓
destination escapes extensions/
        ↓
files written somewhere they shouldn't be
```

Your regression test is also obvious: feed the installer a malicious plugin name and assert installation is rejected and **nothing outside `extensionsDir` changes**.

This gives you plenty to discuss in 500–700 words without requiring you to learn a giant subsystem.

---

**2. Zip Slip TAR extraction — GHSA-p25h-9q54-ffvw**

This may actually be the **easiest vulnerability technically**.

OpenClaw's `extractArchive()` extracted TAR files into a destination directory, but vulnerable versions did not sufficiently reject absolute or traversal entry paths. An archive entry such as `../../something` could therefore escape the intended directory. The affected extraction code was used by plugin and hook installation.

Conceptually:

```text
destination/
    normal.txt

malicious.tar:
    ../../outside.txt
```

The programmer thinks:

```text
extract everything into destination/
```

but the filesystem resolves:

```text
destination/../../outside.txt
```

and the file lands outside the boundary.

That's classic **CWE-22 path traversal**, and the attacker-controlled input, root cause, impact, fix, and regression test are all extremely clean.

The only drawback is that it's almost *too* conventional—it doesn't really showcase anything special about AI agents. That's not a grading problem from what your assignment says, though.

---

**3. `setup-api.js` from CWD — GHSA-r39h-4c2p-3jxp**

This one is my favorite if you want something a little more interesting without becoming miserable.

OpenClaw's provider/plugin setup resolver could use `process.cwd()` as a fallback location when looking for a `setup-api.js`. That means if you cloned or entered a malicious repository containing something like:

```text
malicious-project/
└── extensions/
    └── some-plugin/
        └── setup-api.js
```

and then ran an otherwise ordinary OpenClaw provider/model command from that directory, OpenClaw could load the JavaScript.

The fundamental mistake isn't really “JavaScript is unsafe.” It's **trusting the current working directory as though it were an OpenClaw-owned code location**.

The patch is beautifully understandable: stop searching `process.cwd()` for bundled setup modules and only resolve them relative to the canonical OpenClaw package/repository root. The advisory even says the regression test verifies that a workspace-local `setup-api.js` is not loaded.

That's a really nice root-cause sentence for your eventual paper:

> OpenClaw confused an attacker-controlled workspace path with a trusted application code path.

That's a genuine **trust-boundary failure**, which fits your course extremely well.

### Ones I'd be more hesitant about

The **gateway authentication bypass** you've already been investigating is legitimate and interesting, but you have to correctly explain shared-secret authentication, Tailscale authentication, device pairing, the WebSocket handshake, and exactly when `auth.token` changes from merely supplied to actually validated. The bug itself is elegant—**presence of credentials was treated like successful authentication**—but there are more moving pieces.

The **log-poisoning vulnerability** is also cool given Task 3, but it creates a weaker cause-and-effect story. Attacker sends malicious WebSocket headers → headers enter logs → some later AI-assisted debugging workflow reads those logs → the LLM may interpret them as instructions. That's absolutely indirect prompt injection, but there are several conditional steps between the vulnerability and actual harm. It can be harder to fill the “impact” section without overstating what the vulnerability guarantees.

**SSRF through attachment hydration** is a nice middle ground. OpenClaw could be induced to fetch an attacker-controlled HTTP URL from the gateway machine; because that machine can potentially access `localhost`, private networks, or metadata services, the attacker could potentially access resources unavailable from outside. The vulnerable implementation effectively performed a raw fetch without the later SSRF protections. It's a good topic, but you'll need to understand loopback/private addresses, DNS/redirect protections, and why server-side requests are different from requests made by the attacker.

### Where I'd land

Based on the vulnerabilities you've already been asking me about, I'd narrow it to:

**Want the easiest analysis:** **Zip Slip — GHSA-p25h-9q54-ffvw**

**Want an easy vulnerability with a little more substance:** **Plugin installation path traversal — GHSA-qrq5-wjgg-rvqw**

**Want the most interesting one while still being very understandable:** **`setup-api.js` from CWD — GHSA-r39h-4c2p-3jxp**

I think **`setup-api.js` from CWD is the sweet spot for you**. It's not buried in authentication architecture, the security boundary is extremely clear, the impact is real arbitrary code execution, the patch is straightforward, and the regression test basically writes itself. It also gives you more to talk about conceptually than “someone forgot to sanitize `../`.”

If you want to optimize strictly for **“I need to be able to explain every sentence of this to my professor at checkoff,”** though, I'd go with the **plugin path traversal** you've already started investigating.

---

## User

Explore this option further:

Plugin Installation Path Traversal

What is the vulnerability? What is impact, and what is the fix?

## Assistant

Yep — this is a pretty clean vulnerability to understand because there’s no AI-model weirdness involved. It’s a classic **path traversal caused by trusting an attacker-controlled package name when constructing a filesystem path**.

### What is the vulnerability?

OpenClaw plugins are installed under an extensions directory, conceptually something like:

```text
~/.openclaw/
└── extensions/
    ├── plugin-a/
    └── plugin-b/
```

When OpenClaw installed a plugin, it read the plugin’s `package.json` and used the package’s `name` to decide what directory to create.

Normally:

```json
{
  "name": "@example/weather-plugin"
}
```

might eventually produce an installation directory resembling:

```text
~/.openclaw/extensions/weather-plugin/
```

The problem was that **the package name came from the plugin being installed**, so an attacker who created a malicious plugin could control that value. OpenClaw did not adequately validate the resulting plugin ID before using it as part of a filesystem path.

A malicious package could use a name such as:

```json
{
  "name": "@evil/.."
}
```

OpenClaw's package-name handling stripped the npm scope:

```text
@evil/..
     ↓
..
```

and the vulnerable installer effectively ended up doing something equivalent to:

```js
path.join(extensionsDir, "..")
```

If:

```text
extensionsDir = /home/jacob/.openclaw/extensions
```

then:

```text
path.join("/home/jacob/.openclaw/extensions", "..")
```

resolves to:

```text
/home/jacob/.openclaw
```

So instead of copying the plugin into:

```text
.openclaw/extensions/plugin-name/
```

the installer could copy files **outside the directory it was supposed to be confined to**.

That's **CWE-22: Path Traversal**.

### Why didn't the original sanitization stop it?

This is one of the more useful parts to understand.

The old code had a function resembling:

```ts
function safeDirName(input: string): string {
    const trimmed = input.trim();
    if (!trimmed) {
        return trimmed;
    }

    return trimmed.replaceAll("/", "__");
}
```

At first glance, that sounds like protection against path traversal: replace `/` so someone can't supply something like:

```text
../../etc
```

But the problem happened **after processing the npm package name**.

For:

```text
@evil/..
```

the package-name logic produced:

```text
..
```

Now `safeDirName()` sees:

```text
..
```

There are no `/` characters to replace.

So:

```text
safeDirName("..")
```

still returns:

```text
..
```

And `..` has special meaning to the filesystem.

That is the root cause in a nutshell:

> **OpenClaw sanitized path separators but failed to validate that the resulting plugin identifier was a safe directory name or that the final resolved destination remained inside the extensions directory.**

### What does an attacker need?

This isn't a vulnerability where someone on the Internet can spontaneously overwrite an OpenClaw machine.

The victim/operator has to install attacker-controlled plugin content, such as by running:

```bash
openclaw plugins install <malicious-plugin>
```

The malicious plugin contains the crafted `package.json`.

So the flow is:

```text
Attacker creates malicious plugin
        ↓
package.json contains malicious name
        ↓
Victim installs plugin
        ↓
OpenClaw reads attacker-controlled name
        ↓
name becomes ".."
        ↓
OpenClaw calculates installation directory
        ↓
path resolves outside extensions/
        ↓
plugin files are written outside intended boundary
```

That user interaction is an important **precondition** for your report.

### What is the impact?

The direct impact is **unauthorized filesystem writes outside the plugin directory**.

OpenClaw intended the plugin installer to have this authority:

```text
~/.openclaw/extensions/
                    ↓
              write here only
```

But the vulnerability could turn that into:

```text
~/.openclaw/
    ↑
    plugin installer can unexpectedly write here
```

For the documented POSIX example, the malicious `..` can cause files to land in OpenClaw's state directory rather than inside `extensions/`. That could allow the malicious installation to overwrite or tamper with files OpenClaw relies on.

One distinction I'd preserve in your eventual report: **don't automatically call this arbitrary code execution.** The demonstrated vulnerability is arbitrary/unintended **file placement outside the expected installation directory**. Depending on which file can be replaced and how OpenClaw later uses it, that could potentially contribute to more serious effects, but that's a separate claim you'd need evidence for.

Windows had another wrinkle. The vulnerable sanitizer only replaced forward slashes:

```ts
replaceAll("/", "__")
```

but not Windows backslashes:

```text
\
```

This could permit deeper traversal through crafted plugin IDs on Windows, still limited by the privileges of the user running OpenClaw.

### What was the fix?

The patch takes a **defense-in-depth** approach rather than just trying to remove one bad character.

First, it explicitly validates plugin IDs. The new logic rejects:

```text
""
"."
".."
```

and IDs containing:

```text
/
\
```

Conceptually:

```ts
if (pluginId === "." || pluginId === "..") {
    reject();
}

if (pluginId.includes("/") || pluginId.includes("\\")) {
    reject();
}
```

The patch also updated the directory sanitizer to handle both Unix `/` and Windows `\` separators.

But the most important improvement is the **final containment check**.

Instead of assuming a sanitized name creates a safe path, the code now calculates the final path and verifies that it actually remains underneath the extensions directory.

Conceptually:

```text
base:
~/.openclaw/extensions

candidate:
~/.openclaw/extensions/weather
```

Then calculate:

```text
relative(base, candidate)
```

For a legitimate plugin:

```text
weather
```

Good.

For an escaping target:

```text
..
```

or:

```text
../something
```

Bad → reject installation.

The actual patch uses `path.resolve()` and `path.relative()` and rejects cases where the relative path is `..`, begins with `../`, is absolute, or otherwise doesn't represent a proper child of the extensions directory.

That second defense is especially important because it protects the **security property you actually care about**:

> Regardless of the input string, the final plugin installation directory must be contained inside the configured extensions directory.

### The regression test is unusually clean

This vulnerability is also nice for your assignment because the patch basically hands you the regression test.

The developers added a test creating a plugin with:

```json
{
  "name": "@evil/..",
  "version": "0.0.1",
  "openclaw": {
    "extensions": ["./dist/index.js"]
  }
}
```

They package it into an archive and call the plugin installer.

The expected result is:

```text
installation fails
```

with an error containing:

```text
reserved path segment
```

The fix also adds a similar test for:

```json
"name": "@evil/."
```

For your report, you could phrase the regression test very simply:

> Construct a valid OpenClaw plugin archive whose `package.json` contains the scoped name `@evil/..`. Attempt installation into a temporary extensions directory. Verify that installation fails and that no plugin files are created outside the extensions directory.

### Prompt injection?

**Irrelevant.**

No LLM has to be tricked.

There is no:

```text
malicious text
→ model interprets instruction
→ tool invocation
```

Instead:

```text
malicious package metadata
→ vulnerable application code
→ unsafe filesystem path
```

That's ordinary software exploitation.

And that contrast is actually useful given the rest of your homework, since Task 4 explicitly asks you to say whether prompt injection is required, helpful, or irrelevant.

The cleanest one-sentence summary I'd keep in your notes is:

> **OpenClaw trusted an attacker-controlled plugin package name when deriving its installation path, allowing a specially crafted name such as `@evil/..` to cause the resolved destination to escape the extensions directory; the fix rejects unsafe plugin IDs and verifies that the final resolved path remains inside the extensions directory.**

This one is very workable for the assignment because you can explain the actual buggy behavior **and** the actual patch without hand-waving.

---

## User

Explore this option further:

GHSA-r39h-4c2p-3jxp — `setup-api.js` loaded from CWD

What is the vulnerability? What is impact, and what is the fix?

## Assistant

This one is a bit more interesting than the path traversal because the security failure is fundamentally about a **trust boundary**: OpenClaw accidentally treated the directory you happened to run it from as a trusted place to load executable JavaScript.

The advisory is **GHSA-r39h-4c2p-3jxp**, affecting OpenClaw versions before `2026.4.23`; it was fixed in `2026.4.23`.

### What is the vulnerability?

OpenClaw supports plugins/providers that can expose setup information through a file named `setup-api.js`. During operations such as resolving provider configuration or model/provider status, OpenClaw may need to locate one of these setup modules.

The vulnerable function, `resolveSetupApiPath()`, built a list of places where it was willing to look for that module. Before the patch, that list effectively included:

```ts
const repoRootCandidates = [
    canonicalOpenClawRoot,
    process.cwd(),
];
```

`process.cwd()` means **the current working directory of the user who launched OpenClaw**. The code would then construct something conceptually like:

```text
<candidate>/extensions/<plugin>/setup-api.js
```

and, if the file existed, load it as JavaScript.

That creates a nasty situation. Imagine an attacker publishes a malicious repository:

```text
cool-project/
├── README.md
├── src/
└── extensions/
    └── workspace-shadow/
        └── setup-api.js
```

You clone it:

```bash
git clone ...
cd cool-project
```

At this point:

```js
process.cwd()
```

is:

```text
/home/jacob/cool-project
```

If you then run an affected OpenClaw command that triggers provider/setup resolution, OpenClaw could discover:

```text
/home/jacob/cool-project/extensions/workspace-shadow/setup-api.js
```

and execute it.

The important distinction is that **you did not intentionally install that file as an OpenClaw plugin**. You merely ran OpenClaw while your shell happened to be inside the malicious repository.

### Why is that a security vulnerability?

The current working directory is fundamentally **untrusted input**.

If you run:

```bash
cd ~/Downloads/random-github-project
openclaw ...
```

OpenClaw should assume files under:

```text
~/Downloads/random-github-project
```

belong to that project.

Instead, the vulnerable resolver effectively treated that directory as though it might be part of OpenClaw's own trusted source tree.

You can think of the intended trust model as:

```text
Trusted OpenClaw installation
    ↓
extensions/plugin/setup-api.js
    ↓
execute JavaScript
```

but the bug allowed:

```text
Untrusted repository
    ↓
extensions/plugin/setup-api.js
    ↓
OpenClaw mistakes it for trusted setup code
    ↓
execute attacker JavaScript
```

That's the core root cause:

> **OpenClaw included an attacker-controlled filesystem location, `process.cwd()`, in a search path for trusted executable plugin setup modules.**

That's a much stronger explanation than simply saying "OpenClaw loaded a malicious file."

### Why would OpenClaw execute `setup-api.js` at all?

The file isn't supposed to just be data like JSON. It's a JavaScript module containing plugin/provider setup logic.

That's fine when the module comes from:

```text
OpenClaw's trusted installation
```

The vulnerability arises because **the resolver chose the wrong source location**.

In other words, the problem isn't:

```text
OpenClaw executes JavaScript
```

That's expected.

It's:

```text
OpenClaw executes JavaScript
FROM A LOCATION THE ATTACKER CAN CONTROL
```

### What does the attacker need?

There is still user interaction involved. The attacker cannot simply contact an OpenClaw Gateway over the Internet and trigger this vulnerability.

The attack requires roughly:

```text
Attacker creates malicious repository
        ↓
repository contains extensions/<plugin>/setup-api.js
        ↓
victim downloads/clones repository
        ↓
victim enters repository
        ↓
victim runs vulnerable OpenClaw command
        ↓
provider/setup resolution occurs
        ↓
OpenClaw searches process.cwd()
        ↓
attacker's setup-api.js gets loaded
```

That precondition is important for your report: **the attacker needs to convince the victim to run OpenClaw from attacker-controlled directory contents.**

### What's the impact?

This is much more severe than the plugin path traversal you were looking at earlier.

The advisory describes the impact as **arbitrary JavaScript execution in the OpenClaw process under the current user's account**.

If malicious JavaScript runs inside a normal Node/OpenClaw process, it inherits whatever permissions that OpenClaw process has.

Conceptually, malicious setup code could act with access available to that user/process, potentially affecting:

```text
User-accessible files
OpenClaw configuration/state
Environment variables visible to OpenClaw
Network resources accessible to the process
Other resources available to that OS user
```

You shouldn't describe it as root/system compromise unless OpenClaw itself happens to be running with those privileges. The accurate statement is:

> The attacker gains code execution with **the permissions of the user running OpenClaw**.

That's still extremely serious.

### The fix is surprisingly small

This is what makes the vulnerability especially nice for your analysis.

The vulnerable code effectively had:

```ts
const repoRootCandidates = [
    path.resolve(path.dirname(CURRENT_MODULE_PATH), "..", ".."),
    process.cwd(),
];
```

The patch changed it to:

```ts
const repoRootCandidates = [
    path.resolve(path.dirname(CURRENT_MODULE_PATH), "..", "..")
];
```

So OpenClaw stopped considering the CWD a trusted fallback location entirely.

Now setup fallbacks are resolved only relative to OpenClaw's **canonical package/repository root**.

Before:

```text
Where should I search for trusted setup-api.js?

1. OpenClaw installation        ✓ trusted
2. wherever the user is        ✗ potentially attacker-controlled
```

After:

```text
Where should I search?

1. OpenClaw installation        ✓
```

That's exactly the right kind of fix because it restores the intended trust boundary rather than attempting to inspect malicious JavaScript and decide whether it's safe.

### The regression test is also very understandable

The patch adds a test specifically named:

```text
does not load setup-api modules from the current working directory
```

The test creates:

```text
temporary-workspace/
└── extensions/
    └── workspace-shadow/
        └── setup-api.js
```

It then mocks:

```js
process.cwd()
```

to point at that malicious workspace and runs provider setup resolution.

The expected result is:

```text
no provider returned
setup module loader never called
```

Specifically, the test asserts that the JavaScript loader wasn't invoked at all.

For your assignment, a good regression-test description would be:

> Create a temporary working directory containing `extensions/<plugin>/setup-api.js`, set it as the process's current working directory, and trigger provider setup resolution. Verify that the resolver does not load or execute the workspace-local module.

### Is prompt injection involved?

**No. Prompt injection is irrelevant.**

There doesn't even need to be a meaningful LLM interaction.

This isn't:

```text
Attacker text
→ LLM follows malicious instruction
→ LLM invokes tool
→ compromise
```

It's:

```text
Attacker-controlled filesystem
→ OpenClaw searches unsafe directory
→ OpenClaw loads JavaScript
→ JavaScript executes
```

So this is a traditional **software/code-loading vulnerability**, rather than an LLM prompt-injection vulnerability.

The sentence I'd keep at the center of your notes is:

> **OpenClaw mistakenly treated `process.cwd()`—which may point to attacker-controlled repository contents—as a trusted source for executable plugin setup modules. As a result, running certain OpenClaw commands from a malicious repository could cause arbitrary JavaScript in `extensions/<plugin>/setup-api.js` to execute with the privileges of the OpenClaw user. The fix removed the current working directory from the trusted setup-module search path.**

This is actually a **very strong Task 4 candidate** because the root cause, trust boundary, impact, patch, and regression test are all unusually easy to trace directly through the code.

---

## User

What are high level examples of what the malicous code could do?

## Assistant

At a high level, once that malicious `setup-api.js` is executed, it can do **whatever the OpenClaw process is allowed to do as that user**.

Examples include:

- **Read files** the user can access, such as OpenClaw config files, project files, logs, or local documents.
- **Modify or delete files**, which could corrupt projects, alter OpenClaw settings, or break the application.
- **Read environment variables**, which may contain API keys, tokens, or other secrets passed into the OpenClaw process.
- **Make network requests**, such as sending data to an attacker-controlled server or contacting internal services reachable from the machine.
- **Run local commands or programs** through Node's OS/process capabilities, subject to the user's permissions.
- **Tamper with OpenClaw state**, plugins, configuration, or cached data.
- **Create additional files or startup hooks** in locations writable by the user, potentially giving the attacker a way to keep code around after the initial execution.
- **Use the victim's identity/permissions** to access resources that are available to that logged-in account.

The key constraint is important:

> The malicious code does **not automatically become root**. It runs with the same privileges as the OpenClaw process.

So if OpenClaw is running as a normal user, the attacker generally gets that user's level of access. If OpenClaw were run with elevated privileges, the impact could be much worse.

For your writeup, I'd phrase the impact like this:

> Successful exploitation allows arbitrary JavaScript execution in the OpenClaw process. The malicious code could read or modify user-accessible files, access environment variables and OpenClaw configuration, make network requests, or execute local commands, limited by the privileges of the account running OpenClaw.

That keeps the impact strong without claiming capabilities the advisory doesn't specifically prove.

---

## User

Export and format our entire conversation so far as a clean Markdown (.md) code block or downloadable file.
