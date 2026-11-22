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
