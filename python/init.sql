CREATE TABLE soyosource ( "value" double precision);
Insert into soyosource (value) values (0);
CREATE TABLE metrics ( "time" timestamptz NOT NULL, "key" varchar NOT NULL, "value" double precision );
SELECT create_hypertable('metrics', 'time');
ALTER TABLE metrics SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );
SELECT add_compression_policy('metrics', INTERVAL '1 days');
SELECT add_retention_policy('metrics', INTERVAL '7 days');
CREATE TABLE voltages ( "time" timestamptz NOT NULL, "key" varchar NOT NULL, "value" double precision );
SELECT create_hypertable('voltages', 'time');
ALTER TABLE voltages SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );
SELECT add_retention_policy('voltages', INTERVAL '1 days');