# HW 4 AI Usage

## Entry 1 - Task 1 Understanding

**Tool/model and date:** ChatGPT (GPT-6), November 19–21, 2026.

**Purpose:** Task 1 guidance, implementation, and Docker configuration.

**AI Conversation Log files:** `task1_conversation.md`

**What I used:** HTML examples, mock skill script, Dockerfile, and Compose configuration.

**What I changed:** Adapted the examples for my lab environment.

**How I tested it:** Docker Compose checks, HTTP requests, and SHA-256 comparison.

**One error, limitation, or rejected suggestion:** AI-generated code required independent testing and verification.

## Entry 2 - Task 2 Guidance and Debugging

**Tool/model and date:** ChatGPT (GPT-6), November 22, 2026.

**Purpose:** Task 2 guidance, TCP listener troubleshooting, and packet reconstruction.

**AI Conversation Log files:** `task2_conversation.md`

**What I used:** Nmap/TShark commands, socat troubleshooting, and reconstruction table formatting.

**What I changed:** Modified mock_skill.sh to run the TCP listener in the foreground and adapted report formatting.

**How I tested it:** Verified TCP 9009 with Nmap/netcat and analyzed the HTTP POST using TShark.

**One error, limitation, or rejected suggestion:** Background socat listener failed to remain accessible; switched to foreground execution.

## Entry 3 - Task 3 Understanding and Guidance

**Tool/model and date:** ChatGPT (GPT-6), November 22, 2026

**Purpose:** Understand Task 3 requirements, iptables, and Docker firewall configuration.

**AI Conversation Log files:** `task3_conversation.md`

**What I used:** Firewall breakdown, iptables explanations, and example scripts.

**What I changed:** Adapted examples to my lab setup 

**How I tested it:** Run the five required firewall verification tests.

**One error, limitation, or rejected suggestion:** Firewall rules may not filter bridged traffic without `br_netfilter`.

## Entry 4 - Task 4 Guidance and Rule Creation

**Tool/model and date:** ChatGPT (GPT-6), November 22, 2026

**Purpose:** Understand and implement Suricata detection rules for Task 4.

**AI Conversation Log files:** `task4_conversation.md`

**What I used:** Three Suricata rules, keyword explanations, and testing commands.

**What I changed:** Customized the rules for my lab, including my unique fake token.

**How I tested it:** Suricata syntax validation and malicious/clean PCAP analysis. Results to be verified.

**One error, limitation, or rejected suggestion:** HTTP body detection cannot inspect encrypted content without decryption.

## Entry 5 - Task 5 Summary Structure

**Tool/model and date:** ChatGPT (GPT-6), November 22, 2026

**Purpose:** Help structure the Task 5 incident summary.

**AI Conversation Log files:** `task5_conversation.md`

**What I used:** Suggested report sections, timeline format, and recommendations.

**What I changed:** Adapted the outline to my incident evidence.

**How I tested it:** Compared the structure against Task 5 requirements.

**One error, limitation, or rejected suggestion:** Example timeline lacked actual packet timestamps.
