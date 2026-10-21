-- Analytical mart; independent from the API's minimal predictions audit table.
CREATE TABLE IF NOT EXISTS calendar (day TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS routing_events (
  prediction_id TEXT PRIMARY KEY,
  day TEXT NOT NULL,
  model_version TEXT NOT NULL,
  needs_review INTEGER NOT NULL CHECK(needs_review IN (0,1)),
  predicted_route TEXT NOT NULL,
  true_route TEXT,
  latency_ms NUMERIC NOT NULL CHECK(latency_ms >= 0)
);
CREATE INDEX IF NOT EXISTS routing_day_version ON routing_events(day,model_version);
DROP VIEW IF EXISTS routing_daily;
CREATE VIEW routing_daily AS
WITH daily AS (
  SELECT day, model_version, COUNT(*) AS volume,
         SUM(needs_review) AS reviewed,
         COUNT(true_route) FILTER (WHERE needs_review=0) AS accepted_labeled,
         COUNT(*) FILTER (WHERE needs_review=0 AND true_route=predicted_route) AS accepted_correct
  FROM routing_events GROUP BY day,model_version
), spine AS (
  SELECT c.day,v.model_version,COALESCE(d.volume,0) AS volume,
         COALESCE(d.reviewed,0) AS reviewed,
         COALESCE(d.accepted_labeled,0) AS accepted_labeled,
         COALESCE(d.accepted_correct,0) AS accepted_correct
  FROM calendar c CROSS JOIN (SELECT DISTINCT model_version FROM routing_events) v
  LEFT JOIN daily d ON c.day=d.day AND v.model_version=d.model_version
)
SELECT *,1.0*reviewed/NULLIF(volume,0) AS review_rate,
       1.0*accepted_correct/NULLIF(accepted_labeled,0) AS accepted_precision,
       AVG(volume) OVER (PARTITION BY model_version ORDER BY day
         ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS volume_7day_average,
       volume-LAG(volume,7) OVER (PARTITION BY model_version ORDER BY day) AS weekly_volume_change
FROM spine;
