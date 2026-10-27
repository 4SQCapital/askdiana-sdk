import socket

from askdiana.cli import _next_free_port, _port_in_use


def _listen():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    return s, s.getsockname()[1]


def test_a_port_with_a_server_is_in_use_and_a_closed_one_is_not():
    s, port = _listen()
    try:
        assert _port_in_use(port)
    finally:
        s.close()
    assert not _port_in_use(port)


def test_the_next_free_port_skips_busy_ones():
    first, port = _listen()
    try:
        free = _next_free_port(port - 1)
        assert free is not None and free != port and free >= port - 1
    finally:
        first.close()
