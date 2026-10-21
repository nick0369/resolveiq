# ResolveIQ — project summary

Unstructured complaints require product-team routing. The model suggests a route from narrative text, while a validation-selected threshold sends uncertain cases to humans. Routes proxy CFPB product categories, not independent operational adjudications.

14,930 training narratives (2015â€“2016); 3,013 for regularization selection (Q1 2017); 3,233 for review policy (Q2 2017); 11,846 test narratives (July 2017â€“April 2018). Exact normalized duplicates are removed before splitting. Only text is used as input.

## Measured results

| Metric | Held-out result |
|---|---|
| Macro-F1 | 0.813 |
| Accepted precision | 91.1% |
| Automation coverage | 67.7% |

Test size: **11,846**. See metrics.json for baselines, partition sizes and policy thresholds. Results were computed locally on Python 3.14.7. Source: [official download](https://files.consumerfinance.gov/f/documents/CCDB_Export_1_December_2011_through_April_2018.zip); checksum in manifest.json. No realized financial ROI is claimed.


## Deliverables

Commented Python, trained JSON model, measured holdout evaluation, interactive browser demo, tested FastAPI service, SQL, unit/integration checks, data provenance, Docker configuration, monitoring summary and honest operational limitations.
