import pytest

from secure_record import (
    seal,
    open_record,
    SequenceError,
)

def test_replayed_record_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"perform action",
        message_type=1,
    )

    # First delivery is legitimate.
    _, plaintext = open_record(
        node_session,
        record,
    )

    assert plaintext == b"perform action"

    # Exact same authenticated record is replayed.
    with pytest.raises(SequenceError):
        open_record(node_session, record)
