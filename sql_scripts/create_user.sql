-- Remove default permission
REVOKE ALL ON DATABASE athlon FROM PUBLIC;

-- Create reader role
CREATE ROLE reader;

-- Allow connect
GRANT CONNECT ON DATABASE athlon TO reader;
GRANT USAGE ON SCHEMA public TO reader;
-- Set perms and default perms for future items
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO reader;

-- Create user and give role
CREATE USER {user} WITH PASSWORD '{password}';
GRANT reader TO {user}