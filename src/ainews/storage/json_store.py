"""JSON file storage with file locking."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Generic, TypeVar

from filelock import FileLock
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class JsonEncoder(json.JSONEncoder):
    """Custom JSON encoder for Pydantic models and datetime objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, BaseModel):
            return obj.model_dump(mode="json")
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


class JsonStore(Generic[T]):
    """Generic JSON file storage with file locking."""

    def __init__(self, file_path: Path, model_class: type[T]):
        self.file_path = file_path
        self.model_class = model_class
        self.lock = FileLock(f"{file_path}.lock")

    def _ensure_parent(self) -> None:
        """Ensure parent directory exists."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[T]:
        """Load all items from the JSON file."""
        with self.lock:
            if not self.file_path.exists():
                return []
            try:
                data = json.loads(self.file_path.read_text(encoding="utf-8"))
                items = data.get("items", [])
                return [self.model_class.model_validate(item) for item in items]
            except (json.JSONDecodeError, KeyError):
                return []

    def save(self, items: list[T]) -> None:
        """Save all items to the JSON file."""
        self._ensure_parent()
        with self.lock:
            data = {
                "items": [item.model_dump(mode="json") for item in items],
                "metadata": {
                    "count": len(items),
                    "last_updated": datetime.utcnow().isoformat(),
                },
            }
            self.file_path.write_text(
                json.dumps(data, indent=2, cls=JsonEncoder),
                encoding="utf-8",
            )

    def append(self, item: T) -> None:
        """Append a single item to the store."""
        items = self.load()
        items.append(item)
        self.save(items)

    def get_by_id(self, item_id: str, id_field: str = "id") -> T | None:
        """Get an item by its ID."""
        items = self.load()
        for item in items:
            if getattr(item, id_field, None) == item_id:
                return item
        return None

    def update(self, item_id: str, updated_item: T, id_field: str = "id") -> bool:
        """Update an existing item by ID."""
        items = self.load()
        for i, item in enumerate(items):
            if getattr(item, id_field, None) == item_id:
                items[i] = updated_item
                self.save(items)
                return True
        return False

    def delete(self, item_id: str, id_field: str = "id") -> bool:
        """Delete an item by ID."""
        items = self.load()
        original_count = len(items)
        items = [item for item in items if getattr(item, id_field, None) != item_id]
        if len(items) < original_count:
            self.save(items)
            return True
        return False

    def exists(self, item_id: str, id_field: str = "id") -> bool:
        """Check if an item exists."""
        return self.get_by_id(item_id, id_field) is not None


class DatePartitionedStore(Generic[T]):
    """JSON storage partitioned by date (one file per day)."""

    def __init__(self, directory: Path, model_class: type[T]):
        self.directory = directory
        self.model_class = model_class

    def _get_store(self, target_date: date) -> JsonStore[T]:
        """Get the store for a specific date."""
        file_path = self.directory / f"{target_date.isoformat()}.json"
        return JsonStore(file_path, self.model_class)

    def load(self, target_date: date) -> list[T]:
        """Load items for a specific date."""
        return self._get_store(target_date).load()

    def save(self, target_date: date, items: list[T]) -> None:
        """Save items for a specific date."""
        self._get_store(target_date).save(items)

    def append(self, target_date: date, item: T) -> None:
        """Append an item to a specific date."""
        self._get_store(target_date).append(item)

    def list_dates(self) -> list[date]:
        """List all dates with stored data."""
        if not self.directory.exists():
            return []
        dates = []
        for file_path in self.directory.glob("*.json"):
            try:
                dates.append(date.fromisoformat(file_path.stem))
            except ValueError:
                continue
        return sorted(dates, reverse=True)
