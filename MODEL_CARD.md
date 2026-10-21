# ResolveIQ model card

## Intended use
Classify financial complaint narratives into six product routes and send uncertain cases for human review. Decision support and educational benchmarking with historical public data.

## Data and training
14,930 training narratives (2015–2016); 3,013 for regularization selection (Q1 2017); 3,233 for review policy (Q2 2017); 11,846 test narratives (July 2017–April 2018). Exact normalized duplicates are removed before splitting. Only text is used as input.

Artifact: model.json. Scope and source SHA-256: manifest.json. Reproducible partitions: split_manifest.csv. Weights were fitted; no results are simulated. Dataset itself is not redistributed.

## Evaluation
| Macro-F1 | 0.813 |
| Accepted precision | 91.1% |
| Automation coverage | 67.7% |

See metrics.json for full details. Credit intervals use account-level bootstrap; text accepted-precision uncertainty uses Wilson bounds, which do not fully model correlated templates. No fairness certification or operational approval is claimed.

## Conclusion
The classifier achieved 0.813 macro-F1 versus 0.060 for a majority-route baseline. The frozen routing policy accepted 67.7% of test cases at 91.1% precision (Wilson lower endpoint: 90.4%). Full-coverage performance and selective precision answer different questions. Credit reporting and debt collection confusion remains a review priority.

## Risks and limitations
Selected historical public narratives and six mapped routes; near-duplicate templates may remain. Taxonomy shifts and new languages are unsupported. Raw top-route scores are not calibrated certainty. Handling-time savings require a pilot.

## Monitoring and rollback
Immediate: input validation, inference failures, audit-store failures. Monitor latency and review rate with monitor.py. Future delayed labels are required to measure real model drift. Restore a reviewed previous artifact and restart the API to roll back; never silently retrain or change review thresholds in production.

## Release checklist
Run pytest, model-export parity, JavaScript parity, one synthetic API request, /ready and dashboard smoke checks. Maintain the data checksum, dependency pins, threshold and metrics with the model release. The public demo executes inference in the visitor browser and does not retain submitted text.
