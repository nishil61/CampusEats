CREATE DATABASE IF NOT EXISTS canteen;
USE canteen;

DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','vendor','customer') NOT NULL
);

DROP TABLE IF EXISTS vendors;
CREATE TABLE vendors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT
);

DROP TABLE IF EXISTS menu_items;
CREATE TABLE menu_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vendor_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    available BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    status ENUM('inmaking','ready','pickedup') NOT NULL DEFAULT 'inmaking',
    payment_id VARCHAR(255),
    razorpay_order_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS order_items;
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    menu_item_id INT NOT NULL,
    quantity INT NOT NULL,
    price_at_time DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE CASCADE
);

INSERT INTO vendors (name, description) VALUES
('Fee Fa Foo', 'Chinese and Indian street food'),
('Mech Cafe', 'Specialty puffs and snacks'),
('Poornima Kitchen', 'Ice creams and snacks'),
('Nescafe', 'Beverages and quick bites');

INSERT INTO menu_items (vendor_id, name, description, price, available) VALUES
(1, 'Chinese', 'Delicious Chinese noodles with vegetables', 100.00, TRUE),
(1, 'Manchurian', 'Crispy vegetable balls in tangy sauce', 80.00, TRUE),
(1, 'Dabeli', 'Spicy potato filling in bun', 15.00, TRUE),
(1, 'Vadapav', 'Spicy potato vada in bun', 15.00, TRUE),
(1, 'Katka Dabeli', 'Special dabeli with extra toppings', 50.00, TRUE);

INSERT INTO menu_items (vendor_id, name, description, price, available) VALUES
(2, 'Butter Puff', 'Flaky puff with butter filling', 15.00, TRUE),
(2, 'Chinese Puff', 'Puff with Chinese style filling', 20.00, TRUE),
(2, 'Butter Garlic Puff', 'Puff with butter garlic filling', 25.00, TRUE);

INSERT INTO menu_items (vendor_id, name, description, price, available) VALUES
(3, 'Chocolate Ice cream', 'Rich chocolate flavored ice cream', 50.00, TRUE),
(3, 'Thumbs-Up', 'Refreshing cola drink', 10.00, TRUE),
(3, 'Bread Pakoda', 'Deep fried bread with potato filling', 20.00, TRUE),
(3, 'Bhajiya', 'Crispy vegetable fritters', 30.00, TRUE);

INSERT INTO menu_items (vendor_id, name, description, price, available) VALUES
(4, 'Garlic Bread', 'Toasted bread with garlic butter', 70.00, TRUE),
(4, 'Veg. Sandwich', 'Fresh vegetable sandwich', 40.00, TRUE),
(4, 'Maggie', 'Instant noodles with vegetables', 50.00, TRUE),
(4, 'Tea', 'Hot tea with milk', 10.00, TRUE),
(4, 'Coffee', 'Hot coffee with milk', 10.00, TRUE); 