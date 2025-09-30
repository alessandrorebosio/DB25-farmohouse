use farmhouse;
-- Top 5 most booked services (by booking details),
-- showing a friendly name with subtype code (Restaurant/Room)
SELECT
  CASE
    WHEN s.type = 'RESTAURANT' THEN CONCAT('Restaurant - ', r.code)
    WHEN s.type = 'ROOM' THEN CONCAT('Room - ', ro.code)
    ELSE s.type
  END AS service_name,
  COUNT(rd.service) AS booking_count
FROM SERVICE AS s
LEFT JOIN RESTAURANT AS r
  ON s.id = r.service
LEFT JOIN ROOM AS ro
  ON s.id = ro.service
JOIN BOOKING_DETAIL AS rd
  ON s.id = rd.service
GROUP BY
  s.id,
  s.type,
  r.code,
  ro.code
ORDER BY
  booking_count DESC
LIMIT 5;

-- Top 5 products by total quantities sold (sum of ORDER_DETAIL.quantity)
SELECT
  p.name AS product_name,
  SUM(od.quantity) AS total_quantity
FROM PRODUCT AS p
JOIN ORDER_DETAIL AS od
  ON p.id = od.product
GROUP BY
  p.id,
  p.name
ORDER BY
  total_quantity DESC
LIMIT 5;

-- Top 5 events by total participants (sum of EVENT_SUBSCRIPTION.participants)
SELECT
  e.title AS event_title,
  e.event_date,
  SUM(es.participants) AS total_participants
FROM EVENT AS e
JOIN EVENT_SUBSCRIPTION AS es
  ON e.id = es.event
GROUP BY
  e.id,
  e.title,
  e.event_date
ORDER BY
  total_participants DESC
LIMIT 5;

-- Top 5 products by total revenue (quantity * unit_price)
SELECT
  p.name AS product_name,
  SUM(od.quantity * od.unit_price) AS total_revenue
FROM PRODUCT AS p
JOIN ORDER_DETAIL AS od
  ON p.id = od.product
GROUP BY
  p.id,
  p.name
ORDER BY
  total_revenue DESC
LIMIT 5;

-- Quick KPIs: total customers, employees, orders, revenue, bookings
-- Note: expects tables USER, EMPLOYEE, ORDERS, ORDER_DETAIL, BOOKING
SELECT
  (SELECT COUNT(*) FROM USER) AS total_customers,
  (SELECT COUNT(*) FROM EMPLOYEE) AS total_employees,
  (SELECT COUNT(*) FROM ORDERS) AS total_orders,
  (SELECT ROUND(SUM(od.quantity * od.unit_price), 2) FROM ORDER_DETAIL AS od) AS total_revenue,
  (SELECT COUNT(*) FROM BOOKING) AS total_bookings;

-- Room availability for a given period and people
-- Requires session variables:
--   @n_persone, @data_inizio (DATETIME), @data_fine (DATETIME)
SELECT
  ro.code AS camera,
  s.price AS prezzo,
  ro.max_capacity
FROM ROOM AS ro
JOIN SERVICE AS s
  ON s.id = ro.service
WHERE
  ro.max_capacity >= @n_persone
  AND ro.service NOT IN (
    SELECT rd.service
    FROM BOOKING_DETAIL AS rd
    WHERE NOT (rd.end_date <= @data_inizio OR rd.start_date >= @data_fine)
  );

-- Restaurant availability with remaining seats in a period
-- Requires session variables: @data_inizio, @data_fine, @n_partecipanti
SELECT
  r.code AS ristorante,
  s.price AS prezzo,
  r.max_capacity,
  (r.max_capacity - IFNULL(SUM(rd.people), 0)) AS posti_disponibili
FROM RESTAURANT AS r
JOIN SERVICE AS s
  ON s.id = r.service
LEFT JOIN BOOKING_DETAIL AS rd
  ON rd.service = r.service
  AND NOT (rd.end_date <= @data_inizio OR rd.start_date >= @data_fine)
GROUP BY
  r.service,
  r.code,
  s.price,
  r.max_capacity
HAVING
  posti_disponibili >= @n_partecipanti;

-- Insert a REVIEW for an event attended by user 'mrossi'
-- Guards: only if subscribed, past event, and review does not already exist
INSERT INTO REVIEW (user, event, rating, comment)
SELECT
    'mrossi' AS user,
    e.id AS event,
    5 AS rating,
    'Amazing experience! Will definitely come again.' AS comment
FROM EVENT AS e
INNER JOIN EVENT_SUBSCRIPTION AS es
    ON e.id = es.event
    AND es.user = 'mrossi'
WHERE
    e.title = 'Farm Open Day'
    AND e.event_date < CURDATE()
    AND NOT EXISTS (
        SELECT 1
        FROM REVIEW AS r
        WHERE r.user = 'mrossi' AND r.event = e.id
    )
LIMIT 1;

-- Insert a REVIEW for a service used by user 'aneri' (completed booking)
-- Guards: only for RESTAURANT services and avoid duplicate reviews
INSERT INTO REVIEW (user, service, rating, comment)
SELECT
  'aneri' AS user,
  s.id AS service,
  4 AS rating,
  'Good service and friendly staff.' AS comment
FROM SERVICE AS s
INNER JOIN BOOKING_DETAIL AS rd
  ON s.id = rd.service
INNER JOIN BOOKING AS r
  ON rd.booking = r.id
WHERE
  r.username = 'aneri'
  AND rd.end_date < NOW()
  AND s.type = 'RESTAURANT'
  AND NOT EXISTS (
    SELECT 1
    FROM REVIEW AS rev
    WHERE rev.user = 'aneri' AND rev.service = s.id
  )
LIMIT 1;

-- Update an existing event review for user 'mrossi' (Farm Open Day)
-- Refreshes rating, comment, and timestamp
UPDATE REVIEW
SET
  rating = 4,
  comment = 'Very good event, but could use more activities. Overall enjoyed it!',
  created_at = NOW()
WHERE
  user = 'mrossi'
  AND event = (
    SELECT id
    FROM EVENT
    WHERE title = 'Farm Open Day'
  )
  AND id IS NOT NULL;

-- Upsert-like subscription: insert or update participants for 'lblu' on 'Harvest Festival'
INSERT INTO EVENT_SUBSCRIPTION (event, user, participants)
SELECT
  e.id,
  u.username,
  4
FROM EVENT AS e
CROSS JOIN USER AS u
WHERE
  e.title = 'Harvest Festival'
  AND u.username = 'lblu'
ON DUPLICATE KEY UPDATE
  participants = 4;

-- Create a booking today for 'gverdi' only if not already present
INSERT INTO BOOKING (username, booking_date)
SELECT
  'gverdi',
  NOW()
WHERE NOT EXISTS (
  SELECT 1
  FROM BOOKING
  WHERE
    username = 'gverdi'
  AND DATE(booking_date) = CURDATE()
);

-- Capture the last inserted booking id in @new_booking_id
SET @new_booking_id = LAST_INSERT_ID();

-- Add a RESTAURANT booking detail (table T01) for the created booking
INSERT INTO BOOKING_DETAIL (booking, service, start_date, end_date, people, unit_price)
SELECT
  @new_booking_id AS booking,
  s.id AS service,
  '2024-01-25 19:00:00' AS start_date,
  '2024-01-25 21:00:00' AS end_date,
  2 AS people,
  s.price AS unit_price
FROM SERVICE AS s
INNER JOIN RESTAURANT AS r
  ON s.id = r.service
WHERE r.code = 'T01'
LIMIT 1;

-- Create a second booking (1 hour later) for 'fbianchi' if not already present
INSERT INTO BOOKING (username, booking_date)
SELECT
  'fbianchi',
  DATE_ADD(NOW(), INTERVAL 1 HOUR)
WHERE NOT EXISTS (
  SELECT 1
  FROM BOOKING
  WHERE
    username = 'fbianchi'
  AND DATE(booking_date) = CURDATE()
);

-- Capture the new booking id in @room_booking_id
SET @room_booking_id = LAST_INSERT_ID();

-- Add a ROOM booking detail (room R03) to the created booking
INSERT INTO BOOKING_DETAIL (booking, service, start_date, end_date, people, unit_price)
SELECT
  @room_booking_id AS booking,
  s.id AS service,
  '2024-01-26 15:00:00' AS start_date,
  '2024-01-28 11:00:00' AS end_date,
  2 AS people,
  s.price AS unit_price
FROM SERVICE AS s
INNER JOIN ROOM AS r
  ON s.id = r.service
WHERE r.code = 'R03'
LIMIT 1;

-- Delete all BOOKING_DETAIL rows associated with @booking_id
-- Requires variables: @booking_id
DELETE FROM BOOKING_DETAIL
WHERE booking = @booking_id;

-- Then delete the BOOKING itself for the given user
-- Requires variables: @booking_id, @username
DELETE FROM BOOKING
WHERE
  id = @booking_id
    AND username = @username;

-- Cancel an event subscription in the future for @username and @event_id
-- Requires variables: @username, @event_id
DELETE FROM EVENT_SUBSCRIPTION
WHERE
    user = @username
    AND event = @event_id
    AND EXISTS (
        SELECT 1
        FROM EVENT AS e
        WHERE
            e.id = @event_id
            AND e.event_date > CURDATE()
    );

-- Delete an empty booking (no past or current details)
-- Requires variables: @booking_id, @username
DELETE FROM BOOKING
WHERE
  id = @booking_id
    AND username = @username
    AND NOT EXISTS (
    SELECT 1
    FROM BOOKING_DETAIL AS rd
        WHERE
  rd.booking = @booking_id
            AND rd.start_date <= NOW()
    );

-- Get user profile details with role classification (employee/customer)
SELECT
  u.username,
  u.email,
  u.password,
  p.name,
  p.surname,
  CASE WHEN e.username IS NOT NULL THEN 'employee' ELSE 'customer' END AS user_type,
  e.role AS employee_role
FROM USER AS u
INNER JOIN PERSON AS p
  ON u.cf = p.cf
LEFT JOIN EMPLOYEE AS e
  ON u.username = e.username
WHERE
  u.username = 'mrossi'
  OR u.email = 'mrossi@farm.com';

-- Create a new order for user 'aneri' today if one doesn't already exist
INSERT INTO ORDERS (username, date)
SELECT
    'aneri',
    NOW()
WHERE NOT EXISTS (
    SELECT 1
    FROM ORDERS
    WHERE
        username = 'aneri'
        AND DATE(date) = CURDATE()
);

-- Capture the new order id in @new_order_id
SET @new_order_id = LAST_INSERT_ID();

-- Add items to the newly created order: eggs, bread, honey (with current product price)
INSERT INTO ORDER_DETAIL (`order`, product, quantity, unit_price)
SELECT
  @new_order_id AS order_id,
  p.id AS product_id,
  3 AS quantity,
  p.price AS unit_price
FROM PRODUCT AS p
WHERE p.name = 'Farm Eggs (12 pcs)'
LIMIT 1;

INSERT INTO ORDER_DETAIL (`order`, product, quantity, unit_price)
SELECT
  @new_order_id AS order_id,
  p.id AS product_id,
  2 AS quantity,
  p.price AS unit_price
FROM PRODUCT AS p
WHERE p.name = 'Fresh Bread'
LIMIT 1;

INSERT INTO ORDER_DETAIL (`order`, product, quantity, unit_price)
SELECT
  @new_order_id AS order_id,
  p.id AS product_id,
  1 AS quantity,
  p.price AS unit_price
FROM PRODUCT AS p
WHERE p.name = 'Honey Jar (500g)'
LIMIT 1;
