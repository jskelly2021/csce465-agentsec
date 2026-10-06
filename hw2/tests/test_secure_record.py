from secure_record import seal, open_record


def test_valid_bidirectional_messages(sessions):
    gateway_session, node_session = sessions

    gateway_message = b"Hello, Node"
    record = seal(
        gateway_session,
        gateway_message,
        message_type=1,
    )

    message_type, plaintext = open_record(
        node_session,
        record,
    )

    assert message_type == 1
    assert plaintext == gateway_message

    node_message = b"Hello, Gateway"
    record = seal(
        node_session,
        node_message,
        message_type=2,
    )

    message_type, plaintext = open_record(
        gateway_session,
        record,
    )

    assert message_type == 2
    assert plaintext == node_message
