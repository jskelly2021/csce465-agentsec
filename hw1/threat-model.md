# Threat Model

## Assets

1. Model Input. User prompt and retrieved external content.
2. HTML web page.
3. The Agent context. User prompt + external content + skill and tool definitions.
4. Model response. Includes tool call decisions.

## Principals

1. User
2. OpenClaw Gateway/Agent
3. Model Provider

## Trust Boundaries

1. User - Web Server
2. User - OpenClaw Gateway
3. Agent Runtime Context - Model Provider
4. Skill/Tool Decision Authorization - OS

## Threats

### 1. Direct Prompt Injection

**Prevention/Detection**

Do not trust user input. Require authorization for tool use.

### 2. Indirect Prompt Injection

**Prevention/Detection**

Never trust external content. The system should separate user instructions from retrieved content.

### 3. Altered skill/tool file

**Prevention/Detection**

Use least privilege access. Review skills before use and require authorization for tool use.

### 4. Sensitive data leakage to model provider

**Prevention/Detection**

Never expose sensitive data. Redact secrets, use fake data, or use a local model. 

### 5. Unauthorized tool execution

**Prevention/Detection**

Require human confirmation for high risk tool calls.

### 6. Malicious code execution

**Prevention/Detection**

Use sandboxing and least privilege.
