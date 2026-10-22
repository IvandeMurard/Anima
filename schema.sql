-- Anima - PostgreSQL schema (Aiven for PostgreSQL). Synthetic data only.
-- Durable memory lives here; this-stay memory lives in Valkey with a TTL at check-out.

CREATE TABLE guests (
  guest_id      text PRIMARY KEY,
  name          text NOT NULL CHECK (name LIKE 'SYN-%'),   -- synthetic only
  stays_before  int  NOT NULL DEFAULT 0
);

CREATE TABLE consents (                                    -- one row per purpose (R1)
  guest_id  text REFERENCES guests ON DELETE CASCADE,
  purpose   text NOT NULL,                                 -- 'stay personalisation' | 'arrival coordination'
  given     date NOT NULL,
  via       text NOT NULL,
  PRIMARY KEY (guest_id, purpose)
);

CREATE TABLE claims (                                      -- durable memory: declared only (R2)
  claim_id        text PRIMARY KEY,
  guest_id        text REFERENCES guests ON DELETE CASCADE,
  key             text NOT NULL,
  value           jsonb NOT NULL,
  statement       text NOT NULL,
  origin          text NOT NULL CHECK (origin = 'declared'),
  source          text NOT NULL,
  purpose         text NOT NULL,
  layer           text NOT NULL CHECK (layer = 'semantic'), -- working claims go to Valkey
  first_seen      date NOT NULL,
  last_confirmed  date NOT NULL,
  confirmations   int  NOT NULL DEFAULT 1,
  expires_at      date GENERATED ALWAYS AS ((last_confirmed + interval '36 months')::date) STORED,
  needs_reconfirm boolean NOT NULL DEFAULT false,         -- R10
  FOREIGN KEY (guest_id, purpose) REFERENCES consents (guest_id, purpose) ON DELETE CASCADE
);

-- R9: daily expiry sweep (run at day start; log the count, not the content)
-- DELETE FROM claims WHERE expires_at <= CURRENT_DATE RETURNING claim_id;

-- R1: consent withdrawal deletes memory in one transaction
-- BEGIN; DELETE FROM consents WHERE guest_id = $1; DELETE FROM claims WHERE guest_id = $1; COMMIT;

CREATE TABLE refusals (                                    -- R2 log, deliberately NO guest_id
  day        date NOT NULL,
  attribute  text NOT NULL,
  origin     text NOT NULL,
  source     text NOT NULL,
  count      int  NOT NULL DEFAULT 1,
  PRIMARY KEY (day, attribute, origin, source)
);

CREATE TABLE events (                                      -- what happened, in order
  seq     int PRIMARY KEY,
  at      timestamptz NOT NULL,
  type    text NOT NULL,
  source  text NOT NULL,
  payload jsonb NOT NULL
);

CREATE TABLE decisions (                                   -- R4: every recommendation, and who validated it
  id            bigserial PRIMARY KEY,
  at            timestamptz NOT NULL,
  guest_id      text,
  room          text,
  ready_by      time,
  cites         text[] NOT NULL DEFAULT '{}',
  alternative   text,
  validated_by  text,
  validated_at  timestamptz
);

-- Valkey (this stay):
--   HSET stay:R-G001:claims C002 '{"key":"needs_desk","value":true,...}'
--   EXPIREAT stay:R-G001:claims <check-out unix ts>      -- forgets by itself (R9)
--   XADD events * seq 3 type guest_message ...           -- live event stream
--   ZADD hk:queue <priority> 206                          -- housekeeping queue, pinned rooms first
