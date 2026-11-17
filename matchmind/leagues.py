"""Fixed league sources and artifact locations; user input never becomes a path."""
DEFAULT_LEAGUE = "premier-league"
SOURCE_COMMIT = "e6744429ee395bc86f247348c6184bb08d4eb361"
LEAGUES = {
    "premier-league": {
        "name": "Premier League", "source_file": "en.1.json",
        "data_dir": "data", "model_dir": "models",
        "expected_matches": dict.fromkeys(["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"], 380),
        "hashes": {
            "2020-21": "21ddf26b48469da530c51ccc4857bf1a534bda3aed08766b55185efb142e9a20",
            "2021-22": "fbdfd426fa18fa2f8630b77de87c082734da495ac4668d6d72f29f76b73b9564",
            "2022-23": "8d09f0f9846981626cdfec48903e1f21e7c79aabe6f92535c9e092e8e79b808b",
            "2023-24": "03e13eafbf78dfe00d7e89dd3bf6643986eb6e8fd86c7664aeb8c5bc0bed88d0",
            "2024-25": "c3d18f552d83382cd4b6b21127adbbfe38e7f8618ddc979fb5404f2df07d0a75",
        },
    },
    "la-liga": {
        "name": "La Liga", "source_file": "es.1.json",
        "data_dir": "data/la-liga", "model_dir": "models/la-liga",
        "expected_matches": {"2020-21": 380, "2021-22": 380, "2022-23": 380,
                             "2023-24": 380, "2024-25": 370},
        "hashes": {
            "2020-21": "817a41df564a1790147e97fc417922f6e9354b142b2baf6d376d809da2bd24b6",
            "2021-22": "7beb67dd49d7132bf9f7baea540342439b97ed4a7b21ffb90d3231a402c54d02",
            "2022-23": "0204c66c919c2cd5cc3d1ba26be4f68592e4e173843162a9e6755182ccf83778",
            "2023-24": "e4c1e1a958f224ba3c815c898982ab495b9577315cc58ee7a5e7b532960f738b",
            "2024-25": "da5bfa1b3634e1039d9e71aec50bdc847f8761189e3de235a4e730e0dc64ca38",
        },
    },
}


def get_league(league=DEFAULT_LEAGUE):
    if league not in LEAGUES:
        raise ValueError("Choose a supported league: " + ", ".join(LEAGUES))
    return LEAGUES[league]
