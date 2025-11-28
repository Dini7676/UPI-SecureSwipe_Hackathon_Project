-- Seed sample data
INSERT INTO users(name, mobile, email, role) VALUES
('Alice', '9000000001', 'alice@example.com', 'USER'),
('Bob', '9000000002', 'bob@example.com', 'USER');

INSERT INTO merchants(name, upi_id, category) VALUES
('Cafe Mocha', 'cafe@upi', 'FOOD'),
('FastTravel', 'fasttravel@upi', 'TRAVEL');

INSERT INTO admin(name, email, role) VALUES
('Admin One', 'admin@example.com', 'ADMIN');
