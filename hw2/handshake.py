from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import dh, rsa


GROUP_FILE = Path("ffdhe3072.pem")
GROUP_ID = "ffdhe3072"


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


class Gateway:
    def __init__(
        self,
        dh_parameters: dh.DHParameters,
        signing_key: rsa.RSAPrivateKey,
        trusted_peers: dict[str, rsa.RSAPublicKey],
    ):
        self.identity = "gateway"
        self.group_id = GROUP_ID

        self.dh_parameters = dh_parameters

        self.signing_key = signing_key
        self.public_signing_key = signing_key.public_key()
        
        self.trusted_peers=trusted_peers,


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


def main():
    print(f"\n{'=' * 40}\nINITIALIZING HANDSHAKE SIMULATION\n{'=' * 40}")

    dh_parameters = load_dh_parameters(GROUP_FILE)

    print(f"Loaded DH parameters from {GROUP_FILE} (group ID: {GROUP_ID})")

    gateway_signing_key = generate_rsa_signing_key()
    node_signing_key = generate_rsa_signing_key()

    print("Gateway and Node signing keys generated")

    gateway = Gateway(
        dh_parameters=dh_parameters,
        signing_key=gateway_signing_key,
        trusted_peers={
            "node": node_signing_key.public_key(),
        },
    )

    node = Node(
        dh_parameters=dh_parameters,
        signing_key=node_signing_key,
        trusted_peers={
            "gateway": gateway_signing_key.public_key(),
        },
    )

    print("Gateway and Node initialized")

    print("")


if __name__ == "__main__":
    main()
