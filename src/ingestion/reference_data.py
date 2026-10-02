COUNTRIES = [
    ("USA", "United States", "NAM", "USD"),
    ("CAN", "Canada", "NAM", "CAD"),
    ("BRA", "Brazil", "LATAM", "BRL"),

    ("GBR", "United Kingdom", "WEU", "GBP"),
    ("DEU", "Germany", "WEU", "EUR"),
    ("FRA", "France", "WEU", "EUR"),

    ("ARE", "United Arab Emirates", "MEA", "AED"),

    ("IND", "India", "IND", "INR"),

    ("SGP", "Singapore", "SEA", "SGD"),

    ("JPN", "Japan", "JPN", "JPY"),

    ("AUS", "Australia", "ANZ", "AUD"),
]


DATACENTERS_BY_REGION = {
    "NAM": [
        "DC-US-EAST",
        "DC-US-WEST",
    ],

    "LATAM": [
        "DC-US-EAST",
    ],

    "WEU": [
        "DC-EU-WEST",
    ],

    "MEA": [
        "DC-EU-WEST",
    ],

    "IND": [
        "DC-IND-CENTRAL",
    ],

    "SEA": [
        "DC-SEA",
    ],

    "JPN": [
        "DC-JPN",
    ],

    "ANZ": [
        "DC-ANZ",
    ],
}