-- Create user for migration admin
CREATE USER migration_admin WITH PASSWORD= '<Password>'
GO

-- Grant migration admin full permissions (for schema changes)
ALTER ROLE db_owner ADD MEMBER migration_admin;
GO

-- Create user for application
CREATE USER app_user WITH PASSWORD= '<Password>'
GO

-- Grant application user limited permissions
ALTER ROLE db_datareader ADD MEMBER app_user;
ALTER ROLE db_datawriter ADD MEMBER app_user;
GO

-- Grant specific permissions application needs
GRANT EXECUTE TO app_user;  -- For stored procedures if needed
GRANT VIEW DEFINITION TO app_user;  -- To view schema
GO