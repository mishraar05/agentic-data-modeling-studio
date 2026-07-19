-- Proof-slice SOURCE fixture (TEST DATA, not product code).
-- A deliberately legacy-style Guidewire-like P&C Personal Auto source: cryptic
-- names, real PK/FK constraints, privacy-bearing columns, and one opaque column
-- (col_9) with no discernible meaning. Replace this fixture by pointing
-- config/proof_slice.yaml at the real Unity Catalog source.

CREATE SCHEMA IF NOT EXISTS gw_pc_bronze;

CREATE TABLE gw_pc_bronze.pc_driver (
    drv_id      VARCHAR      NOT NULL,
    fname       VARCHAR,                 -- privacy: given name
    lname       VARCHAR,                 -- privacy: family name
    birth_dt    DATE,                    -- privacy: date of birth
    lic_no      VARCHAR,
    gndr_cd     VARCHAR,
    PRIMARY KEY (drv_id)
);

CREATE TABLE gw_pc_bronze.pc_policy (
    pol_id        VARCHAR      NOT NULL,
    ph_drv_id     VARCHAR,               -- policyholder -> driver
    eff_dt        DATE,
    exp_dt        DATE,
    wrtn_prem_amt DECIMAL(12,2),
    pol_stat_cd   VARCHAR,
    col_9         VARCHAR,               -- opaque: no discernible meaning
    PRIMARY KEY (pol_id),
    FOREIGN KEY (ph_drv_id) REFERENCES gw_pc_bronze.pc_driver (drv_id)
);

CREATE TABLE gw_pc_bronze.pc_claim (
    clm_id       VARCHAR      NOT NULL,
    pol_id       VARCHAR,
    loss_dt      DATE,
    incurred_amt DECIMAL(12,2),
    rsrv_amt     DECIMAL(12,2),
    clmnt_ssn    VARCHAR,                -- privacy: claimant SSN
    PRIMARY KEY (clm_id),
    FOREIGN KEY (pol_id) REFERENCES gw_pc_bronze.pc_policy (pol_id)
);

-- a few rows so the catalog is real and populated (enables profiling later)
INSERT INTO gw_pc_bronze.pc_driver VALUES
    ('D1','Ada','Lovelace',DATE '1985-12-10','CA-100','F'),
    ('D2','Alan','Turing',DATE '1979-06-23','CA-200','M');
INSERT INTO gw_pc_bronze.pc_policy VALUES
    ('P1','D1',DATE '2025-01-01',DATE '2026-01-01',1240.50,'ACTIVE','xyz'),
    ('P2','D2',DATE '2025-03-15',DATE '2026-03-15',980.00,'ACTIVE',NULL);
INSERT INTO gw_pc_bronze.pc_claim VALUES
    ('C1','P1',DATE '2025-07-04',5200.00,3000.00,'123-45-6789'),
    ('C2','P1',DATE '2025-09-01',800.00,800.00,'123-45-6789');
