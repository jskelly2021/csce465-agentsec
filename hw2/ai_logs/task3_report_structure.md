# Chat Export — Task 3 Report Structure

## User

How should I structure my report for task 3?

## Assistant

For **Task 3**, I’d structure the report around showing that your `secure_record.py` correctly implements the specified **Encrypt-then-MAC record layer**, rather than turning it into another long theory section. The assignment gives you a very concrete wire format and set of security requirements, and Task 3 is worth **35 points**, so you want the grader to be able to map your report directly to those requirements.

### Task 3 — Encrypt-then-MAC Record Layer

#### 3.1 Design Overview

Start with a short paragraph explaining what the record layer does and where its keys come from.

Something along the lines of:

> After the authenticated Diffie-Hellman handshake in Task 2, each party has separate encryption and MAC keys for each communication direction. Task 3 uses these keys to construct an Encrypt-then-MAC record layer. Each outgoing plaintext is encrypted using AES-256-CTR, and an HMAC-SHA-256 tag authenticates the record header, IV, and ciphertext. Sequence numbers provide replay and ordering protection.

I would explicitly mention the four directional keys:

```text
K_g2n_enc
K_g2n_mac
K_n2g_enc
K_n2g_mac
```

That connects Task 3 cleanly back to Task 2.

---

#### 3.2 Record Format

This should probably be the centerpiece of the section because the assignment gives an exact format.

Show something like:

```text
Record
+-------------------+
| version      1 B  |
| direction    1 B  |
| sequence     8 B  |
| message_type 1 B  |
| length       4 B  |
+-------------------+
| IV           16 B |
+-------------------+
| ciphertext    ... |
+-------------------+
| HMAC tag     32 B |
+-------------------+
```

Then explain:

```text
header =
    version ||
    direction ||
    sequence ||
    message_type ||
    ciphertext_length

IV =
    session_id || sequence

ciphertext =
    AES-256-CTR(K_enc, IV, plaintext)

tag =
    HMAC-SHA-256(K_mac, header || IV || ciphertext)
```

The assignment specifically requires the IV to be the **8-byte session ID plus the 8-byte sequence number**.

A small diagram like this makes your implementation much easier to grade.

---

#### 3.3 `seal()` — Sending a Record

Explain what your `seal()` function does in order.

You don't need to dump the whole function into the report. I'd describe the algorithm:

1. Select the encryption and MAC keys for the sending direction.
2. Obtain the sender's current sequence number.
3. Construct the record header.
4. Construct the IV as `session_id || sequence`.
5. Encrypt the plaintext using AES-256-CTR.
6. Compute the HMAC over:

```text
header || IV || ciphertext
```

7. Assemble the complete record.
8. Increment the sender sequence number.

The important thing to point out is that **the sequence number is included in both the authenticated header and the IV**.

I'd include maybe one short code snippet showing the core operations:

```python
iv = session_id + sequence.to_bytes(8, "big")

ciphertext = encrypt_ctr(k_enc, iv, plaintext)

tag = compute_hmac(
    k_mac,
    header + iv + ciphertext,
)
```

Not the whole function—just enough to prove how your design corresponds to the spec.

---

#### 3.4 `open_record()` — Receiving a Record

This part deserves a little more explanation because most of the security checks happen here.

Describe the order as:

```text
Receive record
    ↓
Parse header
    ↓
Validate version/direction/length
    ↓
Check expected sequence number
    ↓
Reconstruct IV
    ↓
Verify HMAC
    ↓
Decrypt ciphertext
    ↓
Increment expected sequence
    ↓
Release plaintext
```

The assignment explicitly requires the receiver to expect the **exact next sequence number**, verify the HMAC **before decrypting**, reject malformed/modified/wrong-direction/replayed records, and never release plaintext after an error.

I'd call out your ordering in particular:

> Authentication is completed before ciphertext is decrypted. If any validation or authentication step fails, `open_record()` raises an error and returns no plaintext.

That sentence directly hits one of their grading requirements.

---

#### 3.5 Sequence Numbers and IV Uniqueness

Keep this fairly short because Task 4's security note asks you to discuss CTR IV uniqueness in more depth.

Explain that each direction maintains its **own counter starting at zero**:

```text
Gateway → Node:  0, 1, 2, ...
Node → Gateway:  0, 1, 2, ...
```

And because the keys are also direction-specific, the same numerical sequence can safely exist in both directions.

For example:

```text
Gateway → Node:
K_g2n_enc
IV = session_id || 0

Node → Gateway:
K_n2g_enc
IV = session_id || 0
```

Those IV values may have the same bytes, but they're used under **different encryption keys**, satisfying the requirement that an IV never be reused under one key.

---

#### 3.6 Demonstration / Evidence

I'd definitely include one clean successful run of Task 3.

Something like:

```text
Gateway sends:
    sequence: 0
    plaintext: {"action":"READ","path":"notes.txt"}

Node receives:
    sequence: 0
    MAC verification: successful
    plaintext: {"action":"READ","path":"notes.txt"}

Node sends:
    sequence: 0
    plaintext: response message

Gateway receives:
    sequence: 0
    MAC verification: successful
    plaintext: response message
```

A screenshot or pasted terminal output is perfect.

You **do not need to exhaustively demonstrate all the attacks here**. That's what Task 4 is explicitly for: modified ciphertext, modified headers, replay, reflection, etc.

You can simply finish Task 3 with:

> Additional adversarial tests demonstrating rejection of ciphertext modification, header modification, replay, and direction reflection are presented in Task 4.

That keeps your report from repeating itself.

### So your final Task 3 section could look like this

```text
3. Task 3 — Encrypt-then-MAC Record Layer

3.1 Design Overview
    - Purpose of record layer
    - Direction-specific keys from Task 2
    - AES-256-CTR + HMAC-SHA-256

3.2 Record Format
    - Header fields
    - IV construction
    - Ciphertext
    - Authentication tag
    - Record diagram

3.3 seal()
    - Sequence of sending operations
    - Small relevant code snippet

3.4 open_record()
    - Parsing and validation
    - Sequence checking
    - MAC verification before decryption
    - Failure behavior

3.5 Sequence Numbers and IV Management
    - Independent counters
    - Start at zero
    - IV uniqueness

3.6 Successful Record Exchange
    - Gateway → Node example
    - Node → Gateway example
    - Screenshot / console output
    - Refer to Task 4 for adversarial testing
```

I'd aim for roughly **1–2 pages** for Task 3. The main goal is to make it painfully obvious to the grader that every line of their Task 3 requirements exists somewhere in your design. Save the deeper discussion of *why* CTR IV uniqueness, verify-before-decrypt, independent keys, and AEAD matter for the required **500–700 word Task 4 security note**.
