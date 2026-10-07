# Chat Export — Pytest Setup for Task 4

## User

First explain pytest, then walk through setting it up for task 4.

## Assistant

Yep — Task 4 is basically where `pytest` gets to play attacker against the code you wrote in Tasks 2 and 3.

Your assignment specifically requires automated tests for six adversarial/valid cases, and **each test needs to assert a specific safe failure**. Conveniently, the assignment already has you install `pytest==9.1.1`.

## 1. What is pytest?

`pytest` is a Python testing framework. Instead of manually running your program and looking at the output, you write small functions that say:

> Given this setup, when I do this, I expect this exact result.

For example:

```python
def test_addition():
    result = 2 + 2
    assert result == 4
```

Then run:

```bash
pytest
```

Pytest automatically finds functions whose names start with `test_` and runs them.

The important pieces for your homework are **assertions, exception assertions, and fixtures**.

### Normal assertions

For valid behavior:

```python
def test_message():
    plaintext = b"Hello"
    assert plaintext == b"Hello"
```

If that expression is false, pytest reports the test as failed.

For Task 4, you'll use this when checking that a legitimate encrypted record produces the original plaintext.

### Testing expected failures

This is especially important for security testing.

Suppose a replay should cause your `SequenceError`:

```python
with pytest.raises(SequenceError):
    open_record(node_session, record)
```

This means:

> The test passes only if `open_record()` raises `SequenceError`.

That's exactly what your assignment means by a **specific safe failure**.

You already created useful exception types for this:

```python
class RecordError(Exception):
    pass

class AuthenticationError(RecordError):
    pass

class SequenceError(RecordError):
    pass

class DirectionError(RecordError):
    pass
```

So you can write tests such as:

```python
with pytest.raises(AuthenticationError):
    open_record(node_session, modified_record)
```

rather than something vague like:

```python
with pytest.raises(Exception):
```

The first one demonstrates that your program rejected the attack **for the intended security reason**.

---

## 2. Fixtures: the part of pytest you'll probably use most

Your tests repeatedly need this:

1. Load FFDHE parameters.
2. Generate Gateway RSA key.
3. Generate Node RSA key.
4. Initialize Gateway.
5. Initialize Node.
6. Perform handshake.
7. Get two fresh `Session` objects.

You don't want to paste all of that into every test.

That's what a **fixture** is.

A fixture is reusable test setup:

```python
@pytest.fixture
def sessions():
    ...
    return gateway_session, node_session
```

Then pytest injects it into any test that asks for it:

```python
def test_valid_message(sessions):
    gateway_session, node_session = sessions
```

You don't call `sessions()` yourself. Pytest sees the parameter name and supplies it.

Even better: by default, the fixture runs again for **every test**. That's exactly what you want because your `Session` objects are stateful: `seal()` increments `send_sequence`, and `open_record()` increments `recv_sequence`.

So each attack starts against a clean session.

---

# 3. Set up your Task 4 directory

Your assignment expects:

```text
hw2/
├── handshake.py
├── secure_record.py
├── ffdhe3072.pem
└── tests/
```

I'd make it:

```text
hw2/
├── handshake.py
├── secure_record.py
├── ffdhe3072.pem
│
└── tests/
    ├── conftest.py
    ├── test_secure_record.py
    └── test_handshake.py
```

This separation maps nicely to what you're actually testing:

```text
test_secure_record.py
    valid messages
    modified ciphertext
    modified header
    replay
    reflection

test_handshake.py
    incorrect RSA public key
```

And:

```text
conftest.py
    common Gateway/Node setup
```

---

# 4. Create `tests/conftest.py`

`conftest.py` is a special pytest file. Fixtures defined there are automatically available to the tests in that directory.

A good starting point for your implementation is:

```python
from pathlib import Path

import pytest

from handshake import (
    GATEWAY_IDENTITY,
    GATEWAY_ROLE,
    NODE_IDENTITY,
    NODE_ROLE,
    Party,
    generate_rsa_signing_key,
    handshake,
    load_dh_parameters,
)


GROUP_FILE = Path(__file__).resolve().parents[1] / "ffdhe3072.pem"


@pytest.fixture(scope="session")
def dh_parameters():
    return load_dh_parameters(GROUP_FILE)


@pytest.fixture(scope="session")
def signing_keys():
    gateway_key = generate_rsa_signing_key()
    node_key = generate_rsa_signing_key()

    return gateway_key, node_key


@pytest.fixture
def parties(dh_parameters, signing_keys):
    gateway_key, node_key = signing_keys

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

There are three levels here.

### `dh_parameters`

```python
@pytest.fixture(scope="session")
def dh_parameters():
```

`scope="session"` means pytest loads the expensive FFDHE parameter file once for the entire test run.

### `signing_keys`

Same idea:

```python
@pytest.fixture(scope="session")
def signing_keys():
```

Your RSA keys are supposed to represent long-term signing keys anyway, so reusing them throughout the test run actually fits your design.

### `sessions`

Notice this one doesn't say:

```python
scope="session"
```

That's intentional.

It gives every test:

```python
gateway_session
node_session
```

with sequences starting back at:

```text
0
```

Your `Session` class initializes both send and receive sequences at zero.

---

# 5. Start with the happy-path test

Create:

```text
tests/test_secure_record.py
```

Start with the easiest test required by Task 4:

> valid handshake and bidirectional messages

```python
from secure_record import seal, open_record


def test_valid_bidirectional_messages(sessions):
    gateway_session, node_session = sessions

    gateway_message = b"Hello, Node"
    record = seal(
        gateway_session,
        gateway_message,
        message_type=1,
    )

    message_type, plaintext = open_record(
        node_session,
        record,
    )

    assert message_type == 1
    assert plaintext == gateway_message

    node_message = b"Hello, Gateway"
    record = seal(
        node_session,
        node_message,
        message_type=2,
    )

    message_type, plaintext = open_record(
        gateway_session,
        record,
    )

    assert message_type == 2
    assert plaintext == node_message
```

This test verifies quite a bit.

The handshake completed successfully, then:

```text
Gateway ───── encrypted record ────> Node
Gateway <──── encrypted record ───── Node
```

Your handshake deliberately maps Gateway send keys to Node receive keys and vice versa.

So this test proves the normal protocol works before you start beating it with a wrench.

Run just this test:

```bash
pytest -q tests/test_secure_record.py
```

Because your implementation has lots of useful `print()` statements, pytest will normally capture them. If you want to see all of them:

```bash
pytest -s tests/test_secure_record.py
```

`-s` is pretty useful while developing this assignment.

---

# 6. Test modified ciphertext

Your record is:

```text
header || IV || ciphertext || tag
```

Your constants tell us where the ciphertext starts:

```python
HEADER_SIZE
IV_SIZE
```

So:

```python
from secure_record import (
    HEADER_SIZE,
    IV_SIZE,
    AuthenticationError,
    seal,
    open_record,
)


def test_modified_ciphertext_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"Hello, Node",
        message_type=1,
    )

    modified = bytearray(record)

    ciphertext_start = HEADER_SIZE + IV_SIZE

    modified[ciphertext_start] ^= 0x01

    with pytest.raises(AuthenticationError):
        open_record(node_session, bytes(modified))
```

You'll also need:

```python
import pytest
```

at the top.

The important trick is:

```python
modified[ciphertext_start] ^= 0x01
```

That flips one bit.

Because your HMAC covers:

```text
header || IV || ciphertext
```

the tag no longer matches.

Your expected safe failure is therefore:

```python
AuthenticationError
```

And crucially, your implementation checks the HMAC before calling the decryption function.

That's exactly the behavior Task 3 demanded.

---

# 7. Test modified authenticated header

This one has a small gotcha.

Don't change `direction`, because your code checks direction before checking HMAC:

```python
if direction != session.recv_direction:
    raise DirectionError(...)
```

That's useful for your reflection test, but it doesn't cleanly demonstrate that your **authenticated header** is protected by the MAC.

Instead, modify the `message_type`.

Your header format is:

```text
version(1)
direction(1)
sequence(8)
message_type(1)
ciphertext_length(4)
```

Therefore the offsets are:

```text
0       version
1       direction
2-9     sequence
10      message_type
11-14   ciphertext length
```

So:

```python
def test_modified_header_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"Hello, Node",
        message_type=1,
    )

    modified = bytearray(record)

    message_type_offset = 10
    modified[message_type_offset] ^= 0x01

    with pytest.raises(AuthenticationError):
        open_record(node_session, bytes(modified))
```

The record is still structurally valid.

But the header changed while the tag didn't.

Result:

```text
HMAC(header' || IV || ciphertext)
    !=
original tag
```

So you get exactly the failure you want:

```python
AuthenticationError
```

---

# 8. Test replay

This one is beautifully simple because your sequence-number implementation already does all the work.

```python
from secure_record import SequenceError


def test_replayed_record_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"Hello, Node",
        message_type=1,
    )

    message_type, plaintext = open_record(
        node_session,
        record,
    )

    assert plaintext == b"Hello, Node"

    with pytest.raises(SequenceError):
        open_record(node_session, record)
```

First receive:

```text
record sequence = 0
expected sequence = 0

✓ accepted

receiver sequence becomes 1
```

Replay:

```text
record sequence = 0
expected sequence = 1

✗ rejected
```

That's literally what this check in your implementation does:

```python
if sequence != session.recv_sequence:
    raise SequenceError(...)
```

This is probably the cleanest Task 4 test of the bunch.

---

# 9. Test reflection into the opposite direction

Create a legitimate:

```text
Gateway → Node
```

record.

Then hand it back to the Gateway as though an attacker reflected it:

```text
Gateway ─────> attacker
    ↑             |
    └─────────────┘
```

Test:

```python
from secure_record import DirectionError


def test_reflected_record_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"Hello, Node",
        message_type=1,
    )

    with pytest.raises(DirectionError):
        open_record(gateway_session, record)
```

Why?

The record says:

```text
direction = GATEWAY_TO_NODE
```

But Gateway's expected receive direction is:

```text
NODE_TO_GATEWAY
```

Your sessions are deliberately configured this way.

So:

```python
open_record(gateway_session, record)
```

must reject it.

That's a really nice demonstration of why you included direction inside the protected protocol state instead of treating encrypted bytes as interchangeable.

---

# 10. Test the bad RSA public key

Put this one in:

```text
tests/test_handshake.py
```

Task 4 says the sixth test can be **one of**:

> incorrect RSA public key, invalid RSA-PSS transcript signature, or reflected handshake message.

The incorrect-public-key option is probably the cleanest with your current architecture.

Your `verify_signature()` obtains the peer public key from:

```python
self.trusted_peers[peer_identity]
```

and calls RSA-PSS verification.

So deliberately give Gateway the wrong Node public key:

```python
import pytest

from cryptography.exceptions import InvalidSignature

from handshake import (
    GATEWAY_IDENTITY,
    GATEWAY_ROLE,
    NODE_IDENTITY,
    NODE_ROLE,
    Party,
    generate_rsa_signing_key,
    handshake,
)


def test_incorrect_rsa_public_key_rejected(
    dh_parameters,
    signing_keys,
):
    gateway_key, node_key = signing_keys

    wrong_node_key = generate_rsa_signing_key()

    gateway = Party(
        identity=GATEWAY_IDENTITY,
        role=GATEWAY_ROLE,
        dh_parameters=dh_parameters,
        signing_key=gateway_key,
        trusted_peers={
            NODE_IDENTITY: wrong_node_key.public_key(),
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

    with pytest.raises(InvalidSignature):
        handshake(gateway, node)
```

Conceptually:

```text
Actual Node
    |
    | signs TH with Node private key
    ↓

signature


Gateway
    |
    | verifies using WRONG Node public key
    ↓

InvalidSignature
```

That's exactly what authenticated Diffie–Hellman is supposed to prevent.

Someone knowing the DH parameters and generating their own ephemeral DH key isn't sufficient. They must also possess the private signing key corresponding to the public key that the peer already trusts.

---

# 11. Your completed Task 4 test layout

At that point you have:

```text
tests/
├── conftest.py
│
├── test_secure_record.py
│   ├── test_valid_bidirectional_messages
│   ├── test_modified_ciphertext_rejected
│   ├── test_modified_header_rejected
│   ├── test_replayed_record_rejected
│   └── test_reflected_record_rejected
│
└── test_handshake.py
    └── test_incorrect_rsa_public_key_rejected
```

That maps one-for-one onto the required tests:

| Requirement | Expected result |
|---|---|
| Valid handshake + messages | plaintext matches |
| Modified ciphertext | `AuthenticationError` |
| Modified authenticated header | `AuthenticationError` |
| Replay | `SequenceError` |
| Opposite-direction reflection | `DirectionError` |
| Incorrect RSA key | `InvalidSignature` |

That's a very strong setup because you're not merely asserting:

```python
something broke
```

You're asserting:

```text
this particular attack was rejected
by this particular security mechanism
for this particular reason
```

Which is what the Task 4 wording is getting at with **"specific safe failure."**

## 12. Running everything

From your `hw2/` directory:

```bash
pytest
```

More compact output:

```bash
pytest -q
```

Show your program's print statements:

```bash
pytest -s
```

Both:

```bash
pytest -qs
```

Run just the record tests:

```bash
pytest -q tests/test_secure_record.py
```

Run one specific attack:

```bash
pytest -q tests/test_secure_record.py::test_replayed_record_rejected
```

And for your final evidence, I'd run:

```bash
pytest -v
```

You'll get something along the lines of:

```text
tests/test_handshake.py::test_incorrect_rsa_public_key_rejected PASSED
tests/test_secure_record.py::test_valid_bidirectional_messages PASSED
tests/test_secure_record.py::test_modified_ciphertext_rejected PASSED
tests/test_secure_record.py::test_modified_header_rejected PASSED
tests/test_secure_record.py::test_replayed_record_rejected PASSED
tests/test_secure_record.py::test_reflected_record_rejected PASSED

======================= 6 passed =======================
```

That's the output I'd capture for the Task 4 evidence in your report.

One thing I especially like about this setup for **your** implementation is that you don't need to rewrite Tasks 2 or 3 just to make them testable. Your existing `Session` state and the custom `AuthenticationError`, `SequenceError`, and `DirectionError` exceptions already give pytest exactly the hooks it needs.

## User

ImportError while loading conftest '/home/crazy/csce465-agentsec/hw2/tests/conftest.py'.

```text
tests/conftest.py:5: in <module>
    from handshake import (
E   ModuleNotFoundError: No module named 'handshake'
```

## Assistant

Yep — this is almost certainly an **import-path issue**, not a problem with your fixture.

Your structure is probably:

```text
/home/crazy/csce465-agentsec/
└── hw2/
    ├── handshake.py
    ├── secure_record.py
    ├── ffdhe3072.pem
    └── tests/
        └── conftest.py
```

And `conftest.py` has:

```python
from handshake import ...
```

For that to work, Python needs `hw2/` on its module search path.

### The cleanest fix

Run pytest **from inside `hw2`**, and preferably invoke it through Python:

```bash
cd /home/crazy/csce465-agentsec/hw2
python -m pytest -v
```

I recommend `python -m pytest` over just:

```bash
pytest
```

because `python -m pytest` reliably puts your current working directory on Python's import path.

Then Python can see:

```text
hw2/
├── handshake.py   ← import handshake finds this
├── secure_record.py
└── tests/
```

So this works:

```python
from handshake import (
    Party,
    handshake,
    ...
)
```

### Check where you're currently running it

Run:

```bash
pwd
```

You want:

```text
/home/crazy/csce465-agentsec/hw2
```

If instead you're at:

```text
/home/crazy/csce465-agentsec
```

then Python looks for:

```text
/home/crazy/csce465-agentsec/handshake.py
```

which doesn't exist, because it's actually:

```text
/home/crazy/csce465-agentsec/hw2/handshake.py
```

That gives exactly:

```text
ModuleNotFoundError: No module named 'handshake'
```

### I'd keep your imports as-is

I would **not** change this:

```python
from handshake import ...
```

to:

```python
from hw2.handshake import ...
```

at least not right now.

Your `secure_record.py` itself currently imports:

```python
from handshake import (...)
```

So your code is already designed around `hw2/` being the working directory.

That's completely reasonable for this homework, especially since the expected submission layout places `handshake.py`, `secure_record.py`, and `tests/` together under `hw2/`.

So try:

```bash
cd /home/crazy/csce465-agentsec/hw2
source ../.venv/bin/activate   # if your venv is in csce465-agentsec/.venv
python -m pytest -v
```

If your `.venv` is elsewhere, just activate it however you've been doing already.

If that still throws the same error, send me the output of:

```bash
pwd
ls
python -c "import sys; print(sys.path)"
```

and we'll pin down exactly what's happening.

## User

export this chat to markdown
