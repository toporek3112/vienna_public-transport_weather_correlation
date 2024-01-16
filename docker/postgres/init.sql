-- init.sql

CREATE DATABASE grafana;
CREATE DATABASE dsi_project;
ALTER DATABASE dsi_project OWNER TO postgres;

\c dsi_project;

-- CREATE TABLE stops (
--     stop_id INT,
--     diva INT,
--     stop_text VARCHAR(255),
--     municipality VARCHAR(255),
--     municipality_id INT,
--     longitude DOUBLE PRECISION,
--     latitude DOUBLE PRECISION
-- );

-- CREATE TABLE public.delays (
--     id SERIAL PRIMARY KEY,
--     id_delays VARCHAR(255),
--     title TEXT,
--     behoben BOOLEAN,
--     lines JSONB,
--     stations JSONB,
--     time_start_original TIMESTAMP,
--     time_start TIMESTAMP,
--     time_end TIMESTAMP
-- );

-- CREATE TABLE public.weather_data (
--     id SERIAL PRIMARY KEY,
--     time TIMESTAMP,
--     temperature_2m NUMERIC,
--     relative_humidity_2m NUMERIC,
--     wind_speed_10m NUMERIC
-- );

-- CREATE TABLE public.producer_deplays_checkpoint (
--     id SERIAL PRIMARY KEY,
--     page NUMERIC,
--     behoben BOOLEAN,
--     delay_id NUMERIC
--     last_scrape_time TIMESTAMP,
-- );

-- CREATE TABLE public.producer_weather_checkpoint (
--     id SERIAL PRIMARY KEY,
--     date Date,
--     behoben BOOLEAN,
--     delay_id NUMERIC
--     last_scrape_time TIMESTAMP,
-- );