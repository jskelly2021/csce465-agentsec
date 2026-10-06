import pytest

from secure_record import (
    seal,
    open_record,
    DirectionError,
)


def test_reflected_record_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"gateway command",
        message_type=1,
    )

    # Attacker reflects Gateway's own outgoing record back toward Gateway.
    with pytest.raises(DirectionError):
        open_record(gateway_session, record)
