import pytest

from secure_record import (
    seal,
    open_record,
    AuthenticationError,
    HEADER_SIZE,
    IV_SIZE,
)


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
