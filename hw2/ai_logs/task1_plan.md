# CSCE 465 HW2 — Task 1 AES-CTR Discussion

## User

Break down task 1. Create an actionable plan to get it done.

## Assistant

Task 1 is basically a small experiment proving two separate weaknesses of **AES-CTR by itself**:

1. An attacker can alter encrypted data in a predictable way without knowing the key.
2. An attacker can replay a valid ciphertext, and the receiver has no way to know it already processed it.

The assignment specifically wants `baseline_ctr.py`, using the fixed command `{"action":"READ","path":"notes.txt"}`, a relay that changes `READ` to another equal-length value, an explicit demonstration of the XOR relationship, and a replay where the receiver processes the same ciphertext twice.

### Actionable Task 1 plan

#### 1. Do the tiny bit of prep first

Before touching Task 1, make sure your venv is active and capture the required environment evidence:

```bash
python3 --version
openssl version
pip show cryptography pytest
```

Then create:

```text
hw2/
└── baseline_ctr.py
```

#### 2. Build the normal AES-CTR sender/receiver

Start with the exact plaintext:

```python
b'{"action":"READ","path":"notes.txt"}'
```

Create:

- random AES key
- random 16-byte CTR IV
- encryption function
- decryption/receiver function

Conceptually:

```text
plaintext
   ↓
AES-CTR encryption
   ↓
ciphertext
   ↓
receiver decrypts
   ↓
original command
```

Your first checkpoint should simply be:

```text
Original:  {"action":"READ","path":"notes.txt"}
Received:  {"action":"READ","path":"notes.txt"}
```

#### 3. Find the byte positions occupied by `READ`

Now locate the four plaintext bytes:

```text
READ
```

You want your relay to alter **only those four ciphertext bytes**.

You can calculate the starting position with something like:

```python
offset = plaintext.index(b"READ")
```

Pick another **4-byte** value. For example:

```python
b"READ" → b"SEND"
```

#### 4. Calculate and print the XOR difference

CTR works essentially like:

```text
C = P XOR keystream
```

If the attacker wants:

```text
P  = READ
P' = SEND
```

calculate:

```text
delta = READ XOR SEND
```

Then alter the ciphertext:

```text
C' = C XOR delta
```

at just those four positions.

When the receiver decrypts:

```text
C' XOR keystream
```

you get:

```text
SEND
```

even though the attacker never knew the AES key.

Your program should explicitly print something along these lines:

```text
Original bytes:   52 45 41 44
Desired bytes:    53 45 4e 44
XOR difference:   01 00 0f 00

Original command:
{"action":"READ","path":"notes.txt"}

Modified command:
{"action":"SEND","path":"notes.txt"}
```

#### 5. Put the modification inside a `relay()` function

Don't just manually edit the ciphertext in `main()`.

Structure it more like:

```text
sender
   ↓
ciphertext
   ↓
relay(ciphertext)
   ↓
modified ciphertext
   ↓
receiver
```

So your file might eventually have roughly:

```python
def encrypt(...):
    ...

def decrypt(...):
    ...

def relay(ciphertext):
    ...
    return modified_ciphertext

def receiver(...):
    ...

def main():
    ...
```

The important security point is that `relay()` should **not receive the AES key**.

#### 6. Add the replay demonstration

Now do a completely separate experiment.

Take one legitimate ciphertext and give it to your receiver twice:

```python
receiver(ciphertext)
receiver(ciphertext)
```

Make the receiver visibly "process" the request. Something simple is enough:

```text
Receiver processed: {"action":"READ","path":"notes.txt"}
Receiver processed: {"action":"READ","path":"notes.txt"}
```

You could add a counter to make the result even clearer:

```text
Processing command #1: ...
Processing command #2: ...
```

The important thing is that you're replaying the **identical ciphertext**, not encrypting the plaintext twice.

#### 7. Make your final console output screenshot-friendly

Arrange the final program into two labeled demonstrations:

```text
=== CTR BIT-FLIP DEMONSTRATION ===

Original plaintext:
...

Original action bytes:
...

Modified action bytes:
...

XOR delta:
...

Receiver decrypted modified ciphertext:
...


=== REPLAY DEMONSTRATION ===

Sending ciphertext for first time...
Receiver processed command #1: ...

Replaying identical ciphertext...
Receiver processed command #2: ...
```

#### 8. Write the Task 1 report section immediately afterward

Organize the report section around:

- **Design**
- **Experiment**
- **Root cause**

For root cause, distinguish:

```text
Integrity failure:
CTR encryption is malleable. Changing a ciphertext bit predictably
changes the corresponding plaintext bit.

Replay failure:
The receiver has no sequence number, nonce tracking, or other state
indicating whether a ciphertext has already been accepted.
```

The central takeaway is:

> Confidentiality does not automatically provide integrity or replay protection.

### Definition of done

- [ ] `baseline_ctr.py` exists.
- [ ] Exact assigned command is encrypted with AES-CTR.
- [ ] Normal encryption/decryption works.
- [ ] Relay does **not** know the key.
- [ ] `READ` is changed to another four-byte value.
- [ ] Program prints original bytes, desired bytes, and XOR delta.
- [ ] Modified ciphertext decrypts to the attacker-chosen action.
- [ ] Exact same ciphertext is sent to the receiver twice.
- [ ] Receiver visibly processes it twice.
- [ ] Terminal evidence/screenshots are captured.
- [ ] Task 1 report explains **design → experiment → root cause**.

---

## User

Provide a concise walkthrough of the cryptography library for encryption and decryption with aes-ctr

## Assistant

For this homework, the `cryptography` package gives you AES-CTR through three main pieces: `Cipher`, `algorithms.AES`, and `modes.CTR`.

```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
```

Generate a key and IV:

```python
key = os.urandom(32)   # 32 bytes = AES-256
iv = os.urandom(16)    # AES block size = 16 bytes
```

Create the cipher object:

```python
cipher = Cipher(
    algorithms.AES(key),
    modes.CTR(iv),
)
```

### Encrypt

```python
plaintext = b'{"action":"READ","path":"notes.txt"}'

encryptor = cipher.encryptor()
ciphertext = encryptor.update(plaintext) + encryptor.finalize()
```

Conceptually:

```text
plaintext
   ↓
AES(key) + CTR(iv)
   ↓
ciphertext
```

### Decrypt

Use the **same key and IV**:

```python
cipher = Cipher(
    algorithms.AES(key),
    modes.CTR(iv),
)

decryptor = cipher.decryptor()
decrypted = decryptor.update(ciphertext) + decryptor.finalize()

print(decrypted)
```

A clean helper-function version:

```python
def encrypt_ctr(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv))
    encryptor = cipher.encryptor()
    return encryptor.update(plaintext) + encryptor.finalize()


def decrypt_ctr(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv))
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()
```

The important CTR-specific idea is:

```text
ciphertext = plaintext XOR keystream
plaintext  = ciphertext XOR keystream
```

One important rule: **never reuse the same IV with the same AES key in CTR mode**.

---

## User

Clarify the relay function and XOR relation. My understanding is that the relay should receive the ciphertext, not the plaintext message or key.

## Assistant

Yes — your understanding is right.

The **relay should receive the ciphertext**, not the key and not the plaintext as an argument. The point is to show that an on-path attacker can modify AES-CTR ciphertext **without decrypting it**.

The attacker can know or infer the structure of the plaintext. In this assignment, the plaintext is fixed:

```text
{"action":"READ","path":"notes.txt"}
```

So the relay knows that bytes at a certain offset correspond to `READ`, even though it never decrypts the ciphertext.

For CTR:

```text
C = P XOR K
```

where `K` here is the CTR keystream, not literally the AES key.

Suppose the attacker wants:

```text
P  = READ
P' = SEND
```

Compute:

```text
delta = P XOR P'
```

Then modify the corresponding ciphertext bytes:

```text
C' = C XOR delta
```

When the receiver decrypts:

```text
P' = C' XOR K
```

Substitute:

```text
P' = (C XOR delta) XOR K
   = (P XOR K XOR delta) XOR K
   = P XOR delta
   = P XOR (P XOR desired)
   = desired
```

So `READ` becomes `SEND`.

A relay could look like this:

```python
def relay(ciphertext: bytes) -> bytes:
    modified = bytearray(ciphertext)

    offset = len(b'{"action":"')

    original = b"READ"
    desired = b"SEND"

    delta = bytes(a ^ b for a, b in zip(original, desired))

    for i, d in enumerate(delta):
        modified[offset + i] ^= d

    return bytes(modified)
```

Notice what it **doesn't** receive:

```python
relay(ciphertext)
```

not:

```python
relay(ciphertext, key, plaintext)   # defeats the point
```

The relay does have some prior knowledge:

- the message format
- where `READ` occurs
- the expected original value `READ`
- the desired replacement `SEND`

But it does **not** know the AES key or recover the plaintext through decryption.

For reporting/output, explicitly print the XOR relationship:

```python
print("Original:", original.hex())
print("Desired: ", desired.hex())
print("Delta:   ", delta.hex())
```

For example:

```text
R = 0x52    S = 0x53    delta = 0x01
E = 0x45    E = 0x45    delta = 0x00
A = 0x41    N = 0x4e    delta = 0x0f
D = 0x44    D = 0x44    delta = 0x00
```

The important distinction is: **the relay knows what plaintext bytes are expected to be at those positions, but it never receives or decrypts the plaintext.**

---

## User

Drop me a function that outputs the following format:

```text
Original bytes:   52 45 41 44
Desired bytes:    53 45 4e 44
XOR difference:   01 00 0f 00
```

## Assistant

```python
def print_xor_relation(original: bytes, desired: bytes) -> None:
    if len(original) != len(desired):
        raise ValueError("original and desired must be the same length")

    xor_diff = bytes(a ^ b for a, b in zip(original, desired))

    def fmt(data: bytes) -> str:
        return " ".join(f"{b:02x}" for b in data)

    print(f"Original bytes:   {fmt(original)}")
    print(f"Desired bytes:    {fmt(desired)}")
    print(f"XOR difference:   {fmt(xor_diff)}")
```

Usage:

```python
print_xor_relation(b"READ", b"SEND")
```

Output:

```text
Original bytes:   52 45 41 44
Desired bytes:    53 45 4e 44
XOR difference:   01 00 0f 00
```

---

## User

Clarify the replay instruction. My interpretation is that I should have the relay send both the original and modified ciphertexts to the receiver to demonstrate a MITM. Is this correct understanding?

## Assistant

Not quite. That would demonstrate **tampering**, but it would not by itself demonstrate **replay**.

Treat Task 1 as two separate attacks:

1. **Bit-flip / integrity attack**

```text
Sender
   |
   | original ciphertext
   v
Relay -- modifies ciphertext --> Receiver
                                decrypts modified command
```

This proves the MITM can alter the encrypted message without knowing the key.

2. **Replay attack**

```text
Sender
   |
   | ciphertext C
   v
Relay ---- C ----> Receiver   # processed once
      ---- C ----> Receiver   # exact same bytes, processed again
```

For replay, the important part is:

```python
receiver(ciphertext)
receiver(ciphertext)
```

The **identical ciphertext** gets delivered twice.

You could replay either the original ciphertext or the modified ciphertext. For example:

```python
modified = relay(ciphertext)

receiver(modified)
receiver(modified)  # replay
```

That would technically demonstrate both attacks with one modified record.

But for clarity, keep the output separated:

```text
=== BIT-FLIP ATTACK ===
Original command:  READ
Relay changes ciphertext...
Received command:  SEND

=== REPLAY ATTACK ===
Relay forwards original ciphertext...
Receiver processed command #1: READ

Relay forwards exact same ciphertext again...
Receiver processed command #2: READ
```

The two failures are:

- **Original → modified ciphertext** = lack of **integrity**
- **Same ciphertext → sent twice** = lack of **replay protection**

Sending the original once and the modified one once is **not** a replay, because they are two different ciphertexts.
