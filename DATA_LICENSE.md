# Data license and provenance

The historical football match data comes from [OpenFootball football.json](https://github.com/openfootball/football.json), maintained by OpenFootball contributors. It is dedicated to the public domain under **CC0 1.0 Universal**, independently of this application's MIT source-code license.

- Pinned source revision: `e6744429ee395bc86f247348c6184bb08d4eb361`.
- Premier League inputs: `2020-21/en.1.json`, `2021-22/en.1.json`, `2022-23/en.1.json`, `2023-24/en.1.json`, `2024-25/en.1.json`.
- Premier League coverage: 1,900 completed matches, 12 September 2020 through 25 May 2025.
- La Liga inputs: `2020-21/es.1.json`, `2021-22/es.1.json`, `2022-23/es.1.json`, `2023-24/es.1.json`, `2024-25/es.1.json`.
- La Liga coverage: 1,890 completed matches, 12 September 2020 through 18 May 2025. The 2024–25 raw source includes 380 fixtures but only 370 results.
- [Exact upstream license text at this revision](https://raw.githubusercontent.com/openfootball/football.json/e6744429ee395bc86f247348c6184bb08d4eb361/LICENSE.md).
- [CC0 1.0 legal code](https://creativecommons.org/publicdomain/zero/1.0/legalcode).

The project preserves source URLs and SHA-256 checksums in `data/manifest.json` for Premier League and `data/la-liga/manifest.json` for La Liga so the inputs can be identified and reproduced. Processed match tables are derived from these same CC0 records. Credit is retained for provenance even though CC0 does not impose an attribution requirement.

The exact Premier League source-byte SHA-256 hashes are:

| Season | SHA-256 |
|---|---|
| 2020–21 | `21ddf26b48469da530c51ccc4857bf1a534bda3aed08766b55185efb142e9a20` |
| 2021–22 | `fbdfd426fa18fa2f8630b77de87c082734da495ac4668d6d72f29f76b73b9564` |
| 2022–23 | `8d09f0f9846981626cdfec48903e1f21e7c79aabe6f92535c9e092e8e79b808b` |
| 2023–24 | `03e13eafbf78dfe00d7e89dd3bf6643986eb6e8fd86c7664aeb8c5bc0bed88d0` |
| 2024–25 | `c3d18f552d83382cd4b6b21127adbbfe38e7f8618ddc979fb5404f2df07d0a75` |

The exact La Liga source-byte SHA-256 hashes are:

| Season | SHA-256 |
|---|---|
| 2020–21 | `817a41df564a1790147e97fc417922f6e9354b142b2baf6d376d809da2bd24b6` |
| 2021–22 | `7beb67dd49d7132bf9f7baea540342439b97ed4a7b21ffb90d3231a402c54d02` |
| 2022–23 | `0204c66c919c2cd5cc3d1ba26be4f68592e4e173843162a9e6755182ccf83778` |
| 2023–24 | `e4c1e1a958f224ba3c815c898982ab495b9577315cc58ee7a5e7b532960f738b` |
| 2024–25 | `da5bfa1b3634e1039d9e71aec50bdc847f8761189e3de235a4e730e0dc64ca38` |

Download files without reformatting or changing their line endings: a hash identifies exact bytes, not just equivalent JSON values.

Data is provided without a guarantee of accuracy or completeness. One known source issue is that the Premier League 2019–20 file at the pinned revision includes July 2020 matches dated July 2019; that season is excluded from the default dataset.

The La Liga 2024–25 source has empty scores for all ten Matchday 38 fixtures dated 23–25 May 2025. Raw files preserve those records unchanged. Ingestion explicitly excludes them from the completed-match table and records ten missing results in the manifest. Its test set therefore contains 370 matches through 18 May, not a complete 380-match season. These are missing upstream scores, not an assertion that the games were unplayed. No replacement scores have been invented. Verify any expanded dataset before using it in date-based evaluation.

This CC0 license applies to the match data, not the separately licensed player photographs. Photo attribution and reuse terms are documented in [assets/PHOTO_CREDITS.md](assets/PHOTO_CREDITS.md). Club names identify teams in historical matches. OpenFootball, the Premier League, La Liga, players, and participating clubs do not endorse this application.
