# OpenClaw Security Advisory Analysis

[Security Advisory](https://github.com/openclaw/openclaw/security/advisories/GHSA-r39h-4c2p-3jxp)

GHSA-r39h-4c2p-3jxp

Arbitrary code execution via attacker-controlled setup-api.js loaded from cwd during env-key resolution

**Affected Versions**: <2026.4.23

**Severity**: High

During plugin setup, OpenClaw may need to access provider setup metadata typically exposed in a file named setup-api.js. OpenClaw defines a list of places where it is allowed to look for the setup information. In the vulnerable version, this list included the current working directory (cwd) of the user where OpenClaw was launched. OpenClaw blindly trusts the current working directory which opens the door for code injection in an attacker controlled environment. Code injection is an attack in which a bad actor attempts to force a victim to execute unauthorized commands or scripts. Because OpenClaw is known to search for and execute setup-api.js, attackers can write malicious code in this file and force OpenClaw to execute it.

The exploit requires that the attacker controls and has access to a repository and creates a file named extensions/<plugin>/setup-api.js. This file is typically used to resolve provider metadata and establish plugin settings; however, this file serves as the primary payload used in the attack and contains executable Javascript code. With the environment setup, the attacker must get an unknowing user to download or clone the repo. The user then must run an OpenClaw command that triggers the plugin setup location resolution potentially causing OpenClaw to discover the malicious file and execute it. 

Because this code is executed in the OpenClaw process, it executes under the user with the same permissions as the OpenClaw process. This means the malicious script could read, modify, create, or delete files, make network requests to an attacker controlled server, or execute other commands. Thankfully, the exploit is scoped in its reach, as it is local only and requires user interaction. However, these operations can still be potentially harmful and lead to privilege escalation and system compromise, theft of data, or even allow an attacker to install other malicious software.

In the end, the root cause of this vulnerability is due to OpenClaw incorrectly trusting the user by accepting the current working directory as a candidate location to search for and execute scripts. The current working directory may potentially be controlled by the user and should be treated as an untrusted source. While the choice to trust the cwd was a mistake, OpenClaw correctly implemented an allow list, as opposed to a deny list which limited the affected surface.

The fix to this exploit is to disallow OpenClaw from searching for and executing plugin setup scripts from the current working directory. The fix commit supports this perspective, as it removes process.cwd() from its list of allowed search candidates. To test this fix, the malicious repository containing extensions/<plugin>/setup-api.js must first be reproduced. Using this repository as the current working directory, trigger the plugin setup location resolution and verify that OpenClaw did not look for setup-api.js in the current working directory. If OpenClaw does not load setup-api.js from the cwd, the fix is successful; otherwise, the fix is invalid.

Prompt injection is irrelevant for this vulnerability, as no LLM interactions are involved.
