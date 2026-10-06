# Chat Export — CSCE 465 HW2 Task 2 Handshake

## User

My current implementation for task 2:

```python
import os
import hashlib
import struct
import hmac

from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import dh, rsa, padding


PROTOCOL_LABEL = b"CSCE465-HS-v2"
GROUP_ID = b"ffdhe3072"
GROUP_FILE = Path("ffdhe3072.pem")

DH_VALUE_SIZE = 384

GATEWAY_IDENTITY = "gateway"
GATEWAY_ROLE = "gateway"
NODE_IDENTITY = "node"
NODE_ROLE = "node"


def load_dh_parameters(path: Path) -> dh.DHParameters:
    """
    Load the finite-field DH parameters from the PEM group file.
    """
    with path.open("rb") as f:
        parameters = serialization.load_pem_parameters(f.read())

    if not isinstance(parameters, dh.DHParameters):
        raise TypeError("Group file does not contain DH parameters")

    return parameters


def generate_rsa_signing_key() -> rsa.RSAPrivateKey:
    """
    Generate 3072-bit RSA signing key.
    """
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=3072,
    )


def encode_field(value: bytes) -> bytes:
    """
    Encode one transcript field as:

        4-byte big-endian length || value
    """
    return struct.pack(">I", len(value)) + value


def encode_dh_public(public_key: dh.DHPublicKey) -> bytes:
    """
    Encode an ffdhe3072 DH public value as exactly 384 bytes,
    big-endian, left-padded with zeroes when necessary.
    """
    y = public_key.public_numbers().y

    return y.to_bytes(
        DH_VALUE_SIZE,
        byteorder="big",
    )


def build_transcript(
    gateway_identity: str,
    node_identity: str,
    gateway_dh_pub_key: bytes,
    node_dh_pub_key: bytes,
    gateway_nonce: bytes,
    node_nonce: bytes
) -> bytes:
    """
    Encodes the transcript as its fields concatenated together, 
    each preceded by its length as a 4-byte big-endian integer.
    """
    fields = [
        PROTOCOL_LABEL,
        GROUP_ID,
        gateway_identity.encode("utf-8"),
        node_identity.encode("utf-8"),
        encode_dh_public(gateway_dh_pub_key),
        encode_dh_public(node_dh_pub_key),
        gateway_nonce,
        node_nonce,
    ]

    return b"".join(encode_field(field) for field in fields)


def kdf(z: bytes, transcript_hash: bytes) -> SessionKeys:
    """
    Apply the KDF.
    """
    if len(z) != DH_VALUE_SIZE:
        raise ValueError("Z must be exactly 384 bytes")

    # K_master = SHA-256("CSCE465-KDF-v1" || Z || TH)
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


@dataclass(frozen=True)
class SessionKeys:
    g2n_enc: bytes
    g2n_mac: bytes
    n2g_enc: bytes
    n2g_mac: bytes
    session_id: bytes


@dataclass
class Session:
    session_id: bytes
    send_enc_key: bytes
    send_mac_key: bytes
    recv_enc_key: bytes
    recv_mac_key: bytes


@dataclass(frozen=True)
class Hello:
    identity: str
    dh_public_key: dh.DHPublicKey
    nonce: bytes


class Party:
    def __init__(
        self,
        identity: str,
        role: str,
        dh_parameters: dh.DHParameters,
        signing_key: rsa.RSAPrivateKey,
        trusted_peers: dict[str, rsa.RSAPublicKey],
        peer_role: str,
    ):
        self.identity = identity
        self.role = role
        self.group_id = GROUP_ID
        self.dh_parameters = dh_parameters
        self.signing_key = signing_key
        self.public_signing_key = signing_key.public_key()
        self.trusted_peers=trusted_peers
        self.peer_role = peer_role

        # per-handshake state
        self.dh_private_key = None
        self.dh_public_key = None
        self.nonce = None
        self.shared_secret = None

    def hello(self) -> Hello:
        """
        Generate a Hello containing the party identity, a fresh DH public key, 
        and a random 16 byte nonce.
        """
        self.dh_private_key = self.dh_parameters.generate_private_key()
        self.dh_public_key = self.dh_private_key.public_key()
        self.nonce = os.urandom(16)

        print(f"[*] Sending {self.identity} hello")

        return Hello(
            identity=self.identity,
            dh_public_key=self.dh_public_key,
            nonce=self.nonce
        )

    def sign(self, transcript_hash: bytes) -> bytes:
        """
        Sign role + transcript hash.
        """
        message = self.role.encode() + transcript_hash

        signature = self.signing_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )

        return signature

    def verify_signature(
        self,
        peer_identity: str,
        transcript_hash: bytes,
        signature: bytes,
    ) -> None:
        if peer_identity not in self.trusted_peers:
            raise ValueError(f"Unexpected peer identity: {peer_identity}")

        peer_public_key = self.trusted_peers[peer_identity]

        message = self.peer_role.encode() + transcript_hash

        peer_public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )


    def derive_session_keys(
        self,
        peer_dh_public_key: dh.DHPublicKey,
        transcript_hash: bytes,
    ) -> SessionKeys:
        """
        Compute the DH shared secret and derive the session keys.
        """

        if len(transcript_hash) != 32:
            raise ValueError("Transcript hash must be 32 bytes")

        shared_secret = self.dh_private_key.exchange(peer_dh_public_key)

        if len(shared_secret) > DH_VALUE_SIZE:
            raise ValueError("DH shared secret is larger than expected")

        z = shared_secret.rjust(DH_VALUE_SIZE, b"\x00")

        keys = kdf(z, transcript_hash)

        return keys


def handshake(gateway: Party, node: Party) -> tuple[Session, Session]:
    """
    Perform the handshake between the gateway and node. 
    returns the established sessions for each party.
    """
    print(f"\nBeginning handshake between Gateway and Node")
    print(f"{'=' * 60}")

    gateway_hello = gateway.hello()
    node_hello = node.hello()

    transcript = build_transcript(
        gateway_hello.identity,
        node_hello.identity,
        gateway_hello.dh_public_key,
        node_hello.dh_public_key,
        gateway_hello.nonce,
        node_hello.nonce,
    )

    th = hashlib.sha256(transcript).digest()

    print(f"[*] Constructed transcript and computed transcript hash (th): {th.hex()}")

    gateway_signature = gateway.sign(transcript_hash=th)
    node_signature = node.sign(transcript_hash=th)

    gateway.verify_signature(
        peer_identity=node.identity,
        transcript_hash=th,
        signature=node_signature,
    )

    node.verify_signature(
        peer_identity=gateway.identity,
        transcript_hash=th,
        signature=gateway_signature,
    )

    gateway_keys = gateway.derive_session_keys(
        node_hello.dh_public_key,
        th,
    )

    node_keys = node.derive_session_keys(
        gateway_hello.dh_public_key,
        th,
    )

    gateway_session = Session(
        session_id=gateway_keys.session_id,
        send_enc_key=gateway_keys.g2n_enc,
        send_mac_key=gateway_keys.g2n_mac,
        recv_enc_key=gateway_keys.n2g_enc,
        recv_mac_key=gateway_keys.n2g_mac
    )

    node_session = Session(
        session_id=node_keys.session_id,
        send_enc_key=node_keys.n2g_enc,
        send_mac_key=node_keys.n2g_mac,
        recv_enc_key=node_keys.g2n_enc,
        recv_mac_key=node_keys.g2n_mac
    )

    print(f"[*] Sessions established")

    return gateway_session, node_session


def main():
    dh_parameters = load_dh_parameters(GROUP_FILE)

    print(f"[*] Loaded DH parameters from {GROUP_FILE} (group ID: {GROUP_ID})")

    gateway_signing_key = generate_rsa_signing_key()
    node_signing_key = generate_rsa_signing_key()

    print(f"[*] Generated RSA signing keys for Gateway and Node")

    gateway = Party(
        identity=GATEWAY_IDENTITY,
        role=GATEWAY_ROLE,
        dh_parameters=dh_parameters,
        signing_key=gateway_signing_key,
        trusted_peers={
            NODE_IDENTITY: node_signing_key.public_key(),
        },
        peer_role=NODE_ROLE
    )

    node = Party(
        identity=NODE_IDENTITY,
        role=NODE_ROLE,
        dh_parameters=dh_parameters,
        signing_key=node_signing_key,
        trusted_peers={
            GATEWAY_IDENTITY: gateway_signing_key.public_key(),
        },
        peer_role=GATEWAY_ROLE
    )

    print(f"[*] Initialized Gateway and Node")

    gateway_session, node_session = handshake(gateway, node)



    print("")


if __name__ == "__main__":
    main()
```

Analyze it for correctness given the instructions. What means task 2 is finished? What should the script output?

---

## Assistant

You’re pretty close. The core cryptographic construction matches Task 2 well, but I would **not call it finished yet**. There are a couple of concrete correctness issues and one protocol-structure issue that matters for the assignment’s rejection requirements.

The assignment wants: long-term 3072-bit RSA-PSS/SHA-256 signing keys, fresh ffdhe3072 ephemeral keys and 16-byte nonces, the exact canonical length-prefixed transcript, signatures over `role || SHA-256(transcript)`, the supplied KDF, and rejection of malformed/tampered/reflected handshakes.

### First: one bug prevents this exact script from running

You define:

```python
def kdf(z: bytes, transcript_hash: bytes) -> SessionKeys:
```

before `SessionKeys` exists.

Unless you're using postponed annotations, Python will encounter `SessionKeys` while defining `kdf()` and raise a `NameError`.

Either move the dataclass above `kdf()`, or quote the annotation:

```python
def kdf(z: bytes, transcript_hash: bytes) -> "SessionKeys":
```

There's also a type annotation mismatch in `build_transcript()`: the DH key parameters should be `dh.DHPublicKey`, not `bytes`.

### Cryptographically, most of your happy path is correct

Your implementation correctly:

- Loads `ffdhe3072.pem`.
- Generates 3072-bit RSA signing keys.
- Generates fresh ephemeral DH keys and 16-byte nonces.
- Encodes DH public values as exactly 384-byte big-endian values.
- Uses the required transcript field order and 4-byte big-endian length prefixes.
- Computes `TH = SHA-256(transcript)`.
- Signs `role || TH` with RSA-PSS/SHA-256.
- Computes DH through the library.
- Left-pads the DH shared secret to 384 bytes.
- Implements the assignment KDF labels.
- Maps gateway-to-node and node-to-gateway keys correctly into the two sessions.

### The biggest correctness problem: you're checking the wrong identity

You currently use the known `Party` identity:

```python
gateway.verify_signature(
    peer_identity=node.identity,
```

instead of the received Hello identity. That should be:

```python
gateway.verify_signature(
    peer_identity=node_hello.identity,
    transcript_hash=th,
    signature=node_signature,
)

node.verify_signature(
    peer_identity=gateway_hello.identity,
    transcript_hash=th,
    signature=gateway_signature,
)
```

That way the received identity is actually authenticated.

### The subtler issue is that both parties currently share one transcript

Right now `handshake()` constructs one transcript and both parties sign the same centrally produced hash.

For the happy path that's fine, but it makes it difficult to model tampering correctly. A more faithful simulation has each endpoint construct the canonical transcript from its own sent and received handshake values.

On an untampered exchange the transcripts are identical. If a relay modifies a nonce or public value, the two transcript hashes differ and signature verification fails.

### Malformed transcript handling is the other unfinished requirement

`encode_field()` always creates correct lengths, but the assignment also requires malformed declared lengths to be rejected before hashing.

A small transcript parser/validator can walk through each `length || value` field, ensure the bytes actually exist, verify the expected number of fields, and reject trailing or missing data.

### When I would call Task 2 finished

Task 2 is essentially finished when:

1. `handshake.py` runs successfully with `ffdhe3072.pem`.
2. RSA keys are long-term while DH keys/nonces are fresh per session.
3. The canonical transcript is encoded exactly as required.
4. Each endpoint independently obtains the same transcript hash on a valid exchange.
5. Both RSA-PSS signatures verify.
6. Both endpoints derive the same session ID.
7. Gateway send keys equal Node receive keys and vice versa.
8. Unexpected identities, changed nonce/DH values, invalid signatures, malformed transcript lengths, and reflection are rejected.
9. A new handshake produces fresh ephemeral state and a different session ID.
10. The `Session` objects are ready for Task 3.

### Suggested output

```text
[*] Loaded DH parameters from ffdhe3072.pem (group ID: ffdhe3072)
[*] Generated long-term RSA signing keys for Gateway and Node
[*] Initialized Gateway and Node

Beginning handshake between Gateway and Node
============================================================
[*] Gateway generated fresh DH key pair and 16-byte nonce
[*] Node generated fresh DH key pair and 16-byte nonce
[*] Gateway constructed transcript
[*] Node constructed transcript
[*] Transcript hashes match
[*] Gateway signed transcript hash
[*] Node signed transcript hash
[*] Gateway verified Node RSA-PSS signature
[*] Node verified Gateway RSA-PSS signature
[*] Gateway derived session keys
[*] Node derived session keys
[*] Session IDs match: 8f12a9c3...
[*] Gateway send keys match Node receive keys
[*] Node send keys match Gateway receive keys
[*] Sessions established successfully
```

Avoid printing DH private keys, the DH shared secret, `K_master`, encryption keys, MAC keys, or RSA private keys.

---

## User

I agree that each party should build its own transcript. The assignment does explicitly say `Construct one canonical transcript` Am I interpreting this incorrectly?

---

## Assistant

I think your interpretation is right, with one subtle distinction:

**“Construct one canonical transcript” means there is one uniquely defined transcript format and one logical transcript for the handshake—not that your program should literally construct it only once and hand the same byte string to both parties.**

Conceptually, both parties independently construct:

```text
Transcript =
    protocol_label
    group_id
    gateway_identity
    node_identity
    gateway_dh_public
    node_dh_public
    gateway_nonce
    node_nonce
```

using exactly the same encoding rules.

For an untampered handshake:

```text
Gateway transcript == Node transcript
Gateway TH         == Node TH
```

That is what “canonical” buys you: given the same handshake data, there is exactly one valid byte representation.

The better architecture is therefore something like:

```python
gateway_transcript = build_transcript(
    gateway_hello.identity,
    node_hello_received.identity,
    gateway_hello.dh_public_key,
    node_hello_received.dh_public_key,
    gateway_hello.nonce,
    node_hello_received.nonce,
)

node_transcript = build_transcript(
    gateway_hello_received.identity,
    node_hello.identity,
    gateway_hello_received.dh_public_key,
    node_hello.dh_public_key,
    gateway_hello_received.nonce,
    node_hello.nonce,
)
```

Both use the **same canonical transcript definition**, but each party constructs it from **its own view of the exchange**.

If a relay modifies the Node nonce, then the Node and Gateway transcript hashes differ, and RSA verification fails.

So I would phrase the requirement as:

> There is **one canonical transcript specification**, and each endpoint independently constructs its copy of that transcript from the handshake messages it sent and received.

You should keep one shared `build_transcript()` function; just call it separately from each endpoint's perspective.

---

## User

My updated handshake:

```python
def handshake(gateway: Party, node: Party) -> tuple[Session, Session]:
    """
    Perform the handshake between the gateway and node. 
    returns the established sessions for each party.
    """
    print(f"\nBeginning handshake between Gateway and Node")
    print(f"{'=' * 60}")

    gateway_hello = gateway.hello()
    node_hello = node.hello()

    gateway_transcript = build_transcript(
        gateway_hello.identity,
        node_hello.identity,
        gateway_hello.dh_public_key,
        node_hello.dh_public_key,
        gateway_hello.nonce,
        node_hello.nonce
    )

    print(f"[*] {GATEWAY_IDENTITY} constructed transcript")

    node_transcript = build_transcript(
        gateway_hello.identity,
        node_hello.identity,
        gateway_hello.dh_public_key,
        node_hello.dh_public_key,
        gateway_hello.nonce,
        node_hello.nonce
    )

    print(f"[*] {NODE_IDENTITY} constructed transcript")

    assert gateway.hash_transcript(gateway_transcript) == node.hash_transcript(node_transcript)

    print(f"[*] Transcript hashes match")

    gateway_signature = gateway.sign()
    node_signature = node.sign()

    gateway.verify_signature(
        peer_identity=node_hello.identity,
        signature=node_signature,
    )
    node.verify_signature(
        peer_identity=gateway_hello.identity,
        signature=gateway_signature,
    )

    gateway_keys = gateway.derive_session_keys(
        node_hello.dh_public_key,
    )
    node_keys = node.derive_session_keys(
        gateway_hello.dh_public_key,
    )

    gateway_session = Session(
        session_id=gateway_keys.session_id,
        send_enc_key=gateway_keys.g2n_enc,
        send_mac_key=gateway_keys.g2n_mac,
        recv_enc_key=gateway_keys.n2g_enc,
        recv_mac_key=gateway_keys.n2g_mac
    )

    node_session = Session(
        session_id=node_keys.session_id,
        send_enc_key=node_keys.n2g_enc,
        send_mac_key=node_keys.n2g_mac,
        recv_enc_key=node_keys.g2n_enc,
        recv_mac_key=node_keys.g2n_mac
    )

    assert gateway_keys.session_id == node_keys.session_id

    print(f"[*] Session IDs match: {node_keys.session_id.hex()}")

    assert gateway_session.send_enc_key == node_session.recv_enc_key
    assert gateway_session.send_mac_key == node_session.recv_mac_key

    print(f"[*] Gateway send keys match Node receive keys")

    assert node_session.send_enc_key == gateway_session.recv_enc_key
    assert node_session.send_mac_key == gateway_session.recv_mac_key

    print(f"[*] Node send keys match Gateway receive keys")

    print(f"[*] Sessions established successfully")

    return gateway_session, node_session
```

each party builds a transcript then holds onto the hash and reuses it in the signing, verification key derivation.

---

## Assistant

Yep — this is a cleaner design. Having each `Party` store its own transcript hash and then internally reuse it for signing, verification, and KDF makes the responsibilities much more natural.

There are two important tweaks I’d make.

First, **don’t compute the hashes inside an `assert`**:

```python
assert gateway.hash_transcript(gateway_transcript) == node.hash_transcript(node_transcript)
```

If Python is run with optimization (`python -O`), assertions are removed entirely, which would mean `hash_transcript()` never runs and neither party gets its transcript hash.

Do this instead:

```python
gateway_th = gateway.hash_transcript(gateway_transcript)
node_th = node.hash_transcript(node_transcript)

assert gateway_th == node_th

print("[*] Transcript hashes match")
```

Or, for protocol-level rejection:

```python
if gateway_th != node_th:
    raise ValueError("Transcript hashes do not match")
```

The same rule applies to later assertions: assertions are good development sanity checks, but not security-critical rejection logic.

Second, although you're now calling `build_transcript()` twice, both parties still build from the **same objects**:

```python
gateway_hello
node_hello
```

So the computation is separate, but their views are not yet independently represented.

For the happy path, that's fine. For adversarial testing, introduce separate sent and received Hello values so a relay can modify one endpoint's view without changing the sender's original state.

Conceptually:

```python
gateway_hello = gateway.hello()
node_hello = node.hello()

gateway_received_node_hello = node_hello
node_received_gateway_hello = gateway_hello
```

Then construct the Gateway transcript from `gateway_hello` plus `gateway_received_node_hello`, and the Node transcript from `node_received_gateway_hello` plus `node_hello`.

If a relay modifies one received Hello, the transcript hashes differ. You do not actually need an explicit transcript-hash comparison for security: the peer's RSA signature will fail against the local endpoint's different transcript hash.

Your stateful `Party` design now has a nice flow:

```text
hello()
    ↓
fresh DH private/public key + nonce stored

hash_transcript()
    ↓
own transcript hash stored

sign()
    ↓
uses own role + own stored TH

verify_signature()
    ↓
uses expected peer role + own stored TH

derive_session_keys()
    ↓
uses own DH private key + peer public key + own stored TH
```

That is cleaner than passing the transcript hash into every method.

I would also add guards such as:

```python
def sign(self) -> bytes:
    if self.transcript_hash is None:
        raise ValueError("Transcript hash has not been computed")
```

and similar checks in key derivation.

So yes: **the stateful-hash change is an improvement.** Fix the hash-inside-`assert` issue now, and introduce separate sent-versus-received Hello variables when you build the adversarial tests.
