# CSCE 465 — HW4 Task 4 Suricata Conversation Log

**Date:** November 22, 2026  
**Tool/model:** ChatGPT (GPT-6)  
**Topic:** Task 4 — Suricata intrusion-detection rules and evaluation

> **Note:** This Markdown log captures the questions, substantive guidance, example rules, and testing commands from this conversation. Some long-form explanations are condensed for readability. Suggested tests and expected results should not be confused with verified results.

---

## Exchange 1 — Task 4 Breakdown

**User:**

> @HW4.pdf Breakdown task 4. What steps are required to complete it. What outputs do I need to record?

**Assistant:**

### Overview

Task 4 (30 points) requires three Suricata IDS rules in `local.rules` and offline testing against the Task 2 captures, `hw4-malicious.pcap` and `hw4-clean.pcap`.

Write exactly three signatures:

1. **Fake-secret exfiltration:** Detect the unique fake token in an outbound HTTP request body.
2. **Indirect prompt-injection marker:** Detect `CSCE465-COURSE-MARKER` in the HTTP response body sent from `web-lab` to `agent-node`.
3. **Known mock-C2 connection:** Detect a TCP connection from `agent-node` (`172.30.0.10`) to `mock-c2` (`172.30.0.66:8080`).

Each rule needs a unique SID, an alert message (`msg`), revision (`rev`), appropriate traffic direction, and suitable flow or HTTP matching options.

### Procedure

1. Verify the two Task 2 PCAP files exist:

   ```bash
   ls -lh hw4-malicious.pcap hw4-clean.pcap
   ```

2. Create `local.rules` with the three detection signatures.
3. Make output directories:

   ```bash
   mkdir -p suricata-malicious suricata-clean
   ```

4. Analyze both captures:

   ```bash
   suricata -k none -r hw4-malicious.pcap -S local.rules -l suricata-malicious
   suricata -k none -r hw4-clean.pcap -S local.rules -l suricata-clean
   ```

   `-r` specifies the PCAP; `-S` loads only local rules; `-l` identifies the output directory; `-k none` disables checksum checking, which the assignment specifies for Docker bridge PCAPs.

5. Read alerts:

   ```bash
   cat suricata-malicious/fast.log
   cat suricata-clean/fast.log
   ```

6. For each SID and PCAP, classify the result as TP, FP, FN, or TN.

### Outputs to include in `report.pdf`

- The complete three-rule `local.rules` file and explanations of each keyword.
- `fast.log` alerts for the malicious and clean captures (including an empty clean log, if applicable).
- A six-cell TP/FP/FN/TN evaluation table (three rules × two PCAPs).
- One detection limitation, such as encrypted HTTP bodies preventing content inspection without decryption.

The expected ideal evaluation, **subject to actual testing**, is:

| Rule | Malicious PCAP | Clean PCAP |
|---|---|---|
| Fake-secret exfiltration | TP | TN |
| Injection marker | TP | TN |
| Known mock-C2 connection | TP | TN |

The deliverables list specifically includes `local.rules` and `report.pdf`; it does not explicitly require submitting the PCAPs or log directories separately.

---

## Exchange 2 — Understanding Suricata Rules

**User:**

> Help me understand creating the Sericata rules. What do I need to know for this task

**Assistant:**

A Suricata signature is analogous to a conditional statement applied to network traffic. Its general syntax is:

```text
action protocol source_ip source_port -> destination_ip destination_port (options;)
```

Main keywords:

| Keyword | Meaning |
|---|---|
| `alert` | Generate an alert on a match. |
| `tcp` | Inspect TCP traffic. |
| `http` | Inspect recognized HTTP traffic. |
| `any` | Any IP or port in that field. |
| `->` | Match in the given direction. |
| `msg` | Human-readable alert description. |
| `content` | Search for a specified string or byte sequence. |
| `flow` | Filter by connection state and client/server direction. |
| `flags` | Match TCP flags, such as SYN. |
| `sid` | Unique signature ID. |
| `rev` | Revision number. |

### Rule 1 — Fake-secret exfiltration

Match the token that `mock_skill.sh` sends as an HTTP POST body from agent-node to mock-c2.

```suricata
alert http 172.30.0.10 any -> 172.30.0.66 8080 (msg:"HW4 Fake Secret Exfiltration"; flow:established,to_server; http.request_body; content:"YOUR_ACTUAL_FAKE_TOKEN"; sid:1000001; rev:1;)
```

`flow:established,to_server` indicates established client-to-server traffic; `http.request_body` selects the HTTP request body for the following `content` match. Replace the placeholder with the exact value in `fake_secrets.txt`.

### Rule 2 — Indirect prompt-injection marker

Match `CSCE465-COURSE-MARKER` in the HTTP response body from web-lab to agent-node.

```suricata
alert http 172.30.0.40 8000 -> 172.30.0.10 any (msg:"HW4 Indirect Injection Marker"; flow:established,to_client; http.response_body; content:"CSCE465-COURSE-MARKER"; sid:1000002; rev:1;)
```

The response flows from the web server to the client, so this uses `to_client` and `http.response_body`, rather than `to_server` and `http.request_body`.

### Rule 3 — Known C2 connection

Match a TCP connection initiation toward mock-c2:

```suricata
alert tcp 172.30.0.10 any -> 172.30.0.66 8080 (msg:"HW4 Known Mock C2 Connection"; flow:to_server; flags:S; sid:1000003; rev:1;)
```

`flags:S` matches TCP SYN packets. Unlike the first two rules, this one can detect a connection attempt without looking at an HTTP payload. It does not by itself prove data was exfiltrated.

### Incident stages

1. **Adversarial web content received:** Rule 2 detects the marker in an HTTP response.
2. **C2 connection attempted:** Rule 3 detects a SYN to the known endpoint.
3. **Fake secret transmitted:** Rule 1 detects the token in an HTTP POST body.

The key distinction is **application-layer content inspection (Rules 1 and 2)** versus **TCP connection metadata (Rule 3)**. Content matching may fail if the payload changes or becomes encrypted; endpoint detection can continue to see IP/port traffic but may not establish whether a leak occurred.

For syntax validation, use:

```bash
suricata -T -S local.rules
```

Then run the offline PCAP tests and inspect the logs. Intended results are three malicious alerts and none on the clean capture, but verify this rather than assume it.

---

## Exchange 3 — Full Suricata Rules File

**User:**

> Write the full suricata rules file using the rules we discussed

**Assistant:**

Here is the `local.rules` file with exactly three signatures:

```suricata
# Rule 1: Detect fake-secret exfiltration in an HTTP POST body
alert http 172.30.0.10 any -> 172.30.0.66 8080 (msg:"HW4 Fake Secret Exfiltration"; flow:established,to_server; http.request_body; content:"REPLACE_WITH_YOUR_EXACT_FAKE_TOKEN"; sid:1000001; rev:1;)

# Rule 2: Detect the indirect prompt-injection marker in an HTTP response
alert http 172.30.0.40 8000 -> 172.30.0.10 any (msg:"HW4 Indirect Injection Marker"; flow:established,to_client; http.response_body; content:"CSCE465-COURSE-MARKER"; sid:1000002; rev:1;)

# Rule 3: Detect TCP connection attempts from agent-node to mock-c2
alert tcp 172.30.0.10 any -> 172.30.0.66 8080 (msg:"HW4 Known Mock C2 Connection"; flow:to_server; flags:S; sid:1000003; rev:1;)
```

**Required customization:** Replace `REPLACE_WITH_YOUR_EXACT_FAKE_TOKEN` with the actual value shown by:

```bash
cat fake_secrets.txt
```

Validation:

```bash
suricata -T -S local.rules
```

Offline analysis:

```bash
mkdir -p suricata-malicious suricata-clean
suricata -k none -r hw4-malicious.pcap -S local.rules -l suricata-malicious
suricata -k none -r hw4-clean.pcap -S local.rules -l suricata-clean
```

Inspect the results:

```bash
cat suricata-malicious/fast.log
cat suricata-clean/fast.log
```

Expected, **not yet verified in this chat**:

| SID | Detection | Malicious | Clean |
|---|---|---|---|
| 1000001 | Fake-secret exfiltration | Alert | No alert |
| 1000002 | Indirect injection marker | Alert | No alert |
| 1000003 | Known C2 connection | Alert | No alert |

---

## Exchange 4 — Export and AI Usage

**User:**

> Export this conversation to Markdown. Provide an entry for my AI usage. Keep each answer simple and brief.
>
> Tool/model and date:  
> Purpose:  
> AI Conversation Log files:  
> What I used:  
> What I changed:  
> How I tested it:  
> One error, limitation, or rejected suggestion:

**Assistant:** Created this Markdown conversation log and provided a concise AI-use entry separately. Actual rule execution and observed outcomes were not provided in the conversation.
