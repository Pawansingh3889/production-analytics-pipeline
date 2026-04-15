-- ============================================================
-- Sandbox initialisation: create database, read-only user, schema
-- Run against the Docker SQL Server container
-- ============================================================

-- Create the database
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'production_dw')
    CREATE DATABASE production_dw;
GO

USE production_dw;
GO

-- Create read-only user (pipeline connects as this user)
IF NOT EXISTS (SELECT name FROM sys.server_principals WHERE name = 'pipeline_reader')
    CREATE LOGIN pipeline_reader WITH PASSWORD = 'ReadOnly123!';
GO

IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = 'pipeline_reader')
    CREATE USER pipeline_reader FOR LOGIN pipeline_reader;
GO

-- ONLY read permissions — no write, no DDL, no execute
ALTER ROLE db_datareader ADD MEMBER pipeline_reader;
GO

-- Deny all write operations explicitly
DENY INSERT, UPDATE, DELETE, ALTER, CREATE TABLE, DROP TABLE TO pipeline_reader;
GO

PRINT 'Sandbox initialised: production_dw database with read-only pipeline_reader user';
GO
