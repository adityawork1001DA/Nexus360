from pathlib import Path
import requests


DATASETS = {
    "predictive_maintenance.csv": (
        "https://synapseaisolutionsa.z13.web.core.windows.net/"
        "data/MachineFaultDetection/predictive_maintenance.csv"
    )
}


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(f"Downloading: {url}")

    response = requests.get(
        url,
        timeout=120,
    )

    response.raise_for_status()

    destination.write_bytes(response.content)

    size_mb = destination.stat().st_size / (1024 ** 2)

    print(
        f"Saved: {destination} "
        f"({size_mb:.2f} MB)"
    )


def main() -> None:
    base_directory = Path(
        "data/raw/microsoft"
    )

    for filename, url in DATASETS.items():
        destination = base_directory / filename

        if destination.exists():
            print(
                f"Already exists: {destination}"
            )
            continue

        download_file(
            url=url,
            destination=destination,
        )


if __name__ == "__main__":
    main()