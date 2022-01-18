--\conninfo
--\dn
--\dt reservations.*
--
--CREATE TABLE reservations.reservation_hotels
--(
--    id        SERIAL PRIMARY KEY,
--    hotelUid uuid         NOT NULL UNIQUE,
--    name      VARCHAR(255) NOT NULL,
--    country   VARCHAR(80)  NOT NULL,
--    city      VARCHAR(80)  NOT NULL,
--    address   VARCHAR(255) NOT NULL,
--    stars     INT,
--    price     INT          NOT NULL
--);
--
--\dt reservations.*
--
--CREATE TABLE reservations.reservation_reservation
--(
--    id              SERIAL PRIMARY KEY,
--    reservationUid uuid UNIQUE NOT NULL,
--    username        VARCHAR(80) NOT NULL,
--    payment_uid     uuid        NOT NULL,
--    hotel_id        INT REFERENCES reservations.reservation_hotels (id),
--    status          VARCHAR(20) NOT NULL
--        CHECK (status IN ('PAID', 'CANCELED')),
--    startDate      TIMESTAMP WITH TIME ZONE,
--    endDate        TIMESTAMP WITH TIME ZONE
--);
--
--\dt reservations.*
--
--
--CREATE TABLE payments.payment_payment
--(
--    id          SERIAL PRIMARY KEY,
--    paymentUid  uuid        NOT NULL,
--    status      VARCHAR(20) NOT NULL
--        CHECK (status IN ('PAID', 'CANCELED')),
--    price       INT         NOT NULL
--);
--
--
--CREATE TABLE loyalties.loyalty_loyalty
--(
--    id                SERIAL PRIMARY KEY,
--    username          VARCHAR(80) NOT NULL UNIQUE,
--    reservationCount INT         NOT NULL DEFAULT 0,
--    status            VARCHAR(80) NOT NULL DEFAULT 'BRONZE'
--        CHECK (status IN ('BRONZE', 'SILVER', 'GOLD')),
--    discount          INT         NOT NULL
--);

-- то что выше джанго создаёт сам, именно так loyalty_loyalty, payment_payment и тд

INSERT INTO reservations.reservation_hotel ("hotelUid", name, country, city, address, stars, price)
VALUES ('049161bb-badd-4fa8-9d90-87c9a82b0668', 'Ararat Park Hyatt Moscow', 'Россия', 'Москва', 'Неглинная ул., 4', 5, 10000);

INSERT INTO loyalties.loyalty_loyalty (username, "reservationCount", status, discount)
VALUES ('Test Max', 25, 'G', 10);
