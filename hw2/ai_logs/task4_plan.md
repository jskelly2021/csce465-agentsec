# Chat Export — Task 4 Breakdown

## User

Breakdown task 4 into actionable tasks. Explain what is needed. What is considered done. Use code examples when necessary.

---

## Assistant

Task 4 is basically the **attack-your-own-protocol phase**. You already have most of the functionality Task 4 needs: your handshake establishes directional session keys, and your record layer has explicit exceptions for authentication, sequence, and direction failures.

The assignment requires six categories of automated adversarial tests, and every negative test needs to assert a **specific safe failure**. Then you need a 500–700 word security note.

### 1. Set up `pytest` and reusable fixtures

Create something like `tests/test_security.py`. You want every adversarial test to start with a fresh handshake because `Session.send_sequence` and `Session.recv_sequence` mutate as records are sent and received. Your existing `Session` begins both counters at zero.

A nice setup would be:

```python
# tests/test_security.py

from pathlib import Path

import pytest
from cryptography.exceptions import InvalidSignature

from handshake import (
    Party,
    GATEWAY_IDENTITY,
    GATEWAY_ROLE,
    NODE_IDENTITY,
    NODE_ROLE,
    generate_rsa_signing_key,
    load_dh_parameters,
    handshake,
)

from secure_record import (
    seal,
    open_record,
    AuthenticationError,
    SequenceError,
    HEADER_SIZE,
    IV_SIZE,
)


GROUP_FILE = Path(__file__).parent.parent / "ffdhe3072.pem"


@pytest.fixture(scope="session")
def dh_parameters():
    return load_dh_parameters(GROUP_FILE)


@pytest.fixture
def parties(dh_parameters):
    gateway_key = generate_rsa_signing_key()
    node_key = generate_rsa_signing_key()

    gateway = Party(
        identity=GATEWAY_IDENTITY,
        role=GATEWAY_ROLE,
        dh_parameters=dh_parameters,
        signing_key=gateway_key,
        trusted_peers={
            NODE_IDENTITY: node_key.public_key(),
        },
        peer_role=NODE_ROLE,
    )

    node = Party(
        identity=NODE_IDENTITY,
        role=NODE_ROLE,
        dh_parameters=dh_parameters,
        signing_key=node_key,
        trusted_peers={
            GATEWAY_IDENTITY: gateway_key.public_key(),
        },
        peer_role=GATEWAY_ROLE,
    )

    return gateway, node


@pytest.fixture
def sessions(parties):
    gateway, node = parties
    return handshake(gateway, node)
```

This isn't a required architecture, but it keeps the actual attack tests tiny and readable.

**Done means:** running `pytest` successfully discovers your test file and can establish fresh sessions without copy/pasting setup into every test.

### 2. Test a valid handshake and bidirectional communication

This is your positive-control test. You need to prove the protocol works normally before proving attacks fail. The assignment explicitly requires both a valid handshake and bidirectional messages.

Your handshake already maps gateway send keys to node receive keys and vice versa.

```python
def test_valid_handshake_and_bidirectional_messages(sessions):
    gateway_session, node_session = sessions

    g2n_record = seal(
        gateway_session,
        b"hello node",
        message_type=1,
    )

    message_type, plaintext = open_record(
        node_session,
        g2n_record,
    )

    assert message_type == 1
    assert plaintext == b"hello node"

    n2g_record = seal(
        node_session,
        b"hello gateway",
        message_type=2,
    )

    message_type, plaintext = open_record(
        gateway_session,
        n2g_record,
    )

    assert message_type == 2
    assert plaintext == b"hello gateway"
```

**Done means:** both directions decrypt to exactly the original plaintext and message type, with no exception.

### 3. Modify the ciphertext and prove authentication rejects it

Your record layout is `header || IV || ciphertext || tag`, and your `open_record()` verifies HMAC before decrypting. That means flipping even one ciphertext bit should produce `AuthenticationError`.

```python
def test_modified_ciphertext_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"important command",
        message_type=1,
    )

    tampered = bytearray(record)

    ciphertext_start = HEADER_SIZE + IV_SIZE
    tampered[ciphertext_start] ^= 0x01

    with pytest.raises(AuthenticationError):
        open_record(node_session, bytes(tampered))
```

That `^= 0x01` flips exactly one bit.

This test is particularly important because Task 1 showed CTR ciphertext can be modified. Task 3's HMAC is supposed to fix that exact weakness.

**Done means:** the modified ciphertext never produces plaintext, and `open_record()` raises specifically `AuthenticationError`.

### 4. Modify the authenticated header

You want to demonstrate that metadata isn't silently mutable either. Your header is packed as `>BBQBI`: version, direction, sequence, message type, ciphertext length.

A clean test is changing `message_type`, because it doesn't make the record malformed; it just changes authenticated data.

The byte offsets are:

```text
0       version
1       direction
2-9     sequence
10      message_type
11-14   ciphertext_length
```

So:

```python
def test_modified_header_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"hello",
        message_type=1,
    )

    tampered = bytearray(record)

    # Change authenticated message_type.
    tampered[10] ^= 0x01

    with pytest.raises(AuthenticationError):
        open_record(node_session, bytes(tampered))
```

Why `AuthenticationError` instead of something like `RecordError`? Because the message is structurally valid, but the HMAC no longer matches. That's exactly what you want to demonstrate.

**Done means:** changing an authenticated header field results in `AuthenticationError`, with no plaintext released.

### 5. Replay a valid record

This test should succeed once and fail the second time. Your receiver checks that the incoming sequence equals exactly `session.recv_sequence`, then increments the expected sequence only after successful verification/decryption.

```python
def test_replayed_record_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"perform action",
        message_type=1,
    )

    # First delivery is legitimate.
    message_type, plaintext = open_record(
        node_session,
        record,
    )

    assert plaintext == b"perform action"

    # Exact same authenticated record is replayed.
    with pytest.raises(SequenceError):
        open_record(node_session, record)
```

The cool part here is that the replay has a **perfectly valid MAC**. Integrity alone cannot detect it. The sequence number does.

The first time, Node expects sequence `0`. After accepting it, Node expects `1`. Replaying sequence `0` therefore triggers your explicit sequence check.

**Done means:** first delivery succeeds, second delivery raises specifically `SequenceError`.

### 6. Reflect a record back into the sender

Here's where your directional key design comes into play. If Gateway sends a gateway→node record, an attacker can try returning that exact byte string to Gateway as though it were node→gateway traffic.

```python
def test_reflected_record_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"gateway command",
        message_type=1,
    )

    # Attacker reflects Gateway's own outgoing record
    # back toward Gateway.
    with pytest.raises(AuthenticationError):
        open_record(gateway_session, record)
```

At first glance you might expect `DirectionError`. With **your current implementation**, `AuthenticationError` is actually the expected result.

Gateway created this record with its `g2n_mac` key. When Gateway tries to receive something, `open_record()` verifies it with its `n2g_mac` key. Those are intentionally distinct.

And because your code checks the HMAC before checking the direction field, authentication fails first.

That's a completely legitimate safe failure. In fact, it gives you a nice report talking point: **directional key separation itself prevents reflection.**

**Done means:** reflecting an outgoing record back to the sender does not decrypt and raises specifically `AuthenticationError`.

### 7. Attack the authenticated handshake

Requirement 6 gives you a choice: incorrect RSA public key, invalid RSA-PSS transcript signature, **or** reflected handshake message.

The easiest clean test with your current architecture is an incorrect trusted RSA key.

Your `Party.verify_signature()` selects the peer's trusted RSA public key and verifies `peer_role || transcript_hash` with RSA-PSS. So construct the Node with an attacker's public key instead of Gateway's real one:

```python
def test_incorrect_rsa_public_key_rejected(dh_parameters):
    gateway_key = generate_rsa_signing_key()
    node_key = generate_rsa_signing_key()

    attacker_key = generate_rsa_signing_key()

    gateway = Party(
        identity=GATEWAY_IDENTITY,
        role=GATEWAY_ROLE,
        dh_parameters=dh_parameters,
        signing_key=gateway_key,
        trusted_peers={
            NODE_IDENTITY: node_key.public_key(),
        },
        peer_role=NODE_ROLE,
    )

    node = Party(
        identity=NODE_IDENTITY,
        role=NODE_ROLE,
        dh_parameters=dh_parameters,
        signing_key=node_key,

        # Wrong key for "gateway"
        trusted_peers={
            GATEWAY_IDENTITY: attacker_key.public_key(),
        },

        peer_role=GATEWAY_ROLE,
    )

    with pytest.raises(InvalidSignature):
        handshake(gateway, node)
```

Gateway genuinely signs the transcript using `gateway_key`, but Node tries to verify that signature using `attacker_key.public_key()`. The cryptography library therefore raises `InvalidSignature`.

This directly demonstrates why merely claiming `"I am gateway"` isn't sufficient. Node only accepts that identity if the transcript signature verifies under the already-trusted Gateway public key.

**Done means:** handshake establishment aborts with `InvalidSignature`; no usable pair of sessions is returned.

### 8. Run the suite, capture evidence, then write the security note

Run it from the root of `hw2`:

```bash
pytest -v
```

Ideally you'll end up with output roughly like:

```text
tests/test_security.py::test_valid_handshake_and_bidirectional_messages PASSED
tests/test_security.py::test_modified_ciphertext_rejected PASSED
tests/test_security.py::test_modified_header_rejected PASSED
tests/test_security.py::test_replayed_record_rejected PASSED
tests/test_security.py::test_reflected_record_rejected PASSED
tests/test_security.py::test_incorrect_rsa_public_key_rejected PASSED
```

For the report, Task 4 also requires a **500–700 word security note** covering the attacker model/non-goals, CTR IV uniqueness, verify-before-decrypt, separate encryption/MAC keys, comparison with an AEAD mode such as AES-GCM, and the fact that cryptographic authentication does not make an authorized tool call safe.

Your current implementation gives you direct material for almost every paragraph. The IV is `session_id || sequence`, which makes it unique as long as the sequence isn't reused under that session key. Your MAC uses a different key from encryption and authenticates the header, IV, and ciphertext. And `open_record()` verifies that MAC before calling AES-CTR decryption.

So your **Task 4 finish line** is very concrete: six passing pytest attack categories, every attack asserting the exact exception you expect, `pytest -v` evidence in the report, and a 500–700 word security note that explains *why* those tests fail safely rather than merely saying that they passed.

One thing I'd specifically avoid is writing tests like:

```python
with pytest.raises(Exception):
```

The assignment says **specific safe failure**, so `AuthenticationError`, `SequenceError`, and `InvalidSignature` are exactly the sort of assertions you want.

---

## User

Export this chat to markdown.
