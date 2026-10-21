# SQL implementation and validation

schema.sql defines the analytical schema, constraints, and a window-function view. It is separate from the API audit schema, which is created automatically by api.py.

The local implementation uses SQLite, available without extra installation. It demonstrates SQL CTEs, window functions, conditional aggregates, null-safe division, explicit grain, indexes, and constraints. PostgreSQL is a suitable enterprise migration, not a dependency falsely claimed to have run here.

The unit test builds the routing mart from labeled fixtures and checks a zero-volume calendar day. Populate calendar with a contiguous day sequence and routing_events with predictions plus labels available at the reporting cutoff. A real future deployment must record adjudication availability before computing delayed quality; this fixture mart does not claim a deployed adjudication system.

Seven-row rolling averages equal seven days only with the contiguous calendar spine. Aggregate precision using accepted_correct / accepted_labeled counts rather than averaging daily percentages.
