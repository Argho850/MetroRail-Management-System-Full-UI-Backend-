CREATE DATABASE metro_rail;
USE metro_rail;

CREATE TABLE admins (
   id INT AUTO_INCREMENT PRIMARY KEY,
   username VARCHAR(50) UNIQUE NOT NULL,
   password VARCHAR(255) NOT NULL
);

CREATE TABLE users (
   id INT AUTO_INCREMENT PRIMARY KEY,
   username VARCHAR(50) UNIQUE NOT NULL,
   password VARCHAR(255) NOT NULL,
   email VARCHAR(100) UNIQUE NOT NULL,
   balance DECIMAL(10, 2) DEFAULT 0.0
);

CREATE TABLE trains (
   id INT AUTO_INCREMENT PRIMARY KEY,
   train_number VARCHAR(20) UNIQUE NOT NULL,
   train_name VARCHAR(100) NOT NULL,
   source VARCHAR(100) NOT NULL,
   destination VARCHAR(100) NOT NULL,
   departure_time DATETIME NOT NULL,
   fare DECIMAL(10, 2) NOT NULL
);

CREATE TABLE tickets (
   id INT AUTO_INCREMENT PRIMARY KEY,
   user_id INT NOT NULL,
   train_id INT NOT NULL,
   ticket_number VARCHAR(36) UNIQUE NOT NULL,
   purchase_date DATETIME NOT NULL,
   FOREIGN KEY (user_id) REFERENCES users(id),
   FOREIGN KEY (train_id) REFERENCES trains(id)
);

CREATE TABLE feedback (
   id INT AUTO_INCREMENT PRIMARY KEY,
   user_id INT NOT NULL,
   feedback TEXT NOT NULL,
   submitted_at DATETIME NOT NULL,
   FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT INTO admins (username, password) VALUES ('admin', 'admin123');