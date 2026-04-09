-- ============================================================
-- Seed data: realistic fish production mock data
-- ============================================================

-- Production Lines
INSERT INTO production.prod_lines (line_id, line_name, line_type, area, max_capacity_kg) VALUES
(1, 'Line 1', 'filleting', 'fresh', 5000),
(2, 'Line 2', 'filleting', 'fresh', 4500),
(3, 'Line 3', 'packing', 'fresh', 6000),
(4, 'Smoke Line', 'smoking', 'smoked', 2000),
(5, 'VA Line', 'value-added', 'value-added', 3000),
(6, 'Packing A', 'packing', 'fresh', 5500);

-- Products (PLU)
INSERT INTO production.products (product_code, description, category, species, customer, pack_size_g, shelf_life_days, allergens, hazard_class) VALUES
('COD-200-LDL',  'Cod Fillet Skinless 200g',       'fillet',    'cod',     'Lidl',    200, 7,  'fish',                'HIGH'),
('COD-280-ICE',  'Cod Loin 280g',                   'loin',     'cod',     'Iceland',  280, 7,  'fish',                'HIGH'),
('SAL-130-LDL',  'Salmon Fillet Portion 130g',      'fillet',    'salmon',  'Lidl',    130, 7,  'fish',                'HIGH'),
('SAL-200-TES',  'Salmon Darnes 200g',              'portion',   'salmon',  'Tesco',   200, 6,  'fish',                'HIGH'),
('HAD-170-ICE',  'Smoked Haddock Fillet 170g',      'smoked',    'haddock', 'Iceland',  170, 10, 'fish',                'HIGH'),
('MAC-150-LDL',  'Mackerel Fillet Peppered 150g',   'smoked',    'mackerel','Lidl',    150, 14, 'fish, mustard',       'HIGH'),
('FCA-300-ICE',  'Fish Cakes Cod & Parsley 300g',   'value-add', 'cod',     'Iceland',  300, 5,  'fish, wheat, egg',    'HIGH'),
('FCA-400-TES',  'Fish Cakes Premium 400g',         'value-add', 'cod',     'Tesco',   400, 5,  'fish, wheat, egg, milk','HIGH'),
('PRN-200-LDL',  'King Prawns 200g',                'shellfish', 'prawn',   'Lidl',    200, 5,  'crustaceans',         'HIGH'),
('SEA-500-ICE',  'Seafood Selection 500g',          'mixed',     'mixed',   'Iceland',  500, 4,  'fish, crustaceans, molluscs','HIGH');

-- Traceability batches
INSERT INTO production.traceability (trace_id, batch_code, supplier, species, catch_area, catch_method, vessel_name, landing_date, kill_date, received_date, received_temp_c, use_by_date, country_origin, certified) VALUES
('TR-2025-0401', 'BC-COD-8831',  'Grimsby Fresh Ltd',    'cod',     'North Sea IV',   'trawl',       'Harvest Moon',    '2025-03-28', '2025-03-28', '2025-03-30', 1.2, '2025-04-06', 'UK',      'MSC'),
('TR-2025-0402', 'BC-SAL-4421',  'Scottish Salmon Co',   'salmon',  'Scotland West',  'farmed',      NULL,              '2025-03-29', '2025-03-29', '2025-03-31', 0.8, '2025-04-07', 'UK',      'ASC'),
('TR-2025-0403', 'BC-HAD-7712',  'Nordic Fish Supply',   'haddock', 'Norwegian Sea',  'line caught', 'Polar Star',      '2025-03-27', '2025-03-27', '2025-03-30', 1.5, '2025-04-08', 'Norway',  'MSC'),
('TR-2025-0404', 'BC-COD-8832',  'Grimsby Fresh Ltd',    'cod',     'North Sea IV',   'trawl',       'Sea Ranger',      '2025-04-01', '2025-04-01', '2025-04-02', 1.0, '2025-04-09', 'UK',      'MSC'),
('TR-2025-0405', 'BC-MAC-2201',  'Cornish Pelagic',      'mackerel','Celtic Sea VII', 'purse seine', 'Atlantic Spirit', '2025-03-30', '2025-03-30', '2025-04-01', 0.5, '2025-04-14', 'UK',      'MSC'),
('TR-2025-0406', 'BC-PRN-5501',  'Thai Union Frozen',    'prawn',   'Indian Ocean',   'farmed',      NULL,              '2025-02-15', '2025-02-15', '2025-03-20', -18.0,'2025-08-15', 'Thailand','ASC');

-- Production Runs (matching RunNumber pattern from screenshots)
INSERT INTO production.runs (run_number, production_date, shift_code, shift_date, prod_line, product_code, spec, prog_id, target_qty_kg, actual_qty_kg, waste_kg, yield_pct, status, complete, kill_date, trace_id, created_by, created_date) VALUES
('007208', '2025-04-01', 'DAY',   '2025-04-01', 1, 'COD-200-LDL', 'SP-COD-01', 'P001', 800.00,  762.50, 37.50, 95.3, 'complete', 1, '2025-03-28', 'TR-2025-0401', 'PAWAN', '2025-04-01 06:15:00'),
('007216', '2025-04-01', 'DAY',   '2025-04-01', 2, 'SAL-130-LDL', 'SP-SAL-01', 'P002', 500.00,  485.20, 14.80, 97.0, 'complete', 1, '2025-03-29', 'TR-2025-0402', 'PAWAN', '2025-04-01 06:30:00'),
('007217', '2025-04-01', 'DAY',   '2025-04-01', 3, 'COD-280-ICE', 'SP-COD-02', 'P003', 1200.00, 1138.00, 62.00, 94.8, 'complete', 1, '2025-03-28', 'TR-2025-0401', 'PAWAN', '2025-04-01 07:00:00'),
('007225', '2025-04-02', 'DAY',   '2025-04-02', 1, 'HAD-170-ICE', 'SP-HAD-01', 'P004', 600.00,  574.80, 25.20, 95.8, 'complete', 1, '2025-03-27', 'TR-2025-0403', 'JSMITH','2025-04-02 06:15:00'),
('007228', '2025-04-02', 'DAY',   '2025-04-02', 5, 'FCA-300-ICE', 'SP-FCA-01', 'P005', 900.00,  882.00, 18.00, 98.0, 'complete', 1, '2025-04-01', 'TR-2025-0404', 'PAWAN', '2025-04-02 06:30:00'),
('007230', '2025-04-02', 'NIGHT', '2025-04-02', 2, 'SAL-200-TES', 'SP-SAL-02', 'P006', 700.00,  665.00, 35.00, 95.0, 'complete', 1, '2025-03-29', 'TR-2025-0402', 'AJONES','2025-04-02 18:00:00'),
('007232', '2025-04-03', 'DAY',   '2025-04-03', 1, 'COD-200-LDL', 'SP-COD-01', 'P001', 850.00,  799.00, 51.00, 94.0, 'complete', 1, '2025-04-01', 'TR-2025-0404', 'PAWAN', '2025-04-03 06:15:00'),
('007233', '2025-04-03', 'DAY',   '2025-04-03', 4, 'MAC-150-LDL', 'SP-MAC-01', 'P007', 400.00,  388.00, 12.00, 97.0, 'complete', 1, '2025-03-30', 'TR-2025-0405', 'JSMITH','2025-04-03 07:00:00'),
('007234', '2025-04-03', 'DAY',   '2025-04-03', 3, 'FCA-400-TES', 'SP-FCA-02', 'P008', 1000.00, 960.00, 40.00, 96.0, 'complete', 1, '2025-04-01', 'TR-2025-0404', 'PAWAN', '2025-04-03 07:15:00'),
('007235', '2025-04-04', 'DAY',   '2025-04-04', 1, 'COD-200-LDL', 'SP-COD-01', 'P001', 800.00,  NULL,   NULL,  NULL, 'active',   0, '2025-04-01', 'TR-2025-0404', 'PAWAN', '2025-04-04 06:15:00'),
('007237', '2025-04-04', 'DAY',   '2025-04-04', 2, 'PRN-200-LDL', 'SP-PRN-01', 'P009', 350.00,  340.00,  10.00, 97.1, 'complete', 1, '2025-02-15', 'TR-2025-0406', 'AJONES','2025-04-04 06:30:00'),
('007238', '2025-04-04', 'NIGHT', '2025-04-04', 3, 'SEA-500-ICE', 'SP-SEA-01', 'P010', 800.00,  756.00, 44.00, 94.5, 'complete', 1, '2025-04-01', 'TR-2025-0404', 'JSMITH','2025-04-04 18:00:00'),
('007239', '2025-04-05', 'DAY',   '2025-04-05', 1, 'SAL-130-LDL', 'SP-SAL-01', 'P002', 550.00,  528.00, 22.00, 96.0, 'complete', 1, '2025-03-29', 'TR-2025-0402', 'PAWAN', '2025-04-05 06:15:00'),
('007240', '2025-04-05', 'DAY',   '2025-04-05', 5, 'FCA-300-ICE', 'SP-FCA-01', 'P005', 950.00,  931.00, 19.00, 98.0, 'complete', 1, '2025-04-01', 'TR-2025-0404', 'PAWAN', '2025-04-05 06:30:00');

-- Temperature logs
INSERT INTO production.temperature_logs (location, reading_time, temp_celsius, target_min, target_max, in_range, recorded_by) VALUES
('chiller_1',     '2025-04-01 06:00', 1.8, -1.0, 4.0, 1, 'PAWAN'),
('chiller_1',     '2025-04-01 10:00', 2.1, -1.0, 4.0, 1, 'PAWAN'),
('chiller_1',     '2025-04-01 14:00', 2.5, -1.0, 4.0, 1, 'JSMITH'),
('chiller_2',     '2025-04-01 06:00', 3.2, -1.0, 4.0, 1, 'PAWAN'),
('chiller_2',     '2025-04-01 10:00', 5.1, -1.0, 4.0, 0, 'PAWAN'),  -- BREACH
('chiller_2',     '2025-04-01 14:00', 3.8, -1.0, 4.0, 1, 'JSMITH'),
('blast_freezer', '2025-04-01 06:00', -22.0, -25.0, -18.0, 1, 'PAWAN'),
('blast_freezer', '2025-04-01 14:00', -20.5, -25.0, -18.0, 1, 'JSMITH'),
('goods_in',      '2025-04-01 08:00', 1.2, -1.0, 5.0, 1, 'AJONES'),
('despatch',      '2025-04-01 16:00', 2.0, -1.0, 5.0, 1, 'PAWAN'),
('chiller_1',     '2025-04-02 06:00', 2.0, -1.0, 4.0, 1, 'PAWAN'),
('chiller_1',     '2025-04-02 10:00', 1.9, -1.0, 4.0, 1, 'JSMITH'),
('chiller_2',     '2025-04-02 06:00', 3.0, -1.0, 4.0, 1, 'PAWAN'),
('chiller_2',     '2025-04-02 10:00', 4.5, -1.0, 4.0, 0, 'JSMITH'),  -- BREACH
('goods_in',      '2025-04-02 08:30', 0.8, -1.0, 5.0, 1, 'AJONES');

-- Non-conformance records
INSERT INTO production.non_conformance (nc_date, run_number, product_code, nc_type, severity, description, root_cause, corrective_action, raised_by, status) VALUES
('2025-04-01', '007217', 'COD-280-ICE', 'weight',       'minor',    'Average weight 3g below target on 12 packs', 'Portion cutter blade alignment', 'Blade recalibrated, re-checked after 50 packs', 'PAWAN', 'closed'),
('2025-04-01', NULL,      NULL,          'temp',         'major',    'Chiller 2 reached 5.1C at 10:00 check',      'Door left open during cleaning', 'Door interlock check added to cleaning SOP', 'PAWAN', 'closed'),
('2025-04-02', '007230', 'SAL-200-TES', 'label',        'critical', 'Wrong use-by date printed on 24 packs',       'Date offset not updated for new batch', 'All 24 packs quarantined and relabelled', 'AJONES', 'closed'),
('2025-04-03', '007234', 'FCA-400-TES', 'foreign_body', 'critical', 'Metal fragment detected by inline detector',  'Worn blade on mixer', 'Blade replaced, batch before detection quarantined for re-screen', 'JSMITH', 'investigating'),
('2025-04-04', '007238', 'SEA-500-ICE', 'weight',       'minor',    'Giveaway exceeding 5% on seafood selection',  'Operator overfilling trays', 'Briefing on portion control, target weight reminder posted', 'PAWAN', 'open');

-- Shifts
INSERT INTO production.shifts (shift_date, shift_code, line_id, headcount, planned_hours, actual_hours, overtime_hours, output_kg, kg_per_head) VALUES
('2025-04-01', 'DAY',   1, 11, 88.0, 92.5, 4.5, 762.50, 69.3),
('2025-04-01', 'DAY',   2, 8,  64.0, 64.0, 0.0, 485.20, 60.7),
('2025-04-01', 'DAY',   3, 12, 96.0, 96.0, 0.0, 1138.00, 94.8),
('2025-04-02', 'DAY',   1, 11, 88.0, 88.0, 0.0, 574.80, 52.3),
('2025-04-02', 'DAY',   5, 9,  72.0, 74.0, 2.0, 882.00, 98.0),
('2025-04-02', 'NIGHT', 2, 7,  56.0, 58.0, 2.0, 665.00, 95.0),
('2025-04-03', 'DAY',   1, 11, 88.0, 90.0, 2.0, 799.00, 72.6),
('2025-04-03', 'DAY',   4, 6,  48.0, 48.0, 0.0, 388.00, 64.7),
('2025-04-03', 'DAY',   3, 12, 96.0, 98.0, 2.0, 960.00, 80.0),
('2025-04-04', 'DAY',   2, 8,  64.0, 64.0, 0.0, 340.00, 42.5),
('2025-04-04', 'NIGHT', 3, 10, 80.0, 82.0, 2.0, 756.00, 75.6),
('2025-04-05', 'DAY',   1, 11, 88.0, 88.0, 0.0, 528.00, 48.0),
('2025-04-05', 'DAY',   5, 9,  72.0, 72.0, 0.0, 931.00, 103.4);
