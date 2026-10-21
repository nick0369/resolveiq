# ResolveIQ

Classify financial complaint narratives into six product routes and send uncertain cases for human review.

**Status:** trained and evaluated independent portfolio implementation. The public browser demo scores with the checked-in trained model. FastAPI runs locally or in the provided container configuration. This is not a regulated production deployment.

[Live dashboard](https://nikhil-chandekar-data-portfolio.goofyvole8.chatgpt.site/projects/resolveiq.html) · [Model card](MODEL_CARD.md) · [Metrics](metrics.json)

## Project summary

Unstructured complaints require product-team routing. The model suggests a route from narrative text, while a validation-selected threshold sends uncertain cases to humans. Routes proxy CFPB product categories, not independent operational adjudications.

14,930 training narratives (2015–2016); 3,013 for regularization selection (Q1 2017); 3,233 for review policy (Q2 2017); 11,846 test narratives (July 2017–April 2018). Exact normalized duplicates are removed before splitting. Only text is used as input.

## Measured results

| Metric | Held-out result |
|---|---|
| Macro-F1 | 0.813 |
| Accepted precision | 91.1% |
| Automation coverage | 67.7% |

Test size: **11,846**. See metrics.json for baselines, partition sizes and policy thresholds. Results were computed locally on Python 3.14.7. Source: [official download](https://files.consumerfinance.gov/f/documents/CCDB_Export_1_December_2011_through_April_2018.zip); checksum in manifest.json. No realized financial ROI is claimed.

## Run the trained project

Python 3.14 is the tested version. From a fresh clone:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/ for the interactive dashboard and http://127.0.0.1:8000/docs for validated API requests. Use the example inputs in examples.json. No API key is needed.

```bash
python train.py
python monitor.py
# Optional, requires Docker installed:
docker compose up --build
```

Training downloads the official dataset into ignored .data/. It can take time and requires an internet connection. `python train.py --source /path/to/source.zip` reuses an existing official archive. Reproduction records the new checksum in manifest.json; compare it to the committed checksum before comparing results. Raw data and private text are not checked in. Use the committed artifact to run predictions immediately without downloading training data.

## Code map

```text
data.py             Download, schema checks and provenance
features.py         Documented feature/text transformations
train.py            Deterministic split, baselines, fitting and export
evaluate.py         Statistical and business-policy metrics
policy.py           Review threshold and uncertainty helpers
inference.py        Safe JSON model loading / portable prediction
api.py              Pydantic validation, endpoints and SQLite audit
monitor.py          Request counts, review rate and latency summary
test_project.py     Edge cases, API contracts and model-export parity
schema.sql          Advanced SQL reference and data mart
model.json          Trained portable model, not a placeholder
metrics.json        Actual frozen-test results
examples.json       Scoring/parity examples
split_manifest.csv  Stable source IDs / partitions (no narrative text)
manifest.json       Exact source URL, checksum and scope
dashboard.html/js   Public interactive scoring and metrics
MODEL_CARD.md       Intended use, limitations and release/runbook
requirements.txt    Exact tested dependency versions
Dockerfile          Non-root API container configuration
compose.yaml        API health check and persistent audit volume
```

The flat module layout is deliberate: this is a small, readable application. Each file has a clear responsibility without framework boilerplate. SQLite stores operational audit data locally. The SQL analytical mart is separate from inference; see SQL_NOTES.md for database setup and validation scope.

## Key insights and conclusion

The classifier achieved 0.813 macro-F1 versus 0.060 for a majority-route baseline. The frozen routing policy accepted 67.7% of test cases at 91.1% precision (Wilson lower endpoint: 90.4%). Full-coverage performance and selective precision answer different questions. Credit reporting and debt collection confusion remains a review priority.

## Engineering and operations

- The trained artifact is JSON, avoiding unsafe pickle deserialization. Python and JavaScript predictions are parity checked.
- Pydantic checks the request contract; invalid inputs return 422. Missing/corrupt model artifacts prevent startup.
- Requests are audited with random ID, version, score, review flag and timing. Raw narratives and account histories are not logged.
- Run `python monitor.py` to summarize audit counts, review share and inference p95; this is not a full observability platform.
- Version model, policy, schema and service together. To roll back, restore the previous reviewed Git commit/artifact, restart, and run tests plus a synthetic request.
- In a real deployment, add TLS, authentication where required, request limits, alerting and delayed-label performance checks. Do not expose sensitive user data through the public demonstration.

## Limitations

Selected historical public narratives and six mapped routes; near-duplicate templates may remain. Taxonomy shifts and new languages are unsupported. Raw top-route scores are not calibrated certainty. Handling-time savings require a pilot.

Docker configuration is provided; a container build is not claimed tested unless Docker verification is recorded. The measured FastAPI benchmark uses a local test client and is not a cloud throughput/SLA claim. See VALIDATION.md for exact checks and environment.

## Interview talking points

1. Why this business problem needs a review policy as well as a classifier.
2. How the split prevents target or future-data leakage.
3. Why the baseline matters and where the selected model still fails.
4. How offline predictions match deployed inference.
5. What must be measured before claiming business ROI.

## License and attribution

MIT applies to original code. Dataset rights remain with the original publisher. See the official source and manifest for provenance. This is an independent educational portfolio project, not employment or client work.
