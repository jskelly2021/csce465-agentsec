# CSCE 465 Homework 2 — Work Plan Conversation

**Conversation title:** Create Work Plan  
**Date:** September 24  
**Assignment due:** October 4  
**Referenced file:** `HW2-2.pdf` (CSCE 465 Homework 2 assignment handout)

---

## User

Today is September 24th. This assignment is due October 4th. Create a work plan for me to complete this assignment. Give me soft deadlines to help me stay on track. I would like to submit before the deadline.

I may need to start by reviewing the textbook material.

**Attachment:** `HW2-2.pdf`

---

## Assistant

Yep — starting with the textbook is the right move here. This assignment builds directly on the cryptography material rather than asking you to invent a protocol from scratch. The assignment specifically points you to Chapter 2, especially §§2.2, 2.6, 2.7, and Chapter 4, especially §§4.1–4.4.[^1]

You have **10 days including today**, and the official deadline is **Sunday, October 4**.[^2] I’d make **Saturday, October 3 your personal hard deadline**, leaving October 4 as emergency-only buffer.

### Your soft-deadline plan

| Date | Goal | What to do | Soft deadline |
|---|---|---|---|
| **Thu Sep 24 — Today** | Understand + prepare | Read the entire assignment carefully. Review **CTR mode, integrity/MACs, and replay attacks**. Set up the Python environment, generate `ffdhe3072.pem`, and capture the required version information for your report. | **Lab prep completely finished tonight** |
| **Fri Sep 25** | **Task 1 complete** | Finish the relevant Chapter 2 review. Implement `baseline_ctr.py`, demonstrate the CTR bit-flip, demonstrate replay, and capture evidence. Immediately write the Task 1 section of the report while it’s fresh. | **Task 1 done by Friday night** |
| **Sat Sep 26** | Learn Task 2 concepts | Focus on **Diffie–Hellman, RSA signatures, nonces, entity authentication, MITM/reflection attacks, forward secrecy, and key separation**. Then sketch the handshake flow and canonical transcript before coding. | **Understand Task 2 + handshake design drafted** |
| **Sun Sep 27** | Build Task 2 | Implement the happy-path authenticated DH handshake: RSA keys, ephemeral DH values, nonces, transcript encoding, signatures, verification, shared secret, KDF, and directional keys. | **Successful handshake working** |
| **Mon Sep 28** | **Task 2 complete** | Add rejection behavior for bad signatures, changed values, malformed transcripts, wrong identities, and reflection. Write your Task 2 report explanation. | **Task 2 fully done** |
| **Tue Sep 29** | Build Task 3 | Implement `secure_record.py`: header, IV construction, AES-CTR encryption, HMAC, `seal()`, and `open_record()`. Get normal gateway→node and node→gateway messages working. | **Happy-path record layer working** |
| **Wed Sep 30** | **Task 3 complete** | Finish sequence-number handling, replay rejection, direction checking, MAC-before-decrypt behavior, and safe error handling. Write your Task 3 explanation. | **Task 3 fully done** |
| **Thu Oct 1** | **Task 4 complete** | Write the adversarial tests: valid communication, ciphertext modification, header modification, replay, direction reflection, and handshake authentication failure. Every attack should assert a specific safe failure. | **Entire implementation + tests passing** |
| **Fri Oct 2** | Report day | Write the **500–700 word security note**, finish screenshots/evidence, explanations, README, `AI_USAGE.md`, and organize AI logs. Run everything again from the VM. | **Submission package complete** |
| **Sat Oct 3** | **Submit** | Proofread `report.pdf`, verify every rubric item, make a clean test run, inspect the repository/archive, and submit. | **Submit by ~6 PM** |
| **Sun Oct 4** | Buffer only | Use only if something unexpectedly breaks or you discover a submission problem. | **No planned assignment work** |

The reason I’d front-load Task 2 is that it’s probably the biggest conceptual jump. It requires authenticated finite-field Diffie–Hellman, a very specific canonical transcript, RSA-PSS signatures, identity and role validation, and the assignment-provided KDF.[^3] Task 3 then builds naturally on the keys produced by that handshake: AES-CTR plus HMAC, sequence numbers, directional keys, unique IVs, and verify-before-decrypt.[^4]

### How I’d approach the textbook review

Don’t try to read Chapters 2 and 4 cover-to-cover before touching code. Tie the reading directly to the task you’re about to implement.

**Today / Task 1:** understand AES-CTR especially well. Make sure you can explain why changing ciphertext bits predictably changes plaintext bits, why encryption provides confidentiality but **not integrity**, and why encryption alone does nothing to identify a replay. That is exactly what Task 1 is demonstrating.[^5]

**Before Task 2:** spend the most study time here. You want to be able to explain the difference between *key establishment* and *authentication*: Diffie–Hellman establishes shared secret material, while the RSA signatures authenticate who participated in the exchange. Pay special attention to nonces, signatures, entity authentication, MITM attacks, reflection attacks, and forward secrecy.

**Before Task 3:** review MACs/HMAC, CTR IV requirements, Encrypt-then-MAC, and sequence numbers. By the time you start coding this portion, you should be able to answer, without looking it up, **why the receiver verifies the MAC before decrypting** and **why encryption and MAC keys are separate**.

One thing that will save you a ton of pain: **write each report section when you finish its task.** Don’t leave all the writing and screenshots until October 2. Your report is explicitly the main graded submission, even though the code is included so the grader can verify it.[^6]

Also keep your **AI log updated as you go** rather than reconstructing it on October 3. The assignment allows AI for learning, brainstorming, debugging, and coding, but requires the relevant conversation logs plus an `AI_USAGE.md` explaining what you used, changed, tested, and at least one limitation/error/rejected suggestion.[^7]

Your biggest milestone should be **Thursday, October 1: all code and tests work**. That gives you two full days for writing, verification, and submission instead of getting trapped in the classic “code works at 11:42 PM, now I have to write six pages” situation.

If you stay on those soft deadlines, this should feel pretty controlled rather than like a 10-day crypto boss fight.

---

## Citation notes

All numbered citations below refer to the user-provided assignment handout, **`HW2-2.pdf`**:

[^1]: Assignment sections identifying the relevant textbook chapters and subsections.
[^2]: Assignment deadline stated in the handout.
[^3]: Task 2 requirements for authenticated finite-field Diffie–Hellman, canonical transcripts, RSA-PSS signatures, validation, and key derivation.
[^4]: Task 3 requirements for the secure record layer, including AES-CTR, HMAC, sequencing, directional keys, IV uniqueness, and verification before decryption.
[^5]: Task 1 requirements demonstrating CTR-mode bit flipping and replay behavior.
[^6]: Submission and report requirements in the assignment handout.
[^7]: Assignment policy and deliverables concerning AI use, conversation logs, and `AI_USAGE.md`.

---

## Follow-up user request

Export this conversation to markdown.
