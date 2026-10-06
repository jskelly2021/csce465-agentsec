# CSCE 465 HW2 — Task 2 Discussion

## User

Break down task 2. Create an actionable plan to get it done.

## Assistant

Task 2 is basically: **build a tiny authenticated key-exchange protocol between a simulated gateway and node**, and end with both sides independently deriving the exact same set of session keys.

It is worth **30 points**, and the required supporting files are `handshake.py` plus the `ffdhe3072.pem` parameter file.

### What you are building

At a high level, the handshake should look like this:

```text
Gateway                                   Node
   |                                        |
   |-- identity, DH public, nonce --------->|
   |<--------- identity, DH public, nonce --|
   |                                        |
   |       Both construct SAME transcript   |
   |                                        |
   |-- gateway signature ------------------>|
   |<-------------------- node signature ---|
   |                                        |
   |       Verify peer identity/signature   |
   |                                        |
   |       Compute DH shared secret Z       |
   |                                        |
   |       Derive identical session keys    |
```

The important bit is that **Diffie–Hellman establishes the secret, while RSA signatures authenticate who participated in that exchange**. The RSA keys never encrypt application data.

### Actionable implementation plan

#### 1. Get the prerequisite DH group working first

Before writing `handshake.py`, make sure you have:

```bash
cd "$HOME/csce465-agentsec/hw2"

openssl genpkey \
  -genparam \
  -algorithm DH \
  -pkeyopt group:ffdhe3072 \
  -out ffdhe3072.pem

openssl dhparam -in ffdhe3072.pem -text -noout | head -3
```

You want:

```text
DH Parameters: (3072 bit)
GROUP: ffdhe3072
```

**Checkpoint:** `ffdhe3072.pem` exists and loads successfully using `cryptography`.

#### 2. Build the basic party/key setup

In `handshake.py`, start with two simulated parties:

```text
Gateway
Node
```

Each needs a **long-term 3072-bit RSA signing key**.

Something along these lines conceptually:

```python
gateway_signing_key = ...
node_signing_key = ...
```

Then load `ffdhe3072.pem` once:

```python
dh_parameters = ...
```

For **each new session**, generate:

```python
gateway_dh_private
gateway_dh_public
gateway_nonce

node_dh_private
node_dh_public
node_nonce
```

The nonce must be **16 random bytes**, and the DH private values must be fresh every session.

**Checkpoint:** running the program twice produces different nonces and DH public values.

#### 3. Write an encoding helper before doing any cryptography

Every transcript field must be encoded as:

```text
4-byte big-endian length || field
```

So write a helper like:

```python
def encode_field(value: bytes) -> bytes:
    ...
```

Conceptually:

```text
"abc"

becomes

00 00 00 03 61 62 63
```

You'll probably also want something like:

```python
def encode_transcript(fields: list[bytes]) -> bytes:
    ...
```

Do **not** just concatenate fields.

I'd also implement:

```python
def decode_transcript(data: bytes) -> list[bytes]:
    ...
```

and make it throw an error if:

```text
declared length > bytes remaining
extra bytes remain
wrong number of fields
wrong fixed-size fields
```

#### 4. Add the fixed-width DH public-value encoding

FFDHE3072 has a 3072-bit modulus:

```text
3072 / 8 = 384 bytes
```

So create a helper:

```python
def int_to_384(value: int) -> bytes:
    return value.to_bytes(384, "big")
```

Use that representation for **both ephemeral DH public values** in the transcript.

**Checkpoint:** assert:

```python
len(gateway_dh_public_bytes) == 384
len(node_dh_public_bytes) == 384
```

#### 5. Build exactly one canonical transcript

The fields must occur in this order:

```text
protocol label
group identifier
gateway identity
node identity
gateway DH public value
node DH public value
gateway nonce
node nonce
```

Using values such as:

```python
b"CSCE465-HS-v2"
b"ffdhe3072"
b"gateway"
b"node"
gateway_public_bytes
node_public_bytes
gateway_nonce
node_nonce
```

Then:

```python
transcript = encode_transcript(fields)
TH = SHA256(transcript)
```

I'd put all of this behind:

```python
def build_transcript(...):
    ...
```

At this point, stop and verify:

```python
gateway_transcript == node_transcript
gateway_TH == node_TH
```

#### 6. Implement RSA-PSS signing

Each side signs:

```text
role || SHA-256(transcript)
```

So conceptually:

```python
gateway_signed_data = b"gateway" + TH
node_signed_data = b"node" + TH
```

Then:

```python
gateway_signature = gateway_private_key.sign(...)
node_signature = node_private_key.sign(...)
```

with:

```text
RSA-PSS
SHA-256
```

The receiver verifies using the peer's **known long-term RSA public key**.

Crucially:

```python
node verifies b"gateway" + TH
gateway verifies b"node" + TH
```

I'd make helpers:

```python
def sign_handshake(private_key, role: bytes, transcript_hash: bytes) -> bytes:
    ...

def verify_handshake_signature(
    public_key,
    expected_role: bytes,
    transcript_hash: bytes,
    signature: bytes,
) -> None:
    ...
```

#### 7. Check identity before accepting anything

The node should explicitly expect:

```python
peer_identity == b"gateway"
```

and the gateway should expect:

```python
peer_identity == b"node"
```

If it gets anything else:

```python
raise HandshakeError(...)
```

Conceptually:

```text
Identity tells you who the peer claims to be.
RSA verification proves that claim using the expected public key.
```

#### 8. Compute the Diffie–Hellman shared secret

Both sides independently compute:

```python
gateway_Z = gateway_dh_private.exchange(node_dh_public)
node_Z = node_dh_private.exchange(gateway_dh_public)
```

Make sure they become exactly:

```text
384 bytes
```

Then verify during development:

```python
assert gateway_Z == node_Z
assert len(gateway_Z) == 384
```

Do **not** implement DH arithmetic yourself.

#### 9. Implement the assignment's KDF exactly

First:

```text
K_master =
SHA-256(
    "CSCE465-KDF-v1"
    || Z
    || TH
)
```

Then derive:

```text
K_g2n_enc =
HMAC-SHA-256(
    K_master,
    "gateway-to-node encryption" || TH
)

K_g2n_mac =
HMAC-SHA-256(
    K_master,
    "gateway-to-node MAC" || TH
)

K_n2g_enc =
HMAC-SHA-256(
    K_master,
    "node-to-gateway encryption" || TH
)

K_n2g_mac =
HMAC-SHA-256(
    K_master,
    "node-to-gateway MAC" || TH
)

session_id =
first 8 bytes of
HMAC-SHA-256(
    K_master,
    "session identifier" || TH
)
```

A good helper would be:

```python
@dataclass
class SessionKeys:
    g2n_enc: bytes
    g2n_mac: bytes
    n2g_enc: bytes
    n2g_mac: bytes
    session_id: bytes
```

and:

```python
def derive_session_keys(z: bytes, transcript_hash: bytes) -> SessionKeys:
    ...
```

#### 10. Make both sides independently derive the keys

Do:

```python
gateway_keys = derive_session_keys(gateway_Z, gateway_TH)
node_keys = derive_session_keys(node_Z, node_TH)
```

Then verify:

```python
assert gateway_keys == node_keys
```

At minimum, print safe diagnostic information like hashes or lengths rather than actual secret keys:

```text
Handshake accepted
Transcript hashes match: True
Shared secrets match: True
Derived session keys match: True
Session ID: ...
```

### Then add the failure cases

Once the good handshake works, make Task 2 robust enough for Task 4.

Implement failures roughly in this order:

```text
1. Change one nonce after signature generation
   → signature verification fails

2. Change one DH public value
   → signature verification fails

3. Give node the wrong gateway RSA public key
   → signature verification fails

4. Change identity from gateway → attacker
   → identity check fails

5. Corrupt a transcript length
   → parser rejects before SHA-256

6. Give gateway's signature back to gateway as though it came from node
   → verification fails because expected role is "node"
```

### A clean `handshake.py` structure

```text
handshake.py

constants
    PROTOCOL_LABEL
    GROUP_ID
    GATEWAY_ID
    NODE_ID

data classes
    HandshakeParty
    SessionKeys
    HandshakeMessage

encoding helpers
    encode_field()
    decode_fields()
    dh_public_to_bytes()

crypto helpers
    generate_rsa_key()
    load_dh_parameters()
    sign_handshake()
    verify_handshake_signature()
    derive_session_keys()

protocol logic
    build_transcript()
    perform_handshake()

demo
    main()
```

### What to put in the report

Explain:

- **Diffie–Hellman key establishment:** produces a shared secret without transmitting it.
- **Digital signatures:** authenticate the ephemeral exchange.
- **Entity authentication:** expected identities + known RSA public keys tell each side who it is communicating with.
- **Nonces:** make sessions fresh and help prevent reuse/replay of old handshakes.
- **Replay resistance:** replaying old DH/nonces/signatures won't match the fresh session.
- **Forward secrecy:** fresh ephemeral DH values mean later compromise of the long-term RSA signing keys does not reveal old DH session secrets, assuming ephemeral DH private values are gone.
- **Key separation:** separate HMAC labels create independent gateway→node/node→gateway encryption and MAC keys.
- **MITM resistance:** attacker can't substitute DH values because those values, identities, and nonces are covered by the signed transcript.
- **Reflection resistance:** gateway and node sign different role-prefixed values.

### Recommended work order

```text
[ ] Generate/verify ffdhe3072.pem
[ ] Load DH parameters
[ ] Generate gateway/node RSA keys
[ ] Generate ephemeral DH keys + nonces
[ ] Implement 384-byte DH public encoding
[ ] Implement length-prefixed field encoding
[ ] Build canonical transcript
[ ] Compute TH
[ ] Sign role || TH
[ ] Verify both signatures + identities
[ ] Compute matching Z values
[ ] Implement exact KDF
[ ] Confirm all five outputs match
[ ] Add nonce-tamper test
[ ] Add DH-public tamper test
[ ] Add bad RSA key/signature test
[ ] Add malformed-transcript test
[ ] Add wrong-identity test
[ ] Add reflected-signature test
[ ] Capture successful output for report
[ ] Write Task 2 explanation while implementation is fresh
```

---

## User

I need clarification on the direction for this task. My understanding is that I need to build a simulated gateway and node, probably implemented as classes. Each will have a long-term RSA signing key. 

A session will be a run of the program. Each session, I generate DH values with the group.

I then need to basically reimplement the DH setup between the Gateway and Node? explain the transcript and the functionality I should be creating in this task.

## Assistant

Yes—your mental model is basically right. The key clarification is: **you are not reimplementing Diffie–Hellman itself.** You are building the **handshake protocol around library-provided Diffie–Hellman**.

The assignment explicitly says to use maintained library implementations and not implement DH arithmetic, RSA, SHA-256, or HMAC yourself.

### What the gateway and node are

Thinking of them as classes is a good design:

```python
class Gateway:
    identity
    rsa_private_key
    rsa_public_key

class Node:
    identity
    rsa_private_key
    rsa_public_key
```

Those RSA keys are **long-term identity keys**. In the simulation, you can generate them when the program starts and treat them as already trusted by the other side.

Conceptually:

```text
Gateway permanently knows:
    Gateway RSA private key
    Node RSA public key

Node permanently knows:
    Node RSA private key
    Gateway RSA public key
```

That's your simulated trust setup.

Then each **handshake/session** creates temporary values:

```text
Gateway:
    fresh ephemeral DH private/public key
    fresh 16-byte nonce

Node:
    fresh ephemeral DH private/public key
    fresh 16-byte nonce
```

One small correction to your wording: a session doesn't necessarily have to mean "one run of the program." You could absolutely make your program perform one session per run, but conceptually a session means **one execution of the handshake**. You could perform two handshakes in one program run and those would be two separate sessions.

### So what is the handshake actually doing?

Imagine your program begins with:

```python
gateway = Gateway(...)
node = Node(...)
```

Then you initiate:

```python
session = gateway.handshake(node)
```

Internally, you're simulating this:

```text
Gateway                                      Node

Generate ephemeral DH key             Generate ephemeral DH key
Generate nonce                         Generate nonce

       ------ exchange public info ------>

       <----- exchange public info -------

Both now know:

Gateway identity
Node identity
Gateway DH public value
Node DH public value
Gateway nonce
Node nonce

        ↓

Both construct EXACTLY the same transcript

        ↓

Both hash transcript

        ↓

Gateway signs "gateway" || transcript hash
Node signs    "node"    || transcript hash

        ↓

They verify each other's signatures

        ↓

They perform DH exchange

        ↓

Both independently obtain same shared secret Z

        ↓

Use Z + transcript hash to derive session keys
```

That's Task 2.

### The transcript is probably the weirdest part

The transcript is simply a **canonical record of everything important that happened during this handshake**.

Suppose your handshake has:

```python
protocol = b"CSCE465-HS-v2"
group = b"ffdhe3072"

gateway_id = b"gateway"
node_id = b"node"

gateway_dh_public = ...
node_dh_public = ...

gateway_nonce = ...
node_nonce = ...
```

The transcript contains all of them:

```text
CSCE465-HS-v2
ffdhe3072
gateway
node
gateway DH public value
node DH public value
gateway nonce
node nonce
```

But you don't serialize them like:

```python
transcript = (
    protocol
    + group
    + gateway_id
    + node_id
    + ...
)
```

because that can be ambiguous.

Instead, every field is length-prefixed:

```text
[length][field][length][field][length][field]...
```

where each length is exactly:

```text
4-byte big-endian integer
```

For example:

```text
gateway
```

is seven bytes, so you encode:

```text
00 00 00 07 | gateway
```

And:

```text
node
```

becomes:

```text
00 00 00 04 | node
```

So conceptually your function is:

```python
def encode_field(data: bytes) -> bytes:
    return len(data).to_bytes(4, "big") + data
```

Then:

```python
transcript = (
    encode_field(protocol)
    + encode_field(group)
    + encode_field(gateway_id)
    + encode_field(node_id)
    + encode_field(gateway_dh_public)
    + encode_field(node_dh_public)
    + encode_field(gateway_nonce)
    + encode_field(node_nonce)
)
```

Both sides must create **identical bytes**.

That's why the assignment calls it a **canonical transcript**.

### Why does the transcript exist?

This is the security heart of Task 2.

Imagine you only signed your DH public value:

```text
Sign(gateway_DH_public)
```

That tells you:

> "The gateway signed this DH value."

But what session was it for?

Who was it talking to?

What protocol was being used?

What nonce belonged to it?

What if an attacker moves that signed value into a different handshake?

The transcript binds **all of the context together**.

So instead of signing individual fields, both sides create:

```python
TH = SHA256(transcript)
```

and sign:

```text
role || TH
```

The gateway signs:

```python
b"gateway" + TH
```

and the node signs:

```python
b"node" + TH
```

So the gateway is effectively saying:

> "I, the gateway, approve this exact handshake involving these identities, these DH values, these nonces, this protocol, and this group."

And the node says the equivalent.

That's much stronger than simply signing a DH public key.

### Where Diffie–Hellman fits

This part is simpler than it sounds.

Both sides load the same:

```text
ffdhe3072
```

group parameters.

Then they independently generate ephemeral DH keys:

```python
gateway_private = dh_parameters.generate_private_key()
gateway_public = gateway_private.public_key()

node_private = dh_parameters.generate_private_key()
node_public = node_private.public_key()
```

They exchange the **public** values.

Then:

```python
gateway_Z = gateway_private.exchange(node_public)
```

and:

```python
node_Z = node_private.exchange(gateway_public)
```

The math guarantees:

```python
gateway_Z == node_Z
```

That `Z` is your shared secret.

So no, you're not implementing equations like:

```text
g^a mod p
g^b mod p
(g^b)^a mod p
```

yourself.

The `cryptography` library does that.

Your assignment is about making sure that **the DH exchange is authenticated**.

Plain DH has a classic weakness:

```text
Gateway <---- Attacker ----> Node
```

An attacker could substitute their own DH values and establish:

```text
Gateway ↔ Attacker

Attacker ↔ Node
```

That's the man-in-the-middle problem.

The RSA signatures solve that because the attacker cannot produce:

```text
valid Gateway RSA signature
```

over their substituted DH value.

### Then the transcript hash is also used in the KDF

After signatures are verified, both sides have:

```text
Z = DH shared secret
TH = SHA256(transcript)
```

Then Task 2 tells you exactly how to derive:

```text
K_master
K_g2n_enc
K_g2n_mac
K_n2g_enc
K_n2g_mac
session_id
```

So your resulting "session" could be something like:

```python
@dataclass
class Session:
    session_id: bytes

    gateway_to_node_enc_key: bytes
    gateway_to_node_mac_key: bytes

    node_to_gateway_enc_key: bytes
    node_to_gateway_mac_key: bytes
```

And the really important property is:

```python
gateway.session_keys == node.session_keys
```

without either side ever transmitting those keys.

That's what DH accomplished.

### What functionality I would actually implement

I would structure Task 2 around these pieces:

1. `Gateway` and `Node` each own a long-term RSA identity key and know the expected peer identity/public key.
2. When a handshake starts, each generates a fresh ephemeral FFDHE3072 key pair and a 16-byte nonce.
3. They exchange simulated handshake messages containing identity, DH public value, and nonce.
4. Both build the same length-prefixed canonical transcript.
5. Both compute `TH = SHA256(transcript)`.
6. Each signs `role || TH` with RSA-PSS/SHA-256.
7. Each checks the peer identity and verifies the peer signature.
8. Only after authentication succeeds, each computes `Z` from its DH private key and the peer's DH public key.
9. Both run the required KDF and independently derive identical directional encryption/MAC keys and `session_id`.
10. Reject altered nonces, altered DH values, bad signatures, unexpected identities, malformed transcripts, and reflection attempts.

So your top-level code could eventually read almost like:

```python
gateway = Gateway(...)
node = Node(...)

gateway_hello = gateway.start_handshake()
node_hello = node.start_handshake()

transcript = build_transcript(
    gateway_hello,
    node_hello,
)

gateway_signature = gateway.sign_transcript(transcript)
node_signature = node.sign_transcript(transcript)

gateway.verify_node(
    node_hello,
    transcript,
    node_signature,
)

node.verify_gateway(
    gateway_hello,
    transcript,
    gateway_signature,
)

gateway_session = gateway.establish_session(node_hello, transcript)
node_session = node.establish_session(gateway_hello, transcript)

assert gateway_session.keys == node_session.keys
```

That's the direction I'd take.

And there's an important conceptual separation here:

```text
RSA
    "Who am I talking to?"

Diffie-Hellman
    "Can we establish a shared secret?"

Transcript
    "Exactly what handshake are we authenticating?"

Nonce
    "Is this a fresh handshake?"

KDF
    "Turn that shared secret into several purpose-specific keys."
```

Once those five pieces click, Task 2 gets a lot less mysterious. You're essentially building a **very small TLS-like authenticated handshake**, except the professor has already specified all of the crypto primitives and wire format for you.

---

## User

export this chat to markdown
