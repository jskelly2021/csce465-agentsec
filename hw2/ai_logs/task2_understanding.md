# Task 2 Handshake Architecture — Chat Export

## User

Help me refine my understanding and plan for task 2. I think the piece I'm missing is how everything should connect. We're simulating a handshake between two parties but in a single python script.

These two entities are the Gateway and the Node. I'm representing these as a class, each of which holds its respective information and secrets. This information includes:

- identity
- group id
- generated DH parameters
- long-term public and private RSS signing keys
- any trusted peers' identities and public keys

Now, we want to establish a session between these two parties. Is this session an entity itself or is it more of the relationship between the node and gateway? My current understanding is that the transcript we are generating is basically the session, or is owned by the session.

We can create a handshake function that takes both parties, `handshake(gateway, node)`, and returns the session. This handshake must generate the DH public values and fresh nonces. It creates a transcript, `session.transcript` which includes:

- protocol label - CSCE465-HS-v2
- group id - ffdhe3072
- both party ids
- DH public values
- nonces

Then, each party must verify the session. It does this by verifying the public peer RSA signature. Each party accepts or rejects the session then signs it's role + transcript hash.

Finally, we use the provided KDF to generate keys for the session. Where are these keys generated? By the session after it has been verified by the parties? Individually by each party? What are these keys used for? Do both parties need all keys?

Refine my understanding and current plan. Is my understanding correct? Am I overlooking or missing anything?

## Assistant

You’re very close. The main thing to straighten out is **who owns what**. Even though everything runs in one Python process, you want the code to preserve the illusion that Gateway and Node are actually separate machines communicating over a network.

The assignment explicitly describes this as a “local, in-process handshake between a simulated gateway and node,” so your `handshake(gateway, node)` coordinator is a perfectly reasonable structure.

The mental model I’d use is:

**Gateway ↔ handshake messages ↔ Node → shared Session**

The handshake function orchestrates that interaction, but it should avoid doing cryptographic work *on behalf of* the parties when that work would normally happen locally.

### First important correction: DH parameters are not generated per party

Your classes probably contain something like:

```text
Gateway
├── identity
├── DH group parameters (ffdhe3072)
├── RSA private signing key
├── RSA public signing key
└── trusted_peers
     └── node_id -> node RSA public key

Node
├── identity
├── DH group parameters (ffdhe3072)
├── RSA private signing key
├── RSA public signing key
└── trusted_peers
     └── gateway_id -> gateway RSA public key
```

But the **FFDHE parameters aren't a secret and aren't unique to Gateway/Node**. Both load the same standardized `ffdhe3072` group from the PEM file. What changes every session is each party's **ephemeral DH private/public key pair** and its nonce.

So I'd distinguish:

```text
Long-lived Party state
    RSA signing key
    identity
    trusted peer keys
    FFDHE group parameters

Per-handshake state
    ephemeral DH private key
    ephemeral DH public key
    nonce
```

That distinction will make the rest click.

### The Session versus the Transcript

I would absolutely make `Session` an entity, but **the transcript is not the session**.

Think of the transcript as:

> A canonical record of exactly what both sides agreed to during the handshake.

Something like:

```text
Transcript
    protocol = CSCE465-HS-v2
    group = ffdhe3072
    gateway_id
    node_id
    gateway_DH_public
    node_DH_public
    gateway_nonce
    node_nonce
```

The **session** is larger:

```text
Session
├── gateway identity
├── node identity
├── transcript
├── transcript hash
├── session_id
├── session keys
└── later: send/receive sequence numbers
```

So your instinct that the transcript is "owned by the session" makes sense.

I'd phrase the relationship as:

> **Handshake creates the transcript. Successful authentication of that transcript creates an established session.**

Before verification, it's really a *candidate handshake*, not yet a trusted session.

### One subtle but important change to your handshake design

You said:

> handshake must generate the DH public values and fresh nonces.

Conceptually, I'd change that to:

> `handshake()` asks each party to generate its own DH key pair and nonce.

Instead of this:

```python
def handshake(gateway, node):
    gateway_private = ...
    node_private = ...
```

think:

```python
gateway_state = gateway.begin_handshake()
node_state = node.begin_handshake()
```

Each party should own its secret DH private value.

The coordinator can see everything because this is a simulation, but your design should behave **as though it couldn't**.

### Authentication is the next phase

More precisely than “each party verifies the session”:

> **Each party verifies that the peer authenticated the same transcript.**

You calculate:

```text
TH = SHA256(transcript)
```

Then Gateway signs:

```text
"GATEWAY" || TH
```

and Node signs:

```text
"NODE" || TH
```

with their respective long-term RSA private keys.

Then Gateway verifies the Node signature with the trusted Node public key, and Node verifies the Gateway signature with the trusted Gateway public key.

### Why the role is there

The role isn't really part of your transcript fields. It's attached when signing:

```text
role || TH
```

That makes:

```text
NODE || TH
```

different from:

```text
GATEWAY || TH
```

even though both sides share the same `TH`.

That is one of the protections against reflection attacks.

### Key derivation

**The Session should not centrally generate the keys.**

In a real handshake, neither side sends the session keys to the other.

Instead:

```text
Gateway independently computes Z
Node independently computes Z
```

Gateway has its private DH key and the Node's public DH key, and Node has its private DH key and the Gateway's public DH key.

Diffie-Hellman guarantees:

```text
Z_gateway == Z_node
```

Then both sides independently run the exact same KDF.

No session key ever needs to cross the wire.

### When should the keys be derived?

A clean flow is:

```text
1. Generate ephemeral values
2. Build transcript
3. TH = SHA256(transcript)
4. Exchange signatures
5. Verify signatures and identities
6. Compute DH shared secret
7. Derive session keys
8. Mark session ESTABLISHED
```

You could compute `Z` earlier internally, but don't accept the session or use the resulting keys until authentication passes.

### Do both parties need all four keys?

Cryptographically, both parties can derive all four because they have the same `Z`, `TH`, and `K_master`.

Gateway:

```text
Sending:
    K_g2n_enc
    K_g2n_mac

Receiving:
    K_n2g_enc
    K_n2g_mac
```

Node:

```text
Sending:
    K_n2g_enc
    K_n2g_mac

Receiving:
    K_g2n_enc
    K_g2n_mac
```

A cleaner abstraction is to translate them locally:

```python
gateway_session.send_enc_key = K_g2n_enc
gateway_session.send_mac_key = K_g2n_mac
gateway_session.recv_enc_key = K_n2g_enc
gateway_session.recv_mac_key = K_n2g_mac
```

and for Node:

```python
node_session.send_enc_key = K_n2g_enc
node_session.send_mac_key = K_n2g_mac
node_session.recv_enc_key = K_g2n_enc
node_session.recv_mac_key = K_g2n_mac
```

### Suggested architecture

```text
Party
├── identity
├── group_id
├── dh_parameters
├── signing_private_key
├── signing_public_key
└── trusted_peers

Gateway(Party)

Node(Party)

HandshakeState
├── ephemeral_private_key
├── ephemeral_public_value
└── nonce

Transcript
├── canonical fields
├── encode()
└── hash()

Session
├── peer_identity
├── transcript
├── transcript_hash
├── session_id
├── send_enc_key
├── send_mac_key
├── recv_enc_key
├── recv_mac_key
├── send_sequence
└── recv_sequence
```

I’d lean toward returning **two local views of the same logical session**:

```python
gateway_session, node_session = handshake(gateway, node)
```

The biggest conceptual improvement is to treat `handshake()` as the network/orchestrator, not as a trusted third party doing the cryptography.

---

## User

This is a strong architecture. Clarify a couple things for me.

Firstly, I understand the long term information and the per handshake information:

```python
class Party:
    def __init__(
        self,
        identity: str,
        dh_parameters: dh.DHParameters,
        signing_key: rsa.RSAPrivateKey,
        trusted_peers: dict[str, rsa.RSAPublicKey],
    ):
        self.identity = identity
        self.group_id = GROUP_ID
        self.dh_parameters = dh_parameters
        self.signing_key = signing_key
        self.public_signing_key = signing_key.public_key()
        self.trusted_peers=trusted_peers,
```

I want to understand how the perhandshake data should be handled. Does this data become owned by the session, so we have `node_session.dh_public_key`. This seems like it makes sense because the information is session specific, but that depends on the role of session.

Secondly, the handshake function returns established sessions for the Gateway and Node. Each has the identical authenticated transcripts and can derive it's session keys. Who owns these sessions? Does this become `node.session` and `gateway.session` or do these sessions become different entities used by the respective party?

## Assistant

Yes — the cleanest architecture is to split **per-handshake data** into two categories: temporary handshake state and established session state.

Also, tiny Python catch first: this line has an accidental trailing comma:

```python
self.trusted_peers = trusted_peers,
```

That makes it a one-element tuple. You want:

```python
self.trusted_peers = trusted_peers
```

### 1. Who owns the per-handshake DH data?

I would **not** put all of it directly on `Session`.

Instead, introduce a short-lived `HandshakeState` owned locally by each party while the handshake is happening:

```python
@dataclass
class HandshakeState:
    dh_private_key: dh.DHPrivateKey
    dh_public_key: dh.DHPublicKey
    nonce: bytes
```

Conceptually:

```text
Party
├── identity
├── long-term RSA signing key
├── trusted peers
└── DH group parameters

        begins handshake
              ↓

HandshakeState
├── ephemeral DH private key
├── ephemeral DH public key
└── nonce
```

This object exists **only while negotiating the session**.

Once you've computed the shared secret `Z`, authenticated the transcript, and derived the session keys, you no longer need the ephemeral DH private key.

### What survives into the Session?

```text
Session
├── peer_identity
├── transcript
├── transcript_hash
├── session_id
├── send_enc_key
├── send_mac_key
├── recv_enc_key
├── recv_mac_key
├── send_sequence
└── recv_sequence
```

You don't really need:

```python
node_session.dh_public_key
```

because both DH public values are already contained in the authenticated transcript.

A useful rule:

> **HandshakeState = temporary secrets needed to CREATE a session**  
> **Transcript = permanent record of what was negotiated**  
> **Session = usable cryptographic state AFTER successful negotiation**

### 2. Who owns `gateway_session` and `node_session`?

There is **one logical session**:

```text
Gateway ←──── secure relationship ────→ Node
```

but there are **two local session states**:

```text
Gateway's view                   Node's view
---------------                  -----------
peer = Node                      peer = Gateway

send = g→n keys                  send = n→g keys
recv = n→g keys                  recv = g→n keys

send_seq = 0                     send_seq = 0
recv_seq = 0                     recv_seq = 0

same transcript                  same transcript
same TH                          same TH
same session_id                  same session_id
```

So:

```python
gateway_session, node_session = handshake(gateway, node)
```

is a good model.

I wouldn't necessarily attach one as `gateway.session`, because that implies a Gateway can only have one session. If you wanted parties to manage sessions, a more realistic design would be:

```python
gateway.sessions[session_id] = gateway_session
node.sessions[session_id] = node_session
```

But for this homework, keeping them as independent returned objects is simpler.

Suggested `Session`:

```python
@dataclass
class Session:
    local_identity: str
    peer_identity: str

    transcript: bytes
    transcript_hash: bytes
    session_id: bytes

    send_enc_key: bytes
    send_mac_key: bytes
    recv_enc_key: bytes
    recv_mac_key: bytes

    send_sequence: int = 0
    recv_sequence: int = 0
```

A good ownership rule is:

> **Party owns identity. HandshakeState owns ephemeral secrets. Transcript owns negotiated public facts. Session owns the resulting communication state.**

---

## User

Drop me the code to build the transcript. How do I encode it and hash it?

## Assistant

For this assignment, the transcript can just be a single canonical `bytes` object. The key rules are:

- fixed field order
- every field is bytes
- every field gets a 4-byte big-endian length prefix
- DH public values are always exactly 384 bytes
- hash the final encoded transcript with SHA-256

```python
import hashlib
import struct

PROTOCOL_LABEL = b"CSCE465-HS-v2"
GROUP_ID = b"ffdhe3072"

DH_PUBLIC_SIZE = 384  # 3072 bits / 8


def encode_field(value: bytes) -> bytes:
    """
    Encode one transcript field as:

        4-byte big-endian length || value
    """
    return struct.pack(">I", len(value)) + value


def encode_dh_public(public_key) -> bytes:
    """
    Encode an ffdhe3072 DH public value as exactly 384 bytes,
    big-endian, left-padded with zeroes when necessary.
    """
    y = public_key.public_numbers().y

    return y.to_bytes(
        DH_PUBLIC_SIZE,
        byteorder="big",
    )


def build_transcript(
    gateway,
    node,
    gateway_state,
    node_state,
) -> bytes:
    """
    Construct the canonical handshake transcript.

    Field order:
        1. protocol label
        2. group identifier
        3. gateway identity
        4. node identity
        5. gateway ephemeral DH public value
        6. node ephemeral DH public value
        7. gateway nonce
        8. node nonce
    """

    fields = [
        PROTOCOL_LABEL,
        GROUP_ID,
        gateway.identity.encode("utf-8"),
        node.identity.encode("utf-8"),
        encode_dh_public(gateway_state.dh_public_key),
        encode_dh_public(node_state.dh_public_key),
        gateway_state.nonce,
        node_state.nonce,
    ]

    return b"".join(encode_field(field) for field in fields)


def hash_transcript(transcript: bytes) -> bytes:
    """
    TH = SHA-256(transcript)
    """
    return hashlib.sha256(transcript).digest()
```

Then inside your handshake:

```python
gateway_state = gateway.begin_handshake()
node_state = node.begin_handshake()

transcript = build_transcript(
    gateway,
    node,
    gateway_state,
    node_state,
)

transcript_hash = hash_transcript(transcript)
```

Each field is encoded as:

```text
[length: 4 bytes][field data]
```

For example, `"gateway"` is 7 bytes, so it becomes:

```text
00 00 00 07 | 67 61 74 65 77 61 79
```

The complete transcript is:

```text
len(protocol)       || protocol
len(group)          || group
len(gateway_id)     || gateway_id
len(node_id)        || node_id
len(gateway_dh)     || gateway_dh
len(node_dh)        || node_dh
len(gateway_nonce)  || gateway_nonce
len(node_nonce)     || node_nonce
```

For `ffdhe3072`, DH public values should always use exactly 384 bytes:

```python
y.to_bytes(384, "big")
```

Then:

```python
TH = hashlib.sha256(transcript).digest()
```

Use `.digest()` for the raw 32-byte hash. `.hex()` is only useful for debugging output.

---

## User

Return generate the sign function for step 4.

## Assistant

For Step 4, your `Party.sign()` should sign exactly:

```text
role || SHA-256(transcript)
```

using that party’s **long-term RSA private key**, with RSA-PSS and SHA-256.

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding


GATEWAY_ROLE = b"gateway"
NODE_ROLE = b"node"


class Party:
    # ...

    def sign(self, role: bytes, transcript_hash: bytes) -> bytes:
        """
        Sign role || SHA-256(transcript) using this party's
        long-term RSA private signing key.
        """

        if role not in (GATEWAY_ROLE, NODE_ROLE):
            raise ValueError("Invalid handshake role")

        if len(transcript_hash) != 32:
            raise ValueError("Transcript hash must be 32 bytes")

        message = role + transcript_hash

        signature = self.signing_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )

        return signature
```

Then:

```python
th = hashlib.sha256(transcript).digest()

gateway_signature = gateway.sign(
    GATEWAY_ROLE,
    th,
)

node_signature = node.sign(
    NODE_ROLE,
    th,
)
```

Conceptually:

```text
Gateway:
    RSA-PSS-sign(
        gateway_private_key,
        b"gateway" || TH
    )

Node:
    RSA-PSS-sign(
        node_private_key,
        b"node" || TH
    )
```

Don't hash `role + TH` yourself again before calling `.sign()`. The `cryptography` RSA signing API applies the specified `SHA256()` internally as part of RSA-PSS.

---

## User

In the signature verification, how does one party know the other's role for them to verify their signature?

## Assistant

The key idea is: **the verifier does not learn the peer's role from the signature. It already knows what role the peer is supposed to have from the protocol context.**

If the Gateway is verifying a signature from the Node, it verifies:

```text
NODE_ROLE || TH
```

If the Node is verifying a signature from the Gateway, it verifies:

```text
GATEWAY_ROLE || TH
```

For example:

```python
GATEWAY_ROLE = b"gateway"
NODE_ROLE = b"node"

gateway_signature = gateway.sign(GATEWAY_ROLE, th)
node_signature = node.sign(NODE_ROLE, th)

gateway.verify_signature(
    peer_identity=node.identity,
    peer_role=NODE_ROLE,
    transcript_hash=th,
    signature=node_signature,
)

node.verify_signature(
    peer_identity=gateway.identity,
    peer_role=GATEWAY_ROLE,
    transcript_hash=th,
    signature=gateway_signature,
)
```

And:

```python
def verify_signature(
    self,
    peer_identity: str,
    peer_role: bytes,
    transcript_hash: bytes,
    signature: bytes,
) -> None:
    if peer_identity not in self.trusted_peers:
        raise ValueError(f"Unexpected peer identity: {peer_identity}")

    peer_public_key = self.trusted_peers[peer_identity]

    message = peer_role + transcript_hash

    peer_public_key.verify(
        signature,
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )
```

The role comes from the protocol context:

> The Gateway knows: “I'm the Gateway, therefore the other participant in this handshake is expected to authenticate as the Node.”

And vice versa.

A cleaner design is to make role part of the party's fixed configuration:

```python
class Party:
    def __init__(
        self,
        identity: str,
        role: bytes,
        ...
    ):
        self.identity = identity
        self.role = role
```

Then signing can simply use `self.role`.

Identity and role are different:

```text
identity = "sensor-17"
role     = NODE

identity = "main-gateway"
role     = GATEWAY
```

---

## User

provide the code for computing the shared secret, Z. Also provide the code for deriving the keys in the provided kdf in step 5. Z should not be exposed to the controller

## Assistant

If you want `Z` hidden from the handshake controller, the clean design is:

> **The controller supplies the peer's public DH key and transcript hash to the party. The party computes `Z`, immediately feeds it into the KDF, and returns only the derived key material.**

```python
import hashlib
import hmac
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric import dh


DH_SECRET_SIZE = 384  # ffdhe3072 = 3072 bits = 384 bytes


@dataclass(frozen=True)
class SessionKeys:
    g2n_enc: bytes
    g2n_mac: bytes
    n2g_enc: bytes
    n2g_mac: bytes
    session_id: bytes
```

Then put the shared-secret calculation and KDF **inside `Party`**:

```python
class Party:
    # ... __init__, sign(), verify_signature(), etc.

    def derive_session_keys(
        self,
        handshake_state: HandshakeState,
        peer_dh_public_key: dh.DHPublicKey,
        transcript_hash: bytes,
    ) -> SessionKeys:
        """
        Compute the DH shared secret locally and derive the session keys.

        Z is never returned to the handshake controller.
        """

        if len(transcript_hash) != 32:
            raise ValueError("Transcript hash must be 32 bytes")

        z = self._compute_shared_secret(
            handshake_state.dh_private_key,
            peer_dh_public_key,
        )

        keys = self._kdf(z, transcript_hash)

        return keys

    def _compute_shared_secret(
        self,
        private_key: dh.DHPrivateKey,
        peer_public_key: dh.DHPublicKey,
    ) -> bytes:
        """
        Compute the Diffie-Hellman shared secret Z and normalize it
        to the required 384-byte big-endian representation.
        """

        shared_secret = private_key.exchange(peer_public_key)

        if len(shared_secret) > DH_SECRET_SIZE:
            raise ValueError("DH shared secret is larger than expected")

        return shared_secret.rjust(DH_SECRET_SIZE, b"\x00")

    def _kdf(
        self,
        z: bytes,
        transcript_hash: bytes,
    ) -> SessionKeys:
        """
        Apply the assignment-provided KDF exactly.
        """

        if len(z) != DH_SECRET_SIZE:
            raise ValueError("Z must be exactly 384 bytes")

        k_master = hashlib.sha256(
            b"CSCE465-KDF-v1"
            + z
            + transcript_hash
        ).digest()

        def derive(label: bytes) -> bytes:
            return hmac.new(
                k_master,
                label + transcript_hash,
                hashlib.sha256,
            ).digest()

        k_g2n_enc = derive(b"gateway-to-node encryption")
        k_g2n_mac = derive(b"gateway-to-node MAC")
        k_n2g_enc = derive(b"node-to-gateway encryption")
        k_n2g_mac = derive(b"node-to-gateway MAC")

        session_id = derive(b"session identifier")[:8]

        return SessionKeys(
            g2n_enc=k_g2n_enc,
            g2n_mac=k_g2n_mac,
            n2g_enc=k_n2g_enc,
            n2g_mac=k_n2g_mac,
            session_id=session_id,
        )
```

Then the handshake controller only does:

```python
gateway_keys = gateway.derive_session_keys(
    gateway_state,
    node_state.dh_public_key,
    th,
)

node_keys = node.derive_session_keys(
    node_state,
    gateway_state.dh_public_key,
    th,
)
```

The controller never gets `z`.

A further architectural improvement would be to keep the DH private key entirely inside the `Party` instead of exposing it through `HandshakeState`, and return only a public handshake offer containing the identity, public DH key, and nonce.

---

## User

export this chat to markdown
