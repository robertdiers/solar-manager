# solar-manager

combine Kostal, iDM, Soyosource and charger management


docker run -d --device=/dev/ttyUSB0:/dev/ttyUSB0 robertdiers/solarmanager:arm


## TimescaleDB

CREATE TABLE solar_kostal_battery ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_battery', 'time');

ALTER TABLE solar_kostal_battery SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_battery', INTERVAL '1 days');

CREATE TABLE solar_kostal_batterypercent ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_batterypercent', 'time');

ALTER TABLE solar_kostal_batterypercent SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_batterypercent', INTERVAL '1 days');

CREATE TABLE solar_kostal_batteryflag ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_batteryflag', 'time');

ALTER TABLE solar_kostal_batteryflag SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_batteryflag', INTERVAL '1 days');

CREATE TABLE solar_kostal_inverter ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_inverter', 'time');

ALTER TABLE solar_kostal_inverter SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_inverter', INTERVAL '1 days');

CREATE TABLE solar_kostal_powertogrid ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_powertogrid', 'time');

ALTER TABLE solar_kostal_powertogrid SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_powertogrid', INTERVAL '1 days');

CREATE TABLE solar_idm_feedin ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_idm_feedin', 'time');

ALTER TABLE solar_idm_feedin SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_idm_feedin', INTERVAL '1 days');

CREATE TABLE solar_kostal_consumption_battery ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_consumption_battery', 'time');

ALTER TABLE solar_kostal_consumption_battery SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_consumption_battery', INTERVAL '1 days');

CREATE TABLE solar_kostal_consumption_grid ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_consumption_grid', 'time');

ALTER TABLE solar_kostal_consumption_grid SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_consumption_grid', INTERVAL '1 days');

CREATE TABLE solar_kostal_consumption_pv ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_consumption_pv', 'time');

ALTER TABLE solar_kostal_consumption_pv SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_consumption_pv', INTERVAL '1 days');

CREATE TABLE solar_kostal_consumption_total ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_consumption_total', 'time');

ALTER TABLE solar_kostal_consumption_total SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_consumption_total', INTERVAL '1 days');

CREATE TABLE solar_kostal_generation_total ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_generation_total', 'time');

ALTER TABLE solar_kostal_generation_total SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_generation_total', INTERVAL '1 days');

CREATE TABLE solar_kostal_generation_dc1 ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_generation_dc1', 'time');

ALTER TABLE solar_kostal_generation_dc1 SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_generation_dc1', INTERVAL '1 days');

CREATE TABLE solar_kostal_generation_dc2 ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_generation_dc2', 'time');

ALTER TABLE solar_kostal_generation_dc2 SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_generation_dc2', INTERVAL '1 days');

CREATE TABLE solar_kostal_generation_dc3 ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_generation_dc3', 'time');

ALTER TABLE solar_kostal_generation_dc3 SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_generation_dc3', INTERVAL '1 days');

CREATE TABLE solar_kostal_surplus ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_kostal_surplus', 'time');

ALTER TABLE solar_kostal_surplus SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_kostal_surplus', INTERVAL '1 days');

CREATE TABLE solar_battery_chargestatus ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_battery_chargestatus', 'time');

ALTER TABLE solar_battery_chargestatus SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_battery_chargestatus', INTERVAL '1 days');

CREATE TABLE solar_soyosource ( "time" timestamptz NOT NULL , "value" double precision
);

SELECT create_hypertable('solar_soyosource', 'time');

ALTER TABLE solar_soyosource SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );

SELECT add_compression_policy('solar_soyosource', INTERVAL '1 days');