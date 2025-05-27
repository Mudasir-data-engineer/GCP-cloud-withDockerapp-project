-- ========================================
-- Feature Engineering for smaxtec_features
-- ========================================

WITH base AS (
  SELECT 
    cow_id,
    TIMESTAMP_SECONDS(CAST(timestamp AS INT64)) AS event_ts,
    TIMESTAMP_TRUNC(hour_ts, HOUR) AS hour_ts,
    temperature,
    humidity,
    activity_level,
    heart_rate,
    rumination_minutes,
    milk_yield,
    is_ruminating,
    sensor_id_transformed
  FROM `kafka-airflow-data-project.smaxtec_dataset.smaxtec_data`
  WHERE cow_id IS NOT NULL
    AND temperature IS NOT NULL
    AND humidity IS NOT NULL
    AND timestamp IS NOT NULL
    AND hour_ts IS NOT NULL
    AND activity_level IS NOT NULL
    AND heart_rate IS NOT NULL
    AND rumination_minutes IS NOT NULL
    AND milk_yield IS NOT NULL
    AND is_ruminating IS NOT NULL
    AND sensor_id_transformed IS NOT NULL
),

hourly_agg AS (
  SELECT
    cow_id,
    hour_ts,
    AVG(temperature) AS avg_temperature,
    AVG(humidity) AS avg_humidity,
    AVG(activity_level) AS avg_activity_level,
    AVG(heart_rate) AS avg_heart_rate,
    AVG(rumination_minutes) AS avg_rumination_minutes,
    AVG(milk_yield) AS avg_milk_yield,
    SUM(CAST(is_ruminating AS INT64)) AS ruminating_count,
    COUNT(*) AS records_count
  FROM base
  GROUP BY cow_id, hour_ts
),

six_hour_agg AS (
  SELECT
    cow_id,
    TIMESTAMP_SECONDS(DIV(UNIX_SECONDS(hour_ts), 21600) * 21600) AS six_hour_window,
    AVG(avg_temperature) AS six_hour_avg_temp,
    AVG(avg_humidity) AS six_hour_avg_humidity,
    AVG(avg_activity_level) AS six_hour_avg_activity,
    AVG(avg_heart_rate) AS six_hour_avg_heart_rate,
    AVG(avg_rumination_minutes) AS six_hour_avg_rumination,
    AVG(avg_milk_yield) AS six_hour_avg_milk_yield,
    SUM(ruminating_count) AS six_hour_ruminating_count,
    SUM(records_count) AS six_hour_record_count
  FROM hourly_agg
  GROUP BY cow_id, six_hour_window
),

daily_agg AS (
  SELECT
    cow_id,
    DATE(hour_ts) AS day,
    AVG(avg_temperature) AS daily_avg_temp,
    AVG(avg_humidity) AS daily_avg_humidity,
    AVG(avg_activity_level) AS daily_avg_activity,
    AVG(avg_heart_rate) AS daily_avg_heart_rate,
    AVG(avg_rumination_minutes) AS daily_avg_rumination,
    AVG(avg_milk_yield) AS daily_avg_milk_yield,
    SUM(ruminating_count) AS daily_ruminating_count,
    SUM(records_count) AS daily_record_count
  FROM hourly_agg
  GROUP BY cow_id, day
),

herd_hourly_benchmarks AS (
  SELECT
    hour_ts,
    AVG(avg_temperature) AS herd_avg_temperature,
    AVG(avg_humidity) AS herd_avg_humidity,
    AVG(avg_activity_level) AS herd_avg_activity_level,
    AVG(avg_heart_rate) AS herd_avg_heart_rate,
    AVG(avg_rumination_minutes) AS herd_avg_rumination,
    AVG(avg_milk_yield) AS herd_avg_milk_yield
  FROM hourly_agg
  GROUP BY hour_ts
),

flags AS (
  SELECT
    h.cow_id,
    h.hour_ts,
    h.avg_temperature,
    h.avg_humidity,
    h.avg_activity_level,
    h.avg_heart_rate,
    h.avg_rumination_minutes,
    h.avg_milk_yield,
    hb.herd_avg_temperature,
    hb.herd_avg_humidity,
    hb.herd_avg_activity_level,
    hb.herd_avg_heart_rate,
    hb.herd_avg_rumination,
    hb.herd_avg_milk_yield,

    -- Existing Flags
    CASE WHEN h.avg_temperature > hb.herd_avg_temperature + 1 THEN TRUE ELSE FALSE END AS temp_flag,
    CASE WHEN h.avg_heart_rate < 55 OR h.avg_heart_rate > 90 THEN TRUE ELSE FALSE END AS heart_rate_flag,
    CASE WHEN h.avg_rumination_minutes < 0.8 * hb.herd_avg_rumination THEN TRUE ELSE FALSE END AS rumination_flag,

    -- New Flag: low_activity_flag
    CASE WHEN h.avg_activity_level < 0.7 * hb.herd_avg_activity_level THEN TRUE ELSE FALSE END AS low_activity_flag,

    -- New Flag: sudden_drop_flag
    CASE 
      WHEN h.avg_heart_rate - LAG(h.avg_heart_rate) OVER (PARTITION BY h.cow_id ORDER BY h.hour_ts) < -15
        OR h.avg_rumination_minutes - LAG(h.avg_rumination_minutes) OVER (PARTITION BY h.cow_id ORDER BY h.hour_ts) < -30
      THEN TRUE 
      ELSE FALSE 
    END AS sudden_drop_flag

  FROM hourly_agg h
  JOIN herd_hourly_benchmarks hb
    ON h.hour_ts = hb.hour_ts
),

labels AS (
  SELECT
    cow_id,
    hour_ts,
    temp_flag,
    heart_rate_flag,
    rumination_flag,
    CASE
      WHEN temp_flag = FALSE AND heart_rate_flag = FALSE AND rumination_flag = FALSE THEN 'healthy'
      WHEN temp_flag = TRUE OR heart_rate_flag = TRUE THEN 'at-risk'
      ELSE 'unwell'
    END AS health_status
  FROM flags
)

SELECT
  f.cow_id,
  f.hour_ts AS feature_hour,
  f.avg_temperature,
  f.avg_humidity,
  f.avg_activity_level,
  f.avg_heart_rate,
  f.avg_rumination_minutes,
  f.avg_milk_yield,

  f.temp_flag,
  f.heart_rate_flag,
  f.rumination_flag,
  f.low_activity_flag,
  f.sudden_drop_flag,

  l.health_status
FROM flags f
JOIN hourly_agg h 
  ON f.cow_id = h.cow_id AND f.hour_ts = h.hour_ts
JOIN labels l 
  ON f.cow_id = l.cow_id AND f.hour_ts = l.hour_ts;
