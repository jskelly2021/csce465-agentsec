# Chat Export — CSCE 465 HW2 Task 2

**Date:** October 5, 2026

---

## User

I'm working on task two. Give me the code to generate the DH parameters from the group file. Then initialize Gateway and Node classes with the parameters. Include their longterm RSA signing key. Explain each step

---

## Assistant

Yep — this is a good place to start Task 2. The assignment wants both parties to use the same standardized `ffdhe3072` Diffie–Hellman group, while each party has its own long-term 3072-bit RSA signing key. Then, for each handshake session, they'll generate fresh ephemeral DH keys from those shared parameters.

The `ffdhe3072.pem` file itself should already have been created with OpenSSL during Lab Preparation.

Here's a clean starting point for `handshake.py`:

```python
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import dh, rsa


GROUP_FILE = Path("ffdhe3072.pem")
GROUP_ID = "ffdhe3072"


def load_dh_parameters(path: Path) -> dh.DHParameters:
    """
    Load the standardized finite-field DH parameters from the PEM group file.
    """
    with path.open("rb") as f:
        parameters = serialization.load_pem_parameters(f.read())

    if not isinstance(parameters, dh.DHParameters):
        raise TypeError("Group file does not contain DH parameters")

    return parameters


def generate_rsa_signing_key() -> rsa.RSAPrivateKey:
    """
    Generate a long-term 3072-bit RSA signing key.
    """
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=3072,
    )


class Gateway:
    def __init__(
        self,
        dh_parameters: dh.DHParameters,
        signing_key: rsa.RSAPrivateKey,
        node_public_key: rsa.RSAPublicKey,
    ):
        self.identity = "gateway"
        self.group_id = GROUP_ID

        self.dh_parameters = dh_parameters

        self.signing_key = signing_key
        self.public_signing_key = signing_key.public_key()

        self.peer_identity = "node"
        self.peer_public_key = node_public_key


class Node:
    def __init__(
        self,
        dh_parameters: dh.DHParameters,
        signing_key: rsa.RSAPrivateKey,
        gateway_public_key: rsa.RSAPublicKey,
    ):
        self.identity = "node"
        self.group_id = GROUP_ID

        self.dh_parameters = dh_parameters

        self.signing_key = signing_key
        self.public_signing_key = signing_key.public_key()

        self.peer_identity = "gateway"
        self.peer_public_key = gateway_public_key


def main():
    # 1. Load the common Diffie-Hellman group.
    dh_parameters = load_dh_parameters(GROUP_FILE)

    # 2. Create each party's long-term RSA signing key.
    gateway_signing_key = generate_rsa_signing_key()
    node_signing_key = generate_rsa_signing_key()

    # 3. Initialize each endpoint.
    gateway = Gateway(
        dh_parameters=dh_parameters,
        signing_key=gateway_signing_key,
        node_public_key=node_signing_key.public_key(),
    )

    node = Node(
        dh_parameters=dh_parameters,
        signing_key=node_signing_key,
        gateway_public_key=gateway_signing_key.public_key(),
    )

    print("Gateway and Node initialized")


if __name__ == "__main__":
    main()
```

### 1. Load the DH parameters

```python
parameters = serialization.load_pem_parameters(f.read())
```

Your `ffdhe3072.pem` contains the parameters defining the Diffie–Hellman group.

Conceptually, these include values like:

```text
p = large 3072-bit prime
g = generator
```

Both the Gateway and Node have to use the **same group**.

You're not creating their DH private/public keys yet. You're just loading the mathematical environment in which those keys will later be generated.

So think:

```text
ffdhe3072.pem
      |
      v
DH parameters
   /      \
Gateway   Node
```

The assignment specifically says to use the standardized `ffdhe3072` group and generate fresh DH private values for every session.

Later, during the handshake, each side will do something like:

```python
gateway_ephemeral_key = self.dh_parameters.generate_private_key()
```

and:

```python
node_ephemeral_key = self.dh_parameters.generate_private_key()
```

Those are the **session-specific ephemeral DH keys**.

### 2. Generate long-term RSA keys

```python
gateway_signing_key = generate_rsa_signing_key()
node_signing_key = generate_rsa_signing_key()
```

The assignment requires each party to have a long-term 3072-bit RSA signing key and use RSA-PSS with SHA-256 for signatures.

The important distinction is:

```text
RSA signing key
    long-term

DH private key
    fresh every handshake
```

So you **should not** do this inside the eventual handshake method:

```python
# BAD idea
def handshake(self):
    self.signing_key = rsa.generate_private_key(...)
```

That would make the RSA identity change every session.

Instead, generate it when setting up the endpoint:

```python
gateway_signing_key = generate_rsa_signing_key()
```

and then reuse it:

```python
Gateway(..., signing_key=gateway_signing_key)
```

### 3. Private key versus public key

An RSA key pair consists of:

```text
Private RSA key
       |
       +----> Public RSA key
```

The private key is used to **sign**:

```python
signature = private_key.sign(...)
```

The public key is used by the other side to **verify**:

```python
public_key.verify(...)
```

So the Gateway gets:

```python
self.signing_key
```

which is its private RSA key.

And:

```python
self.public_signing_key
```

which is its corresponding public key.

The Node gets its own completely separate pair.

### 4. Why give each party the other's public key?

This part:

```python
gateway = Gateway(
    ...
    node_public_key=node_signing_key.public_key(),
)
```

means:

```text
Gateway knows Node's trusted RSA public key
```

And:

```python
node = Node(
    ...
    gateway_public_key=gateway_signing_key.public_key(),
)
```

means:

```text
Node knows Gateway's trusted RSA public key
```

That's necessary for authentication.

Suppose Node receives:

```text
DH public value
nonce
identity = "gateway"
signature
```

Node needs to verify:

```text
Did the actual Gateway sign this?
```

It does that using:

```python
self.peer_public_key
```

The RSA keys authenticate the ephemeral DH exchange; they aren't used to encrypt your application data.

### 5. What the DH parameter object actually does

After initialization, both objects contain:

```python
self.dh_parameters
```

But they don't yet have a DH key pair.

During a handshake you'll generate one:

```python
self.dh_private_key = self.dh_parameters.generate_private_key()
self.dh_public_key = self.dh_private_key.public_key()
```

Conceptually:

```text
                  ffdhe3072 parameters
                         |
              +----------+----------+
              |                     |
           Gateway                 Node
              |                     |
        random private a       random private b
              |                     |
              v                     v
           g^a mod p             g^b mod p
```

They exchange the public values.

Then:

```text
Gateway computes: (g^b)^a mod p
Node computes:    (g^a)^b mod p

                    |
                    v
              same shared secret Z
```

The library handles that math for you — the homework explicitly says not to implement the DH arithmetic yourself.

### One small design detail I'd keep

Notice that I have:

```python
GROUP_ID = "ffdhe3072"
```

separately from:

```python
dh_parameters
```

That's intentional.

Later your transcript has to contain the literal group identifier:

```text
ffdhe3072
```

along with:

```text
CSCE465-HS-v2
gateway identity
node identity
gateway DH public value
node DH public value
gateway nonce
node nonce
```

So I'd treat:

```python
dh_parameters
```

as the cryptographic object used to generate keys, and:

```python
group_id = "ffdhe3072"
```

as the protocol-level name that eventually goes into the transcript.

At this point, your objects are essentially:

```text
Gateway
├── identity = "gateway"
├── group_id = "ffdhe3072"
├── DH parameters
├── Gateway RSA private key
├── Gateway RSA public key
└── trusted Node RSA public key

Node
├── identity = "node"
├── group_id = "ffdhe3072"
├── DH parameters
├── Node RSA private key
├── Node RSA public key
└── trusted Gateway RSA public key
```

That's a solid foundation for the next Task 2 step: **have each class generate its fresh ephemeral DH key pair and 16-byte nonce for a handshake session.**

---

## User

The node and gateway are using a trust store for the peer id and public key:

```python
class Node:
    def __init__(
        self,
        dh_parameters: dh.DHParameters,
        signing_key: rsa.RSAPrivateKey,
        trusted_peers: dict[str, rsa.RSAPublicKey],
    ):
        self.identity = "node"
        self.group_id = GROUP_ID

        self.dh_parameters = dh_parameters

        self.signing_key = signing_key
        self.public_signing_key = signing_key.public_key()

        self.trusted_peers = trusted_peers
```

Provide the code for the session handshake.

---

## Assistant

Yep — with a trust store, the peer’s RSA public key is already provisioned before the handshake. The handshake then uses that trusted key to authenticate the **fresh ephemeral DH exchange**. That lines up nicely with Task 2: fresh DH keys/nonces per session, canonical transcript, RSA-PSS signatures, then the assignment-specific KDF.

I’d structure it so both `Gateway` and `Node` reuse the same handshake machinery.

```python
from dataclasses import dataclass
import hashlib
import secrets

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.asymmetric import dh, padding, rsa


PROTOCOL_LABEL = b"CSCE465-HS-v2"
GROUP_ID = "ffdhe3072"

DH_WIDTH = 384  # 3072 bits / 8


@dataclass(frozen=True)
class HandshakeHello:
    identity: str
    group_id: str
    dh_public: bytes
    nonce: bytes


@dataclass(frozen=True)
class HandshakeSignature:
    role: bytes
    signature: bytes


@dataclass
class HandshakeState:
    """
    Private session state.

    Never send the DH private key to the peer.
    """
    dh_private_key: dh.DHPrivateKey
    hello: HandshakeHello


@dataclass(frozen=True)
class SessionKeys:
    k_g2n_enc: bytes
    k_g2n_mac: bytes
    k_n2g_enc: bytes
    k_n2g_mac: bytes
    session_id: bytes
    transcript_hash: bytes


def encode_field(value: bytes) -> bytes:
    """
    Canonical length-prefixed encoding:

        4-byte big-endian length || field
    """
    return len(value).to_bytes(4, "big") + value


def encode_dh_public(public_key: dh.DHPublicKey) -> bytes:
    """
    Encode a DH public value as exactly 384 bytes, as required by the HW.
    """
    y = public_key.public_numbers().y
    return y.to_bytes(DH_WIDTH, "big")


def decode_dh_public(
    encoded: bytes,
    parameters: dh.DHParameters,
) -> dh.DHPublicKey:
    """
    Convert the peer's 384-byte public value back into a cryptography
    DHPublicKey object.
    """
    if len(encoded) != DH_WIDTH:
        raise ValueError("Invalid DH public value length")

    y = int.from_bytes(encoded, "big")
    parameter_numbers = parameters.parameter_numbers()

    public_numbers = dh.DHPublicNumbers(
        y,
        parameter_numbers,
    )

    return public_numbers.public_key()


def build_transcript(
    gateway_hello: HandshakeHello,
    node_hello: HandshakeHello,
) -> bytes:
    """
    Build the transcript in ONE canonical order:

        protocol label
        group identifier
        gateway identity
        node identity
        gateway DH public value
        node DH public value
        gateway nonce
        node nonce
    """

    if gateway_hello.group_id != GROUP_ID:
        raise ValueError("Gateway used unexpected DH group")

    if node_hello.group_id != GROUP_ID:
        raise ValueError("Node used unexpected DH group")

    if len(gateway_hello.dh_public) != DH_WIDTH:
        raise ValueError("Invalid gateway DH public value")

    if len(node_hello.dh_public) != DH_WIDTH:
        raise ValueError("Invalid node DH public value")

    if len(gateway_hello.nonce) != 16:
        raise ValueError("Invalid gateway nonce")

    if len(node_hello.nonce) != 16:
        raise ValueError("Invalid node nonce")

    fields = [
        PROTOCOL_LABEL,
        GROUP_ID.encode("utf-8"),
        gateway_hello.identity.encode("utf-8"),
        node_hello.identity.encode("utf-8"),
        gateway_hello.dh_public,
        node_hello.dh_public,
        gateway_hello.nonce,
        node_hello.nonce,
    ]

    return b"".join(encode_field(field) for field in fields)


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def hmac_sha256(key: bytes, data: bytes) -> bytes:
    h = hmac.HMAC(key, hashes.SHA256())
    h.update(data)
    return h.finalize()


def derive_session_keys(
    shared_secret: bytes,
    transcript_hash: bytes,
) -> SessionKeys:

    if len(shared_secret) > DH_WIDTH:
        raise ValueError("DH shared secret is too large")

    z = shared_secret.rjust(DH_WIDTH, b"\x00")

    k_master = sha256(
        b"CSCE465-KDF-v1"
        + z
        + transcript_hash
    )

    k_g2n_enc = hmac_sha256(
        k_master,
        b"gateway-to-node encryption" + transcript_hash,
    )

    k_g2n_mac = hmac_sha256(
        k_master,
        b"gateway-to-node MAC" + transcript_hash,
    )

    k_n2g_enc = hmac_sha256(
        k_master,
        b"node-to-gateway encryption" + transcript_hash,
    )

    k_n2g_mac = hmac_sha256(
        k_master,
        b"node-to-gateway MAC" + transcript_hash,
    )

    session_id = hmac_sha256(
        k_master,
        b"session identifier" + transcript_hash,
    )[:8]

    return SessionKeys(
        k_g2n_enc=k_g2n_enc,
        k_g2n_mac=k_g2n_mac,
        k_n2g_enc=k_n2g_enc,
        k_n2g_mac=k_n2g_mac,
        session_id=session_id,
        transcript_hash=transcript_hash,
    )


class HandshakeParty:
    identity: str
    role: bytes
    peer_role: bytes

    def __init__(
        self,
        dh_parameters: dh.DHParameters,
        signing_key: rsa.RSAPrivateKey,
        trusted_peers: dict[str, rsa.RSAPublicKey],
    ):
        if signing_key.key_size != 3072:
            raise ValueError("RSA signing key must be 3072 bits")

        self.group_id = GROUP_ID
        self.dh_parameters = dh_parameters

        self.signing_key = signing_key
        self.public_signing_key = signing_key.public_key()

        self.trusted_peers = trusted_peers

    def start_handshake(self) -> HandshakeState:
        dh_private_key = self.dh_parameters.generate_private_key()
        dh_public_key = dh_private_key.public_key()

        nonce = secrets.token_bytes(16)

        hello = HandshakeHello(
            identity=self.identity,
            group_id=self.group_id,
            dh_public=encode_dh_public(dh_public_key),
            nonce=nonce,
        )

        return HandshakeState(
            dh_private_key=dh_private_key,
            hello=hello,
        )

    def sign_transcript(
        self,
        gateway_hello: HandshakeHello,
        node_hello: HandshakeHello,
    ) -> HandshakeSignature:

        transcript = build_transcript(
            gateway_hello,
            node_hello,
        )

        transcript_hash = sha256(transcript)
        message = self.role + transcript_hash

        signature = self.signing_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )

        return HandshakeSignature(
            role=self.role,
            signature=signature,
        )

    def finish_handshake(
        self,
        state: HandshakeState,
        peer_hello: HandshakeHello,
        peer_signature: HandshakeSignature,
        gateway_hello: HandshakeHello,
        node_hello: HandshakeHello,
    ) -> SessionKeys:

        if peer_hello.identity == self.identity:
            raise ValueError("Reflected/self handshake identity")

        peer_public_key = self.trusted_peers.get(peer_hello.identity)

        if peer_public_key is None:
            raise ValueError(
                f"Untrusted peer identity: {peer_hello.identity}"
            )

        if peer_signature.role != self.peer_role:
            raise ValueError("Unexpected or reflected handshake role")

        transcript = build_transcript(
            gateway_hello,
            node_hello,
        )

        transcript_hash = sha256(transcript)

        signed_message = (
            peer_signature.role
            + transcript_hash
        )

        try:
            peer_public_key.verify(
                peer_signature.signature,
                signed_message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH,
                ),
                hashes.SHA256(),
            )

        except InvalidSignature as exc:
            raise ValueError(
                "Invalid handshake signature"
            ) from exc

        peer_dh_public_key = decode_dh_public(
            peer_hello.dh_public,
            self.dh_parameters,
        )

        shared_secret = state.dh_private_key.exchange(
            peer_dh_public_key
        )

        return derive_session_keys(
            shared_secret,
            transcript_hash,
        )


class Gateway(HandshakeParty):
    identity = "gateway"
    role = b"gateway"
    peer_role = b"node"


class Node(HandshakeParty):
    identity = "node"
    role = b"node"
    peer_role = b"gateway"


def perform_handshake(
    gateway: Gateway,
    node: Node,
) -> tuple[SessionKeys, SessionKeys]:

    gateway_state = gateway.start_handshake()
    node_state = node.start_handshake()

    gateway_hello = gateway_state.hello
    node_hello = node_state.hello

    gateway_signature = gateway.sign_transcript(
        gateway_hello,
        node_hello,
    )

    node_signature = node.sign_transcript(
        gateway_hello,
        node_hello,
    )

    gateway_session = gateway.finish_handshake(
        state=gateway_state,
        peer_hello=node_hello,
        peer_signature=node_signature,
        gateway_hello=gateway_hello,
        node_hello=node_hello,
    )

    node_session = node.finish_handshake(
        state=node_state,
        peer_hello=gateway_hello,
        peer_signature=gateway_signature,
        gateway_hello=gateway_hello,
        node_hello=node_hello,
    )

    if gateway_session != node_session:
        raise RuntimeError(
            "Gateway and Node derived different session keys"
        )

    return gateway_session, node_session
```

Then your setup can look like:

```python
gateway_signing_key = generate_rsa_signing_key()
node_signing_key = generate_rsa_signing_key()

gateway_trust_store = {
    "node": node_signing_key.public_key(),
}

node_trust_store = {
    "gateway": gateway_signing_key.public_key(),
}

gateway = Gateway(
    dh_parameters,
    gateway_signing_key,
    gateway_trust_store,
)

node = Node(
    dh_parameters,
    node_signing_key,
    node_trust_store,
)

gateway_session, node_session = perform_handshake(
    gateway,
    node,
)

print("Session ID:", gateway_session.session_id.hex())
print("Handshake successful")
```

### What's happening

First, `start_handshake()` generates **session-specific** material:

```text
Gateway                         Node
   |                              |
fresh DH private key          fresh DH private key
fresh DH public value         fresh DH public value
fresh 16-byte nonce           fresh 16-byte nonce
```

Then both sides construct the exact same canonical transcript:

```text
length || "CSCE465-HS-v2"
length || "ffdhe3072"
length || gateway identity
length || node identity
length || gateway DH public
length || node DH public
length || gateway nonce
length || node nonce
```

Every field gets the required four-byte big-endian length prefix. The DH values are always encoded as exactly **384 bytes**.

Then the Gateway signs:

```text
"gateway" || SHA256(transcript)
```

while Node signs:

```text
"node" || SHA256(transcript)
```

The transcript is identical, but the **role being signed is different**.

When Node receives the Gateway signature, it does:

```python
peer_public_key = self.trusted_peers["gateway"]
```

and verifies the signature with the already-trusted Gateway RSA key.

Similarly:

```python
gateway.trusted_peers["node"]
```

is used to authenticate Node.

That means someone can't simply introduce:

```text
identity = "evil_gateway"
public_key = attacker's public key
```

during the handshake. There is no `"evil_gateway"` entry in the trust store, so:

```python
peer_public_key = self.trusted_peers.get(peer_hello.identity)

if peer_public_key is None:
    raise ValueError(...)
```

rejects it.

Once authentication succeeds, each side performs:

```python
shared_secret = my_dh_private.exchange(
    peer_dh_public
)
```

giving:

```text
Gateway                           Node

private a                         private b
   |                                 |
   |       public g^a, g^b           |
   +---------------------------------+
   |                                 |
(g^b)^a                         (g^a)^b
   |                                 |
   +------------ same Z -------------+
```

Finally, `derive_session_keys()` implements the KDF specified in the homework **exactly**, producing the four direction-specific keys and eight-byte session ID.

One design choice here will also make **Task 4 much easier**: keep `start_handshake()`, `sign_transcript()`, and `finish_handshake()` separate instead of hiding everything inside `perform_handshake()`. That lets your tests grab a legitimate `HandshakeHello` or signature, modify the nonce/public value/signature/role, and confirm that `finish_handshake()` rejects it.

---

## User

export this chat to markdown
