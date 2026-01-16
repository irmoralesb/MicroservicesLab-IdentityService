-- Create a new database
CREATE DATABASE [db_name];
GO

USE [db_name];
GO

-- Create a SQL Server login
CREATE LOGIN [db_login] WITH PASSWORD = '<password>';
GO

-- Create user from login
CREATE USER [db_user] FOR LOGIN [db_login];
GO

-- Grant read/write permissions with CORRECT role names
ALTER ROLE db_datareader ADD MEMBER [db_user];
ALTER ROLE db_datawriter ADD MEMBER [db_user];
