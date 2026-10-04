import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


load_dotenv()


def get_engine() -> Engine:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "nexus360")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")

    if not password:
        raise RuntimeError(
            "POSTGRES_PASSWORD is not configured."
        )

    url = (
        f"postgresql+psycopg://"
        f"{user}:{password}@"
        f"{host}:{port}/{database}"
    )

    connect_args = {}

    if host not in {
        "localhost",
        "127.0.0.1",
    }:
        connect_args["sslmode"] = "require"

    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


def test_connection() -> bool:
    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT 1")
        )

        return result.scalar() == 1


if __name__ == "__main__":
    if test_connection():
        print(
            "NEXUS 360 PostgreSQL connection: OK"
        )