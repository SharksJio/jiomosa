-- Guacamole database initialization script
-- Downloads and installs the official Guacamole PostgreSQL schema

-- Download and install the main schema
\! curl -s https://raw.githubusercontent.com/apache/guacamole-client/master/extensions/guacamole-auth-jdbc/modules/guacamole-auth-jdbc-postgresql/schema/001-create-schema.sql | psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

-- Download and install the default admin user
\! curl -s https://raw.githubusercontent.com/apache/guacamole-client/master/extensions/guacamole-auth-jdbc/modules/guacamole-auth-jdbc-postgresql/schema/002-create-admin-user.sql | psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

-- Note: Default login credentials are username: guacadmin, password: guacadmin
-- Change these immediately after first login for security
