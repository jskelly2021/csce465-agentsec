# HW 2 AI Usage Statement

## Assignment Planning

**Tool/model and date:**
ChatGPT, GPT-5.6, Sep 24

**Purpose:**
Break the assignment into tasks and create soft deadlines to stay on track.

**AI Conversation Log files:**
ai_logs/create_work_plan.md

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
