CREATE TABLE principal_locks (
  owner_id VARCHAR(64) COLLATE utf8mb4_bin PRIMARY KEY
);
CREATE TABLE orders (
  order_id VARCHAR(64) COLLATE utf8mb4_bin PRIMARY KEY,
  root_order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
  owner_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
  snapshot_json JSON NULL,
  snapshot_hash CHAR(64) NULL,
  payable_cents BIGINT NOT NULL,
  refunded_cents BIGINT NOT NULL DEFAULT 0,
  split_done BOOLEAN NOT NULL DEFAULT FALSE,
  CONSTRAINT amounts_valid CHECK (payable_cents >= 0 AND refunded_cents >= 0 AND refunded_cents <= payable_cents),
  INDEX root_lookup(root_order_id)
);
CREATE TABLE order_units (
  root_order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
  unit_id VARCHAR(72) COLLATE utf8mb4_bin NOT NULL,
  payable_cents BIGINT NOT NULL,
  refunded BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY(root_order_id, unit_id),
  FOREIGN KEY(root_order_id) REFERENCES orders(order_id),
  CHECK(payable_cents >= 0)
);
CREATE TABLE order_memberships (
  order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
  unit_id VARCHAR(72) COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY(order_id, unit_id),
  FOREIGN KEY(order_id) REFERENCES orders(order_id)
);
CREATE TABLE coupon_uses (
  coupon_id VARCHAR(64) COLLATE utf8mb4_bin PRIMARY KEY,
  order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
  FOREIGN KEY(order_id) REFERENCES orders(order_id)
);
CREATE TABLE idempotency_records (
  owner_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
  operation_id VARCHAR(150) COLLATE utf8mb4_bin NOT NULL,
  request_key VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
  fingerprint CHAR(64) NOT NULL,
  response_json JSON NOT NULL,
  PRIMARY KEY(owner_id, operation_id, request_key)
);
CREATE TABLE refund_requests (
  refund_id VARCHAR(64) COLLATE utf8mb4_bin PRIMARY KEY,
  order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
  root_order_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
  amount_cents BIGINT NOT NULL,
  unit_ids JSON NOT NULL,
  snapshot_hash CHAR(64) NOT NULL,
  FOREIGN KEY(order_id) REFERENCES orders(order_id),
  CHECK(amount_cents >= 0)
);
