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


def main():
    message = b'{"action":"READ","path":"notes.txt"}'

    key = os.urandom(32)
    initial_value = os.urandom(16)

    print("Plaintext:", message.decode())

    ciphertext = encrypt(key, initial_value, message)
    print("Encrypted:", ciphertext.hex())

    plaintext = decrypt(key, initial_value, ciphertext)
    print("Decrypted:", plaintext.decode())


if __name__ == "__main__":
    main()
