-- 1. Create the database if it does not already exist
CREATE DATABASE IF NOT EXISTS employee_reward;

-- 2. Use the database
USE employee_reward;

-- 3. Create the user table with necessary columns and constraints
CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL UNIQUE,
    picture VARCHAR(255),
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email_id VARCHAR(100) NOT NULL UNIQUE,
    department VARCHAR(50) NOT NULL,
    manager ENUM('yes', 'no') NOT NULL,
    manager_points INT DEFAULT 0,
    available_points INT DEFAULT 0,
    received_points INT DEFAULT 0,
    is_admin BOOLEAN NOT NULL
);

-- 4. Create the transaction table with foreign key constraints referencing the user table
-- We allow sender_email and receiver_email to be NULL to avoid constraint errors
-- on deletion when users are removed, setting the emails to NULL in the transactions.
CREATE TABLE IF NOT EXISTS transaction (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_email VARCHAR(100),
    receiver_email VARCHAR(100),
    points_send INT NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    comment TEXT,
    FOREIGN KEY (sender_email) REFERENCES user(email_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (receiver_email) REFERENCES user(email_id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- 5. Create the redeem table with foreign key constraints referencing the user table
-- Allow email_id to be NULL in case the related user is deleted, while setting
-- email_id to NULL rather than breaking the foreign key constraint.
CREATE TABLE IF NOT EXISTS redeem (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email_id VARCHAR(100),
    redeem_points INT NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES user(username) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (email_id) REFERENCES user(email_id) ON DELETE CASCADE, ON UPDATE CASCADE
);
