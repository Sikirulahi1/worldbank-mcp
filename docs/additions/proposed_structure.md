worldbank-mcp/
├── src/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py                          # env vars, base URLs, timeouts, retry limits
│   │   ├── constants.py                        # database ID priority list, default page size, supported formats
│   │   ├── exceptions.py                       # base exception hierarchy (see note below)
│   │   ├── logging.py
│   │   └── result.py                           # a generic Result/Outcome type (success | needs_clarification | not_found | error) — see note below
│   │
│   ├── domain/
│   │   ├── indicator/
│   │   │   ├── entities.py                     # Indicator, IndicatorCandidate, IndicatorSeries, Observation
│   │   │   ├── ranking.py                      # pure: scores/sorts raw candidates by relevance
│   │   │   ├── deduplication.py                # pure: collapses same-concept duplicates across databases (the WB_ESG/WB_GS/WB_CLEAR case) — SEPARATE from ranking, different job
│   │   │   ├── disambiguation.py                # pure: given ranked+deduped candidates, decide auto_resolve | ask_user | not_found
│   │   │   └── validation.py                    # pure: is this indicator code well-formed, is this year range plausible
│   │   │
│   │   ├── country/
│   │   │   ├── entities.py                     # Country dataclass (iso2, iso3, name, aliases)
│   │   │   ├── reference_data.py                # the static country list itself, as data, not logic
│   │   │   └── resolution.py                    # pure: name/alias → Country, handles ambiguous/no-match cases
│   │   │
│   │   ├── shaping/
│   │   │   ├── field_analysis.py                # pure: given rows, classify fields into constant vs varying
│   │   │   ├── series_builder.py                # pure: turns varying fields into the {year: value} structure
│   │   │   └── coverage.py                      # pure: compares requested year range vs indicator's actual available range, flags gaps/out-of-range
│   │   │
│   │   └── report/
│   │       └── table_merge.py                   # pure: merges multiple indicator series into one year-keyed table for export
│   │
│   ├── application/
│   │   ├── ports/                                # interfaces the application layer depends on — NOT implementations
│   │   │   ├── search_port.py                    # abstract: search(topic) -> raw candidates
│   │   │   ├── data_port.py                      # abstract: fetch(indicator, country, range) -> raw observations
│   │   │   └── file_writer_port.py                # abstract: write(table, format) -> file path
│   │   │
│   │   ├── search_indicator/
│   │   │   ├── pipeline.py                       # orchestrates: call search_port → rank → dedupe → return
│   │   │   └── dto.py                             # request/response shape for this specific use case
│   │   │
│   │   ├── get_indicator_data/
│   │   │   ├── pipeline.py                       # orchestrates: call data_port → shape → check coverage → return
│   │   │   └── dto.py
│   │   │
│   │   ├── get_country_indicator/
│   │   │   ├── pipeline.py                       # composes search_indicator + disambiguation decision + get_indicator_data
│   │   │   └── dto.py
│   │   │
│   │   └── export_report/
│   │       ├── pipeline.py                       # loops get_country_indicator per topic → table_merge → file_writer_port
│   │       └── dto.py
│   │
│   ├── infrastructure/
│   │   ├── worldbank_client/
│   │   │   ├── search_client.py                  # implements application/ports/search_port — real HTTP call to searchv2
│   │   │   ├── data_client.py                     # implements data_port — real HTTP call to /data360/data, handles skip/pagination loop
│   │   │   ├── metadata_client.py                 # for /metadata, /disaggregation — used to answer coverage.py's "what's the real range" question
│   │   │   ├── response_parser.py                 # raw JSON → domain entities (Observation, IndicatorCandidate) — isolates "their JSON shape" from the rest of the app
│   │   │   └── http.py                            # low-level shared HTTP client setup (headers, base client instance)
│   │   │
│   │   ├── file_export/
│   │   │   ├── csv_writer.py                      # implements file_writer_port for csv
│   │   │   ├── excel_writer.py                    # implements file_writer_port for xlsx
│   │   │   └── json_writer.py                     # implements file_writer_port for json
│   │   │
│   │   └── resilience/
│   │       ├── retry_policy.py                    # backoff rules, what counts as retryable vs permanent
│   │       └── rate_limit_handler.py               # specifically handles 429s if distinct handling is needed
│   │
│   └── presentation/
│       └── mcp/
│           ├── schemas/
│           │   ├── search_indicator_schema.py     # JSON schema for this one tool's params — separate file per tool
│           │   ├── get_indicator_data_schema.py
│           │   ├── get_country_indicator_schema.py
│           │   └── export_report_schema.py
│           ├── tool_handlers.py                    # thin glue: MCP tool call → dto → application pipeline → MCP result
│           └── server.py                            # registers everything, starts transport
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   │   ├── indicator/
│   │   │   │   ├── test_ranking.py
│   │   │   │   ├── test_deduplication.py
│   │   │   │   ├── test_disambiguation.py
│   │   │   │   └── test_validation.py
│   │   │   ├── country/
│   │   │   │   └── test_resolution.py
│   │   │   ├── shaping/
│   │   │   │   ├── test_field_analysis.py
│   │   │   │   ├── test_series_builder.py
│   │   │   │   └── test_coverage.py
│   │   │   └── report/
│   │   │       └── test_table_merge.py
│   │   │
│   │   └── application/
│   │       ├── test_search_indicator_pipeline.py    # uses a FAKE search_port, not the real HTTP client
│   │       ├── test_get_indicator_data_pipeline.py   # uses a FAKE data_port
│   │       ├── test_get_country_indicator_pipeline.py
│   │       └── test_export_report_pipeline.py         # uses a FAKE file_writer_port too
│   │
│   ├── integration/
│   │   ├── test_search_client_live.py                # real call to World Bank, marked slow/optional
│   │   ├── test_data_client_live.py
│   │   └── test_file_writers.py                       # actually open the produced csv/xlsx and check contents
│   │
│   ├── e2e/
│   │   └── test_tool_calls_via_mcp.py                 # spins up the actual MCP server, calls tools through the protocol itself
│   │
│   ├── fixtures/
│   │   └── sample_responses/
│   │       ├── search_gdp_clean.json
│   │       ├── search_gdp_duplicates.json
│   │       ├── search_poverty_ambiguous.json
│   │       ├── search_nonsense_empty.json
│   │       ├── data_nigeria_gdp_1990_2012.json
│   │       ├── data_zero_records.json
│   │       └── data_error_response.json
│   │
│   └── conftest.py
│
├── docs/
│   └── architecture/
│       ├── adr-001-no-local-cache.md
│       ├── adr-002-database-priority-tiebreak.md
│       └── adr-003-disambiguation-thresholds.md
│
├── .env.example
├── requirements.txt
└── run.py