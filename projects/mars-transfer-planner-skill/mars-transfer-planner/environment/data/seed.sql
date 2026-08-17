-- Mars Transfer Mission Planner Database
-- All values use SI units unless noted. Orbital radii in AU, mu in km³/s².

-- ══════════════ PLANETS ══════════════
CREATE TABLE planets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    orbital_radius_au DOUBLE PRECISION NOT NULL,
    orbital_radius_km DOUBLE PRECISION NOT NULL,
    mu_km3_s2 DOUBLE PRECISION NOT NULL,
    radius_km DOUBLE PRECISION NOT NULL,
    escape_velocity_km_s DOUBLE PRECISION NOT NULL,
    has_atmosphere BOOLEAN NOT NULL,
    surface_gravity_m_s2 DOUBLE PRECISION NOT NULL
);

INSERT INTO planets (name, orbital_radius_au, orbital_radius_km, mu_km3_s2, radius_km, escape_velocity_km_s, has_atmosphere, surface_gravity_m_s2) VALUES
('Sun',     0.0,       0.0,            132712440018.0, 695700.0,  617.7,  FALSE, 274.0),
('Mercury', 0.387,     57909227.0,     22031.868,      2439.7,    4.25,   FALSE, 3.7),
('Venus',   0.723,     108208475.0,    324858.592,     6051.8,    10.36,  TRUE,  8.87),
('Earth',   1.000,     149598023.0,    398600.4418,    6371.0,    11.186, TRUE,  9.807),
('Mars',    1.524,     227939366.0,    42828.375,      3389.5,    5.03,   TRUE,  3.721),
('Jupiter', 5.203,     778547200.0,    126686534.0,    69911.0,   59.5,   TRUE,  24.79),
('Saturn',  9.537,     1426666400.0,   37931187.0,     58232.0,   35.5,   TRUE,  10.44),
('Uranus',  19.19,     2870658186.0,   5793939.0,      25362.0,   21.3,   TRUE,  8.87),
('Neptune', 30.07,     4498396441.0,   6836529.0,      24622.0,   23.5,   TRUE,  11.15);

-- ══════════════ SPACECRAFT ══════════════
CREATE TABLE spacecraft (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    manufacturer VARCHAR(100) NOT NULL,
    dry_mass_kg DOUBLE PRECISION NOT NULL,
    max_fuel_capacity_kg DOUBLE PRECISION NOT NULL,
    engine_isp_s DOUBLE PRECISION NOT NULL,
    thrust_kn DOUBLE PRECISION NOT NULL,
    max_payload_kg DOUBLE PRECISION NOT NULL,
    reliability_rating DOUBLE PRECISION NOT NULL,
    available BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO spacecraft (name, manufacturer, dry_mass_kg, max_fuel_capacity_kg, engine_isp_s, thrust_kn, max_payload_kg, reliability_rating, available) VALUES
('Ares Clipper',       'SpaceCore',     12000, 85000,  450, 2200, 5000,  0.97, TRUE),
('Red Horizon',        'AstralDyn',     18000, 120000, 380, 3100, 8000,  0.94, TRUE),
('Valkyrie Express',   'NovaPulse',      9500, 65000,  470, 1800, 3500,  0.98, TRUE),
('Titan Hauler',       'HeavyLift Co',  32000, 200000, 340, 5500, 15000, 0.91, TRUE),
('Pioneer Scout',      'SpaceCore',      6000, 40000,  310, 900,  2000,  0.95, TRUE),
('Mars Dart',          'RocketLab+',     7500, 55000,  420, 1500, 2800,  0.96, FALSE),
('Olympus Carrier',    'AstralDyn',     25000, 160000, 360, 4200, 12000, 0.93, TRUE),
('Zephyr Light',       'NovaPulse',      4500, 28000,  490, 700,  1500,  0.99, TRUE),
('Helios Mk2',        'SolarTech',      14000, 95000,  430, 2400, 4500,  0.95, TRUE),
('Nebula Hauler',     'HeavyLift Co',   28000, 180000, 350, 4800, 10000, 0.92, TRUE),
('StormRider',        'RocketLab+',     11000, 78000,  440, 2000, 4200,  0.94, TRUE),
('Aether Prime',      'NovaPulse',       8000, 52000,  460, 1600, 3200,  0.97, FALSE),
('Cargo King',        'AstralDyn',      20000, 140000, 370, 3600, 7000,  0.93, TRUE),
('Mercury Express',   'SpaceCore',       5500, 35000,  500, 800,  2500,  0.99, TRUE),
('DeepStar III',      'SolarTech',      15000, 88000,  415, 2100, 5500,  0.96, TRUE);

-- ══════════════ SPACECRAFT FUEL COMPATIBILITY ══════════════
-- Each spacecraft engine is certified for specific propellant combinations.
-- Some certifications have expiry dates; expired certs are no longer valid for mission planning.
CREATE TABLE spacecraft_fuel_compatibility (
    id SERIAL PRIMARY KEY,
    spacecraft_name VARCHAR(100) NOT NULL REFERENCES spacecraft(name),
    fuel_type VARCHAR(50) NOT NULL,
    certified BOOLEAN NOT NULL DEFAULT TRUE,
    certification_expiry DATE,
    notes TEXT
);

INSERT INTO spacecraft_fuel_compatibility (spacecraft_name, fuel_type, certified, certification_expiry, notes) VALUES
('Ares Clipper',     'LOX/LH2',  TRUE, '2029-06-30',  'Primary propellant, RL-10C2 engine'),
('Red Horizon',      'LOX/RP-1', TRUE, '2029-03-15',  'Primary propellant, Merlin-D engine'),
('Red Horizon',      'LOX/LCH4', TRUE, '2028-09-01',  'Alternate certification, methane adaptation'),
('Valkyrie Express', 'LOX/LH2',  TRUE, '2030-01-01',  'Vinci-derived upper stage engine'),
('Titan Hauler',     'LOX/LH2',  TRUE, '2028-06-30',  'Upper stage hydrogen engine'),
('Titan Hauler',     'LOX/RP-1', TRUE, '2029-12-31',  'Booster stage kerosene engine'),
('Titan Hauler',     'LOX/LCH4', TRUE, '2028-03-15',  'Cross-certified methane adaptation'),
('Pioneer Scout',    'LOX/RP-1', TRUE, '2029-09-01',  'Small kerosene engine'),
('Mars Dart',        'LOX/LCH4', TRUE, '2028-12-31',  'Raptor-class methane engine'),
('Olympus Carrier',  'LOX/RP-1', TRUE, '2029-03-15',  'Primary propellant'),
('Olympus Carrier',  'LOX/LH2',  TRUE, '2024-12-31',  'Upper stage cert — recertification pending'),
('Zephyr Light',     'LOX/LH2',  TRUE, '2029-06-30',  'Micro hydrogen engine'),
('Helios Mk2',      'LOX/LH2',  TRUE, '2025-03-01',  'Primary propellant — recertification pending'),
('Helios Mk2',      'LOX/LCH4', TRUE, '2028-12-31',  'Dual-certified methane'),
('Nebula Hauler',   'LOX/RP-1', TRUE, '2029-06-30',  'Heavy kerosene main engine'),
('StormRider',      'LOX/LCH4', TRUE, '2028-09-30',  'Raptor-derived methane engine'),
('Aether Prime',    'LOX/LH2',  TRUE, '2030-03-01',  'High-efficiency hydrogen engine'),
('Cargo King',      'LOX/RP-1', TRUE, '2029-12-31',  'Heavy kerosene propulsion'),
('Mercury Express', 'LOX/LH2',  TRUE, '2029-09-30',  'Micro hydrogen thruster'),
('DeepStar III',    'LOX/LH2',  TRUE, '2029-03-15',  'Primary hydrogen propulsion'),
('DeepStar III',    'LOX/LCH4', TRUE, '2028-06-30',  'Alternate methane cert');

-- ══════════════ LAUNCH WINDOWS ══════════════
CREATE TABLE launch_windows (
    id SERIAL PRIMARY KEY,
    window_name VARCHAR(100) NOT NULL,
    open_date DATE NOT NULL,
    close_date DATE NOT NULL,
    phase_angle_deg DOUBLE PRECISION NOT NULL,
    alignment_quality DOUBLE PRECISION NOT NULL,
    delta_v_penalty_pct DOUBLE PRECISION NOT NULL,
    deprecated BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT
);

INSERT INTO launch_windows (window_name, open_date, close_date, phase_angle_deg, alignment_quality, delta_v_penalty_pct, deprecated, notes) VALUES
('2026-Alpha',  '2026-09-15', '2026-11-10', 44.2,  0.88, 3.5,  FALSE, 'Good window, moderate alignment'),
('2026-Beta',   '2026-10-20', '2026-12-05', 41.8,  0.92, 1.8,  FALSE, 'Excellent alignment, narrow window'),
('2026-Gamma',  '2026-08-01', '2026-09-20', 47.5,  0.78, 6.8,  FALSE, 'Early low-quality window, high penalty'),
('2026-Delta',  '2026-11-15', '2026-12-20', 42.0,  0.85, 4.2,  FALSE, 'Late window, decent alignment'),
('2026-Echo',   '2026-10-01', '2026-10-25', 43.0,  0.90, 2.5,  TRUE,  'Withdrawn — telemetry conflict with ISS resupply'),
('2028-Alpha',  '2028-11-01', '2029-01-15', 46.1,  0.82, 5.2,  FALSE, 'Wider window but higher penalty'),
('2028-Beta',   '2028-12-10', '2029-01-05', 43.5,  0.86, 4.0,  FALSE, 'Decent alignment, short window'),
('2029-Alpha',  '2029-06-10', '2029-08-15', 45.0,  0.84, 4.8,  FALSE, 'Extended cycle backup window'),
('2031-Alpha',  '2031-01-20', '2031-03-25', 39.8,  0.95, 0.9,  FALSE, 'Near-ideal opposition window'),
('2031-Beta',   '2031-02-15', '2031-03-10', 40.5,  0.93, 1.2,  FALSE, 'Very good alignment, narrow');

-- ══════════════ FUEL PROVIDERS ══════════════
CREATE TABLE fuel_providers (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR(100) NOT NULL UNIQUE,
    fuel_type VARCHAR(50) NOT NULL,
    cost_per_kg_usd DOUBLE PRECISION NOT NULL,
    reliability_rating DOUBLE PRECISION NOT NULL,
    max_supply_kg DOUBLE PRECISION NOT NULL,
    lead_time_days INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
);

INSERT INTO fuel_providers (provider_name, fuel_type, cost_per_kg_usd, reliability_rating, max_supply_kg, lead_time_days, status) VALUES
('PropelX',          'LOX/LH2',   12.50, 0.97, 150000, 30, 'active'),
('FuelStar',         'LOX/RP-1',   8.75, 0.93, 200000, 45, 'active'),
('OrbitFuel Co',     'LOX/LH2',   11.00, 0.95, 180000, 35, 'active'),
('DeepSpace Fuels',  'LOX/LCH4',  14.20, 0.98, 120000, 25, 'active'),
('BulkProp Inc',     'LOX/RP-1',   7.50, 0.89, 250000, 60, 'pending_review'),
('CryoJet',          'LOX/LH2',   13.80, 0.96, 100000, 20, 'active'),
('NovaFuel',         'LOX/LH2',   10.50, 0.94, 160000, 40, 'active'),
('CheapProp Ltd',    'LOX/RP-1',   6.90, 0.91, 300000, 55, 'active'),
('ArcticFuels',      'LOX/LCH4',  15.80, 0.99, 90000,  15, 'active'),
('GreenProp',        'LOX/LH2',    9.20, 0.92, 170000, 38, 'suspended');

-- ══════════════ MISSION CONSTRAINTS ══════════════
CREATE TABLE mission_constraints (
    id SERIAL PRIMARY KEY,
    constraint_name VARCHAR(100) NOT NULL,
    max_budget_usd DOUBLE PRECISION NOT NULL,
    max_transfer_days INTEGER NOT NULL,
    min_payload_kg DOUBLE PRECISION NOT NULL,
    min_spacecraft_reliability DOUBLE PRECISION NOT NULL,
    min_fuel_provider_reliability DOUBLE PRECISION NOT NULL,
    target_planet VARCHAR(50) NOT NULL,
    mission_type VARCHAR(50) NOT NULL
);

INSERT INTO mission_constraints (constraint_name, max_budget_usd, max_transfer_days, min_payload_kg, min_spacecraft_reliability, min_fuel_provider_reliability, target_planet, mission_type) VALUES
('Mars Cargo 2026',               850000000,   280, 3000, 0.93, 0.92, 'Mars', 'cargo'),
('Mars Cargo 2026 (Preliminary)', 1200000000,  320, 2000, 0.90, 0.88, 'Mars', 'cargo'),
('Mars Crewed 2031',             2500000000,   200, 8000, 0.96, 0.95, 'Mars', 'crewed'),
('Mars Scout 2026',               400000000,   300, 1000, 0.90, 0.88, 'Mars', 'cargo'),
('Mars Express 2026',            1000000000,   220, 5000, 0.96, 0.95, 'Mars', 'cargo'),
('Mars Resupply 2026',            600000000,   260, 2000, 0.95, 0.94, 'Mars', 'cargo'),
('Jupiter Flyby 2028',           1200000000,   900, 2000, 0.94, 0.93, 'Jupiter', 'flyby'),
('Venus Flyby 2027',              500000000,   150, 1500, 0.92, 0.90, 'Venus', 'flyby');
