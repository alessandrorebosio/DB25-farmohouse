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
