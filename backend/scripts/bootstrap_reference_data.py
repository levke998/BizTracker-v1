"""CLI entrypoint for idempotent reference data bootstrap."""

from __future__ import annotations

from app.bootstrap.reference_data import bootstrap_reference_data
from app.db.session import SessionLocal


def main() -> None:
    """Run the reference data bootstrap and print a short summary."""

    with SessionLocal() as session:
        summary = bootstrap_reference_data(session)

    print(
        "Reference data bootstrap completed "
        f"(created={summary.created_count}, updated={summary.updated_count})."
    )


if __name__ == "__main__":
    main()
