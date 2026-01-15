#!/bin/bash
# Install and configure PostgreSQL and Redis as local services

echo "🔧 Installing PostgreSQL and Redis..."

# Update package list
apt-get update

# Install PostgreSQL
apt-get install -y postgresql postgresql-contrib

# Install Redis
apt-get install -y redis-server

echo "✅ PostgreSQL and Redis installed"

# Start PostgreSQL service
service postgresql start

# Configure PostgreSQL
echo "📦 Configuring PostgreSQL..."
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
sudo -u postgres psql -c "CREATE DATABASE trueshift;"

# Start Redis service
service redis-server start

echo "✅ PostgreSQL configured with:"
echo "   - Database: trueshift"
echo "   - User: postgres"
echo "   - Password: postgres"
echo "   - Port: 5432"
echo ""
echo "✅ Redis configured on port 6379"

# Verify services are running
echo ""
echo "🔍 Verifying services..."
service postgresql status
service redis-server status

echo ""
echo "✅ Setup complete! Services are ready."
echo ""
echo "Connection URLs:"
echo "  PostgreSQL: postgresql+asyncpg://postgres:postgres@localhost:5432/trueshift"
echo "  Redis: redis://localhost:6379/0"
