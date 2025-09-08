USE farmhouse;

-- Insert demo data
INSERT INTO PERSON (cf, name, surname) VALUES
('RSSMRA80A01H501A', 'Mario', 'Rossi'),
('VRDLGI85B02H502B', 'Luigi', 'Verdi'),
('BNCMRC90C03H503C', 'Marco', 'Bianchi'),
('NRIANA95D04H504D', 'Anna', 'Neri'),
('GLLPLA88E05H505E', 'Paolo', 'Gialli'),
('BLULCA92F06H506F', 'Luca', 'Blu'),
('RSSPLA87G07H507G', 'Paola', 'Rossi'),
('VRDGNN93H08H508H', 'Giovanni', 'Verdi'),
('BNCFBA91I09H509I', 'Fabio', 'Bianchi');

-- Insert users
INSERT INTO USER (username, email, password, cf) VALUES
('mrossi', 'mrossi@farm.com', 'pbkdf2_sha256$1000000$YBihCaRMRFKsgmUJPnaR70$+ZQ29axYaZe0aJ7usxHfqltidP79FMcIH0+T2NiOmYQ=', 'RSSMRA80A01H501A'),
('lverdi', 'lverdi@farm.com', 'pbkdf2_sha256$1000000$YBihCaRMRFKsgmUJPnaR70$+ZQ29axYaZe0aJ7usxHfqltidP79FMcIH0+T2NiOmYQ=', 'VRDLGI85B02H502B'),
('mbianchi', 'mbianchi@farm.com', 'pbkdf2_sha256$1000000$YBihCaRMRFKsgmUJPnaR70$+ZQ29axYaZe0aJ7usxHfqltidP79FMcIH0+T2NiOmYQ=', 'BNCMRC90C03H503C'),
('aneri', 'aneri@farm.com', 'pbkdf2_sha256$1000000$YBihCaRMRFKsgmUJPnaR70$+ZQ29axYaZe0aJ7usxHfqltidP79FMcIH0+T2NiOmYQ=', 'NRIANA95D04H504D'),
('pgialli', 'pgialli@farm.com', 'pbkdf2_sha256$1000000$YBihCaRMRFKsgmUJPnaR70$+ZQ29axYaZe0aJ7usxHfqltidP79FMcIH0+T2NiOmYQ=', 'GLLPLA88E05H505E'),
('lblu', 'lblu@farm.com', 'pbkdf2_sha256$1000000$YBihCaRMRFKsgmUJPnaR70$+ZQ29axYaZe0aJ7usxHfqltidP79FMcIH0+T2NiOmYQ=', 'BLULCA92F06H506F'),
('prossi', 'prossi@farm.com', 'pbkdf2_sha256$1000000$YBihCaRMRFKsgmUJPnaR70$+ZQ29axYaZe0aJ7usxHfqltidP79FMcIH0+T2NiOmYQ=', 'RSSPLA87G07H507G'),
('gverdi', 'gverdi@farm.com', 'pbkdf2_sha256$1000000$YBihCaRMRFKsgmUJPnaR70$+ZQ29axYaZe0aJ7usxHfqltidP79FMcIH0+T2NiOmYQ=', 'VRDGNN93H08H508H'),
('fbianchi', 'fbianchi@farm.com', 'pbkdf2_sha256$1000000$YBihCaRMRFKsgmUJPnaR70$+ZQ29axYaZe0aJ7usxHfqltidP79FMcIH0+T2NiOmYQ=', 'BNCFBA91I09H509I');

-- Insert employees with roles
INSERT INTO EMPLOYEE (username, role) VALUES
('mrossi', 'ADMIN'),
('lverdi', 'STAFF'),
('mbianchi', 'RECEPTIONIST'),
('aneri', 'CHEF'),
('pgialli', 'LIFEGUARD'),
('lblu', 'FARMER'),
('prossi', 'ANIMATOR'),
('gverdi', 'MAINTENANCE'),
('fbianchi', 'STAFF');

-- Insert shifts
INSERT INTO SHIFT (day, shift_name, start_time, end_time) VALUES
('MON', 'Morning', '08:00', '16:00'),
('MON', 'Evening', '16:00', '00:00'),
('TUE', 'Morning', '08:00', '16:00'),
('TUE', 'Evening', '16:00', '00:00'),
('WED', 'Morning', '08:00', '16:00'),
('WED', 'Evening', '16:00', '00:00'),
('THU', 'Morning', '08:00', '16:00'),
('THU', 'Evening', '16:00', '00:00'),
('FRI', 'Morning', '08:00', '16:00'),
('FRI', 'Evening', '16:00', '00:00');

-- Insert some employee shifts for next week
INSERT INTO EMPLOYEE_SHIFT (employee_username, shift_id, shift_date, status) VALUES
('mrossi', 1, '2023-09-11', 'SCHEDULED'),
('lverdi', 2, '2023-09-11', 'SCHEDULED'),
('mbianchi', 3, '2023-09-12', 'SCHEDULED'),
('aneri', 4, '2023-09-12', 'SCHEDULED'),
('pgialli', 5, '2023-09-13', 'SCHEDULED'),
('lblu', 6, '2023-09-13', 'SCHEDULED'),
('prossi', 7, '2023-09-14', 'SCHEDULED'),
('gverdi', 8, '2023-09-14', 'SCHEDULED'),
('fbianchi', 9, '2023-09-15', 'SCHEDULED');

-- Insert some history records
INSERT INTO EMPLOYEE_HISTORY (username, role, change_date) VALUES
('mrossi', 'ADMIN', '2023-01-01 09:00:00'),
('lverdi', 'STAFF', '2023-01-01 09:00:00'),
('mbianchi', 'RECEPTIONIST', '2023-01-01 09:00:00');

-- Example products
INSERT INTO PRODUCT (name, price) VALUES
('Farm Eggs (12 pcs)', 3.50),
('Organic Milk (1L)', 1.80),
('Fresh Bread', 2.20),
('Cheese Wheel (kg)', 12.00),
('Honey Jar (500g)', 6.50),
('Apple Jam (300g)', 4.20);

-- Example orders
INSERT INTO ORDERS (date, username) VALUES
('2023-09-11 10:15:00', 'mrossi'),
('2023-09-11 17:45:00', 'lverdi'),
('2023-09-12 09:05:00', 'lverdi'),
('2023-09-13 11:30:00', 'mbianchi');

-- Set order and product variables
SET @o1 = (SELECT id FROM ORDERS WHERE date = '2023-09-11 10:15:00' AND username = 'mrossi');
SET @o2 = (SELECT id FROM ORDERS WHERE date = '2023-09-11 17:45:00' AND username = 'lverdi');
SET @o3 = (SELECT id FROM ORDERS WHERE date = '2023-09-12 09:05:00' AND username = 'lverdi');
SET @o4 = (SELECT id FROM ORDERS WHERE date = '2023-09-13 11:30:00' AND username = 'mbianchi');

SET @p_eggs = (SELECT id FROM PRODUCT WHERE name = 'Farm Eggs (12 pcs)');
SET @p_bread = (SELECT id FROM PRODUCT WHERE name = 'Fresh Bread');
SET @p_milk = (SELECT id FROM PRODUCT WHERE name = 'Organic Milk (1L)');
SET @p_honey = (SELECT id FROM PRODUCT WHERE name = 'Honey Jar (500g)');
SET @p_cheese = (SELECT id FROM PRODUCT WHERE name = 'Cheese Wheel (kg)');
SET @p_jam = (SELECT id FROM PRODUCT WHERE name = 'Apple Jam (300g)');

-- Order rows
INSERT INTO ORDER_DETAIL (`order`, product, quantity, unit_price)
SELECT @o1, @p_eggs, 2, price FROM PRODUCT WHERE id = @p_eggs;
INSERT INTO ORDER_DETAIL (`order`, product, quantity, unit_price)
SELECT @o1, @p_bread, 1, price FROM PRODUCT WHERE id = @p_bread;

INSERT INTO ORDER_DETAIL (`order`, product, quantity, unit_price)
SELECT @o2, @p_milk, 3, price FROM PRODUCT WHERE id = @p_milk;
INSERT INTO ORDER_DETAIL (`order`, product, quantity, unit_price)
SELECT @o2, @p_honey, 1, price FROM PRODUCT WHERE id = @p_honey;

INSERT INTO ORDER_DETAIL (`order`, product, quantity, unit_price)
SELECT @o3, @p_cheese, 1, price FROM PRODUCT WHERE id = @p_cheese;
INSERT INTO ORDER_DETAIL (`order`, product, quantity, unit_price)
SELECT @o3, @p_bread, 4, price FROM PRODUCT WHERE id = @p_bread;

INSERT INTO ORDER_DETAIL (`order`, product, quantity, unit_price)
SELECT @o4, @p_jam, 2, price FROM PRODUCT WHERE id = @p_jam;
INSERT INTO ORDER_DETAIL (`order`, product, quantity, unit_price)
SELECT @o4, @p_eggs, 1, price FROM PRODUCT WHERE id = @p_eggs;

-- Demo events (relative to today)
INSERT INTO EVENT (seats, title, description, event_date, created_by) VALUES
(12, 'Cheese Making Workshop', 'Hands-on class led by our head cheesemaker.', DATE_ADD(CURDATE(), INTERVAL 10 DAY), 'aneri'),
(20, 'Kids Animal Feeding', 'Guided feeding time with goats, chickens, and rabbits.', DATE_ADD(CURDATE(), INTERVAL 7 DAY), 'prossi'),
(40, 'Farm-to-Table Dinner', 'Seasonal 4-course dinner with farm-fresh ingredients.', DATE_ADD(CURDATE(), INTERVAL 14 DAY), 'mrossi'),
(25, 'Wine Tasting at Sunset', 'Local wines paired with farmhouse tapas.', DATE_ADD(CURDATE(), INTERVAL 21 DAY), 'gverdi'),
(100, 'Harvest Festival', 'Live music, food stalls, and family activities.', DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'mbianchi');

-- Optional demo subscriptions
INSERT INTO EVENT_SUBSCRIPTION (event, user_username, participants)
SELECT e.id, 'mrossi', 2 FROM EVENT e WHERE e.title = 'Farm-to-Table Dinner';

INSERT INTO EVENT_SUBSCRIPTION (event, user_username, participants)
SELECT e.id, 'lverdi', 3 FROM EVENT e WHERE e.title = 'Harvest Festival';

INSERT INTO EVENT_SUBSCRIPTION (event, user_username, participants)
SELECT e.id, 'aneri', 1 FROM EVENT e WHERE e.title = 'Wine Tasting at Sunset';

-- Past event
INSERT INTO EVENT (seats, title, description, event_date, created_by) VALUES
(50, 'Farm Open Day', 'Open day.', DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'mrossi');

-- Mario Rossi subscribed to a past event
INSERT INTO EVENT_SUBSCRIPTION (event, user_username, subscription_date, participants)
SELECT e.id, 'mrossi', '2025-08-30 00:00:00', 2
FROM EVENT e
WHERE e.title = 'Farm Open Day';
