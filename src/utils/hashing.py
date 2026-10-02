import hashlib


def create_record_hash(
    values: list,
) -> str:

    normalized = "|".join(
        ""
        if value is None
        else str(value).strip()
        for value in values
    )

    return hashlib.sha256(
        normalized.encode(
            "utf-8"
        )
    ).hexdigest()