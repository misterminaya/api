-- Vailoo Database Initialization
-- This script runs when MySQL container is first created

-- Set character set
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Create database if not exists (handled by docker-compose, but just in case)
CREATE DATABASE IF NOT EXISTS vailoo
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE vailoo;

-- Grant privileges to application user
GRANT ALL PRIVILEGES ON vailoo.* TO 'vailoo'@'%';
FLUSH PRIVILEGES;

-- Note: Tables are created automatically by the application on startup
-- This file is for any additional database initialization needed
