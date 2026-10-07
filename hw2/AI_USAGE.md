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

## Task 3 — Encrypt-then-MAC Secure Record Layer

**Tool/model and date:**
ChatGPT, GPT-5.6 Sol, Oct 6

**Purpose:**
Break down the Task 3 requirements, plan the structure of the secure record layer, and understand how to implement `seal()` and `open_record()` using the session keys established during Task 2.

**AI Conversation Log files:**
ai_logs/task3_plan.md
ai_logs/task3_bug_review.md
ai_logs/task3_report_structure.md

**What I used:**
The breakdown of the required record format, guidance on storing send and receive sequence numbers and directions in each session, examples of AES-256-CTR encryption and HMAC-SHA-256 authentication, guidance on parsing and validating records in `open_record()`, and debugging print statements for inspecting record construction.

**What I changed:**
I adapted the examples to my existing `Session` structure and `handshake.py` implementation. I added send and receive directions and sequence numbers directly to each session, organized the record-processing logic into helper functions, and wrote my own `secure_record.py` implementation around the established session keys.

**How I tested it:**
I manually established Gateway and Node sessions using the Task 2 handshake, sealed a plaintext message using the Gateway session, opened it using the Node session, and checked the record fields, ciphertext, HMAC, sequence numbers, and recovered plaintext through debug output. Additional adversarial behavior will be tested with automated tests in Task 4.

**One error, limitation, or rejected suggestion:**
The AI initially suggested creating a separate `RecordLayer` object to store sequence numbers and directions. I instead kept this state directly in the existing `Session` object because each endpoint already has its own session containing separate send and receive keys, making the additional layer unnecessary for my implementation.

## Task 4 — Adversarial Tests and Security Note

**Tool/model and date:**  
ChatGPT, GPT-5.6 Sol, Oct 6

**Purpose:**  
Break down the Task 4 requirements into actionable steps, understand the required adversarial tests, determine the expected safe failure for each attack, and plan the required security note.

**AI Conversation Log files:**  
ai_logs/task4_plan.md
ai_logs/task4_pytest_explaination.md

**What I used:**  
The suggested pytest structure and fixtures, examples for testing valid bidirectional communication, modified ciphertext, modified authenticated headers, replayed records, reflected records, and an incorrect RSA public key. I also used the explanation of what constitutes a specific safe failure and the outline of topics required for the security note.

**What I changed:**  
I adapted the example tests to my existing `handshake.py` and `secure_record.py` implementation, including my session structure, exception classes, record format, and ordering of validation checks.

**How I tested it:**  
I will run the automated tests with `pytest -v` in the course VM and verify that valid records are accepted while each adversarial case raises the expected specific exception without releasing plaintext or establishing an invalid session.

**One error, limitation, or rejected suggestion:**  
The AI initially suggested that a reflected record should raise `AuthenticationError` because it assumed HMAC verification occurred before the direction check. My current `open_record()` implementation checks the record direction before verifying the HMAC, so a reflected record should instead fail with `DirectionError`. I adjusted the expected test result to match my implementation.
