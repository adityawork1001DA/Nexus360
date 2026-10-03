from __future__ import annotations

from src.ingestion.incremental_loader import (
    load_synthetic_incrementally,
)


def main() -> None:
    load_synthetic_incrementally()


if __name__ == "__main__":
    main()