from agents import TResponseInputItem
from agents.memory.session import SessionABC

class InMemorySession(SessionABC):
    def __init__(self, items: list[TResponseInputItem] | None = None):
        self._items: list[TResponseInputItem] = items or []

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]:
        return self.get_items_sync(limit)
    
    def get_items_sync(self, limit: int | None = None) -> list[TResponseInputItem]:
        if limit is None:
            return self._items.copy()
        return self._items[-limit:]

    async def add_items(self, items: list[TResponseInputItem]) -> None:
        self._items.extend(items)

    async def pop_item(self) -> TResponseInputItem | None:
        if not self._items:
            return None
        return self._items.pop()

    async def clear_session(self) -> None:
        self._items.clear()


    