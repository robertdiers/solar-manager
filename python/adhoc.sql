CREATE TABLE technical_room_temperature ( "time" timestamptz NOT NULL , "value" double precision );
SELECT create_hypertable('technical_room_temperature', 'time');
ALTER TABLE technical_room_temperature SET ( timescaledb.compress, timescaledb.compress_segmentby = 'time' );
SELECT add_compression_policy('technical_room_temperature', INTERVAL '1 days');
SELECT add_retention_policy('technical_room_temperature', INTERVAL '7 days');