from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os


def encrypt(key: bytes, initial_value: bytes, plaintext: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CTR(initial_value))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return ciphertext


def decrypt(key: bytes, initial_value: bytes, ciphertext: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CTR(initial_value))
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext


def relay(ciphertext: bytes) -> bytes:
    print(f"Received Ciphertext: {ciphertext.hex()}")
    modified = bytearray(ciphertext)

    offset = len(b'{"action":"')
    original = b"READ"
    desired = b"PWND"

    delta = bytes(a ^ b for a, b in zip(original, desired))

    for i, d in enumerate(delta):
        modified[offset + i] ^= d

    def fmt(data: bytes) -> str:
        return " ".join(f"{b:02x}" for b in data)

    print(f"\nXOR Relation\n{"-" * 20}")
    print(f"Original bytes:   {fmt(original)}")
    print(f"Desired bytes:    {fmt(desired)}")
    print(f"XOR difference:   {fmt(delta)}")

    print(f"\nModified Ciphertext: {modified.hex()}")
    return bytes(modified)


class Sender:
    def __init__(self, key: bytes, initial_value: bytes):
        self.key = key
        self.iv = initial_value
        self.message = b'{"action":"READ","path":"notes.txt"}'

    def send(self) -> bytes:
        print(f"Plaintext Message:  {self.message.decode()}")

        ciphertext = encrypt(self.key, self.iv, self.message)

        print(f"Encrypted Message:  {ciphertext.hex()}")

        return ciphertext


class Receiver:
    def __init__(self, key: bytes, initial_value: bytes):
        self.key = key
        self.iv = initial_value

    def receive(self, ciphertext: bytes) -> None:
        print(f"Received Ciphertext:  {ciphertext.hex()}")

        plaintext = decrypt(self.key, self.iv, ciphertext)
        print(f"Decrypted Message:    {plaintext.decode()}")


def main():
    key = os.urandom(32)
    initial_value = os.urandom(16)

    sender = Sender(key=key, initial_value=initial_value)
    receiver = Receiver(key=key, initial_value=initial_value)

    print(f"\nSender and Receiver initialized with same key and initial value.")

    print(f"\nSENDER\n{"=" * 40}")
    ciphertext = sender.send()

    print(f"\nRELAY\n{"=" * 40}")
    modified_ciphertext = relay(ciphertext)

    print(f"\nRECEIVER\n{"=" * 40}")
    receiver.receive(modified_ciphertext)

    print("")


if __name__ == "__main__":
    main()
