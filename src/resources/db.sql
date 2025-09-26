DROP DATABASE IF EXISTS farmhouse;
CREATE DATABASE farmhouse;
USE farmhouse;

CREATE TABLE PERSON (
    cf VARCHAR(16) PRIMARY KEY,
    name VARCHAR(32) NOT NULL,
    surname VARCHAR(32) NOT NULL
);

CREATE TABLE USER (
    username VARCHAR(32) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    cf VARCHAR(16) UNIQUE NOT NULL,
    FOREIGN KEY (cf) REFERENCES PERSON(cf)
);

CREATE TABLE EMPLOYEE (
    username VARCHAR(32) PRIMARY KEY,
    role VARCHAR(32) NOT NULL,
    FOREIGN KEY (username) REFERENCES USER(username)
);

CREATE TABLE EMPLOYEE_HISTORY (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(32) NOT NULL,
    fired_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES EMPLOYEE(username)
);

CREATE TABLE SHIFT (
    id INT AUTO_INCREMENT PRIMARY KEY,
    day ENUM('MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN') NOT NULL,
    shift_name VARCHAR(32) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL
);

CREATE TABLE EMPLOYEE_SHIFT (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_username VARCHAR(32) NOT NULL,
    shift_id INT NOT NULL,
    shift_date DATE NOT NULL,
    FOREIGN KEY (employee_username) REFERENCES EMPLOYEE(username),
    FOREIGN KEY (shift_id) REFERENCES SHIFT(id),
    UNIQUE KEY unique_employee_shift (employee_username, shift_date)
);

CREATE TABLE ORDERS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(32) NOT NULL,
    FOREIGN KEY (username) REFERENCES USER(username)
);

CREATE TABLE PRODUCT (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(8,2) NOT NULL CHECK (price > 0)
);

CREATE TABLE ORDER_DETAIL (
    `order` INT NOT NULL,
    product INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(8,2) NOT NULL CHECK (unit_price > 0),
    PRIMARY KEY (`order`, product),
    FOREIGN KEY (product) REFERENCES PRODUCT(id),
    FOREIGN KEY (`order`) REFERENCES ORDERS(id)
);

CREATE TABLE EVENT (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seats INT NOT NULL CHECK (seats > 0),
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    event_date DATE NOT NULL,
    created_by VARCHAR(32) NOT NULL,
    FOREIGN KEY (created_by) REFERENCES EMPLOYEE(username)
);

CREATE TABLE EVENT_SUBSCRIPTION (
    event INT NOT NULL,
    user VARCHAR(32) NOT NULL,
    subscription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    participants INT NOT NULL CHECK (participants > 0),
    PRIMARY KEY (event, user),
    FOREIGN KEY (event) REFERENCES EVENT(id),
    FOREIGN KEY (user) REFERENCES USER(username)
);

CREATE TABLE RESERVATION (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(32) NOT NULL,
    reservation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES USER(username)
);


CREATE TABLE SERVICE (
    id INT AUTO_INCREMENT PRIMARY KEY,
    price DECIMAL(8,2) NOT NULL CHECK (price >= 0),
    type ENUM('RESTAURANT', 'POOL', 'PLAYGROUND', 'ROOM') NOT NULL
);

CREATE TABLE RESERVATION_DETAIL (
    reservation INT NOT NULL,
    service INT NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    people INT NOT NULL CHECK (people > 0),
    CHECK (start_date <= end_date),
    PRIMARY KEY (reservation, service),
    FOREIGN KEY (reservation) REFERENCES RESERVATION(id),
    FOREIGN KEY (service) REFERENCES SERVICE(id)
);

CREATE TABLE RESTAURANT (
    service INT PRIMARY KEY,
    code VARCHAR(3) UNIQUE NOT NULL,
    max_capacity INT NOT NULL CHECK (max_capacity > 0),
    FOREIGN KEY (service) REFERENCES SERVICE(id)
);

CREATE TABLE ROOM (
    service INT PRIMARY KEY,
    code VARCHAR(3) UNIQUE NOT NULL,
    max_capacity INT NOT NULL CHECK (max_capacity > 0),
    FOREIGN KEY (service) REFERENCES SERVICE(id)
);

CREATE TABLE REVIEW (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `user` VARCHAR(32) NOT NULL,
    service INT NULL,
    event INT NULL,
    rating TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user`) REFERENCES USER(username) ON DELETE CASCADE,
    FOREIGN KEY (service) REFERENCES SERVICE(id) ON DELETE CASCADE,
    FOREIGN KEY (event) REFERENCES EVENT(id) ON DELETE CASCADE,
    CHECK ((service IS NULL) + (event IS NULL) = 1),
    UNIQUE KEY unique_user_service_review (`user`, service),
    UNIQUE KEY unique_user_event_review (`user`, event)
);

-- Trigger: allow reviews only after the event/service has been used
DROP TRIGGER IF EXISTS trg_review_before_insert;
DELIMITER $$
CREATE TRIGGER trg_review_before_insert
BEFORE INSERT ON REVIEW
FOR EACH ROW
BEGIN
  DECLARE cnt INT DEFAULT 0;

  -- Exactly one between event and service must be set
  IF (NEW.event IS NOT NULL AND NEW.service IS NOT NULL) OR (NEW.event IS NULL AND NEW.service IS NULL) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Set either event or service (not both) for the review.';
  END IF;

  -- Event check: user must be subscribed and the event date must be in the past
  IF NEW.event IS NOT NULL THEN
    SELECT COUNT(*)
      INTO cnt
      FROM EVENT e
      JOIN EVENT_SUBSCRIPTION es
        ON es.event = e.id
       AND es.`user` = NEW.`user`
     WHERE e.id = NEW.event
       AND e.event_date < CURDATE(); -- event already occurred (DATE type)

    IF cnt = 0 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'You can review the event only if you were subscribed and the event date is in the past.';
    END IF;
  END IF;

  -- Service check: the user must have a reservation for that service that has already ended
  IF NEW.service IS NOT NULL THEN
    SELECT COUNT(*)
      INTO cnt
      FROM RESERVATION r
      JOIN RESERVATION_DETAIL rd
        ON rd.reservation = r.id
       AND rd.service = NEW.service
     WHERE r.username = NEW.`user`
       AND rd.end_date < NOW(); -- reservation already completed

    IF cnt = 0 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'You can review the service only after you have used it (completed reservation).';
    END IF;
  END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trg_review_before_update;
DELIMITER $$
CREATE TRIGGER trg_review_before_update
BEFORE UPDATE ON REVIEW
FOR EACH ROW
BEGIN
  DECLARE cnt INT DEFAULT 0;

  -- Exactly one between event and service must be set
  IF (NEW.event IS NOT NULL AND NEW.service IS NOT NULL) OR (NEW.event IS NULL AND NEW.service IS NULL) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Set either event or service (not both) for the review.';
  END IF;

  -- Event check: user must be subscribed and the event date must be in the past
  IF NEW.event IS NOT NULL THEN
    SELECT COUNT(*)
      INTO cnt
      FROM EVENT e
      JOIN EVENT_SUBSCRIPTION es
        ON es.event = e.id
       AND es.`user` = NEW.`user`
     WHERE e.id = NEW.event
       AND e.event_date < CURDATE();

    IF cnt = 0 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'You can review the event only if you were subscribed and the event date is in the past.';
    END IF;
  END IF;

  -- Service check: the user must have a reservation for that service that has already ended
  IF NEW.service IS NOT NULL THEN
    SELECT COUNT(*)
      INTO cnt
      FROM RESERVATION r
      JOIN RESERVATION_DETAIL rd
        ON rd.reservation = r.id
       AND rd.service = NEW.service
     WHERE r.username = NEW.`user`
       AND rd.end_date < NOW();

    IF cnt = 0 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'You can review the service only after you have used it (completed reservation).';
    END IF;
  END IF;
END$$
DELIMITER ;

-- View: active employees (present in EMPLOYEE) with personal info and last role change date
CREATE VIEW active_employees AS
SELECT 
    e.username,
    u.email,
    p.name,
    p.surname,
    e.role
FROM EMPLOYEE e
JOIN USER u ON e.username = u.username
JOIN PERSON p ON u.cf = p.cf
WHERE e.username NOT IN (
    SELECT username FROM EMPLOYEE_HISTORY
);
