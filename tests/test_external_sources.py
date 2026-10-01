import requests


def test_world_bank():
    url = (
        "https://api.worldbank.org/v2/"
        "country/USA/indicator/NY.GDP.MKTP.CD"
    )

    response = requests.get(
        url,
        params={"format": "json"},
        timeout=30,
    )

    assert response.status_code == 200


def test_open_meteo():
    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": 47.6062,
        "longitude": -122.3321,
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
        "daily": "temperature_2m_mean",
        "timezone": "UTC",
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    assert response.status_code == 200


def test_frankfurter():
    response = requests.get(
        "https://api.frankfurter.dev/v2/rates",
        timeout=30,
    )

    assert response.status_code == 200