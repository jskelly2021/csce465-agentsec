# HW 2 AI Usage Statement

## Assignment Planning

**Tool/model and date:**
ChatGPT, GPT-5.6, Sep 24

**Purpose:**
Break the assignment into tasks and create soft deadlines to stay on track.

**AI Conversation Log files:**
ai_logs/hw_work_plan.md

**What I used:**
The suggested workplan.

**What I changed:**
I reviewed the HW description independently.

**How I tested it:**
Used for planning only.

**One error, limitation, or rejected suggestion:**
I verified the assignment requirements against the HW description.

## Task 1 — AES-CTR Bit-Flipping and Replay

**Tool/model and date:**
ChatGPT, GPT-5.6 Sol, Oct 3

**Purpose:**
Clarify the Task 1 requirements, review AES-CTR encryption and decryption with the Python cryptography library, and understand the ciphertext bit-flipping and replay demonstrations.

**AI Conversation Log files:**
ai_logs/task1_aes_ctr_conversation.md

**What I used:**
The explanation of AES-CTR encryption/decryption, the XOR relationship used to modify ciphertext, guidance on the relay function, the XOR output helper function, and clarification of the replay experiment.

**What I changed:**
I adapted the examples to my own `baseline_ctr.py` implementation and reviewed the Task 1 requirements independently.

**How I tested it:**
I compared the proposed design against the assignment requirements and will verify the implementation by running `baseline_ctr.py` in the course VM and checking the bit-flip and replay output.

**One error, limitation, or rejected suggestion:**
I initially interpreted replay as forwarding the original and modified ciphertexts. The AI clarified that replay requires sending the exact same ciphertext more than once, and I corrected my design accordingly.

## Task 2 — Authenticated Diffie–Hellman Handshake

**Tool/model and date:**
ChatGPT, GPT-5.6 Sol, Oct 4–5

**Purpose:**
Clarify the Task 2 requirements and design an authenticated Diffie–Hellman handshake between a simulated gateway and node. I also used AI to understand the canonical transcript, RSA-PSS authentication, ephemeral DH key exchange, session key derivation, and the responsibilities of the Gateway, Node, and Session objects. Generate code for task 2 completion.

**AI Conversation Log files:**
ai_logs/task2_plan.md  
ai_logs/task2_understanding.md  
ai_logs/task2_code_gen.md  
ai_logs/task2_bug_review.md

**What I used:**
I used explanations and code guidance for loading the `ffdhe3072` parameters, generating ephemeral DH keys and nonces, representing the Gateway and Node, constructing and hashing the length-prefixed transcript, signing and verifying `role || SHA-256(transcript)` with RSA-PSS, computing the DH shared secret, and deriving the required directional encryption/MAC keys and session identifier. I also used clarification about which values belong to each party internally versus which values represent exchanged handshake data.

**What I changed:**
I adapted the suggested structure and examples to my own `handshake.py` implementation, including my own Party/Gateway/Node and Session organization, helper functions, naming, validation, and program output. I reviewed the required transcript fields and assignment-specific KDF against the homework specification rather than copying an alternative protocol design.

**How I tested it:**
I ran the handshake in the course VM and checked that both parties construct the same transcript hash, independently compute the same Diffie–Hellman shared secret, verify each other's RSA-PSS signatures, and derive matching session keys and session identifier. I also used invalid or modified handshake values to verify that authentication failures are rejected as required.

**One error, limitation, or rejected suggestion:**
I initially thought Task 2 required reimplementing the Diffie–Hellman setup itself. The AI clarified that the maintained cryptography library should perform the DH arithmetic and that my responsibility is to implement the authenticated handshake protocol around it, including the transcript, signatures, identity checks, and key derivation.
