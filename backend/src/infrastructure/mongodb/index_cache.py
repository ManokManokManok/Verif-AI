"""Run index creation once per client/database per process.

Repositories are rebuilt on every request, and each create_index call is a network
round-trip to Atlas. On a warm Lambda container this keeps them to the first request.
"""
from typing import Callable

_done: set = set()
_clients: dict = {}  # keeps clients alive so id() is never reused


def ensure_once(client, database_name: str, name: str, create: Callable[[], None]) -> None:
    key = (id(client), database_name, name)
    if key in _done:
        return
    create()
    _clients[id(client)] = client
    _done.add(key)
