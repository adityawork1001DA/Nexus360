import argparse

from scripts.run_sql import (
    execute_directory,
)


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "directory",
        help=(
            "Directory containing "
            "SQL files."
        ),
    )

    args = parser.parse_args()

    execute_directory(
        args.directory
    )


if __name__ == "__main__":
    main()