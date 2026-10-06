import pytest

from secure_record import (
    seal,
    open_record,
    AuthenticationError,
)


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
