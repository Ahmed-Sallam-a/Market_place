-- Create Product table
CREATE TABLE product (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100),
    selling_price FLOAT,
    discounted_price FLOAT,
    description TEXT,
    composition TEXT DEFAULT '',
    prodapp TEXT DEFAULT '',
    category VARCHAR(3),
    product_image VARCHAR(255),
    Quantity INTEGER DEFAULT 1
);

-- Create Customer table
CREATE TABLE customer (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    name VARCHAR(200),
    locality VARCHAR(200),
    city VARCHAR(50),
    mobile INTEGER DEFAULT 0,
    zipcode INTEGER,
    state VARCHAR(100)
);

-- Create Cart table
CREATE TABLE cart (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES product(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1
);

-- Create Payment table
CREATE TABLE payment (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    amount FLOAT,
    razorpay_order_id VARCHAR(100),
    razorpay_payment_status VARCHAR(100),
    razorpay_payment_id VARCHAR(100),
    paid BOOLEAN DEFAULT FALSE
);

-- Create OrderPlaced table
CREATE TABLE orderplaced (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES customer(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES product(id) ON DELETE CASCADE,
    quantity SMALLINT DEFAULT 1,
    ordered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Pending'
);
