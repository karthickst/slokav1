#!/bin/bash
# Setup script for Spiritual Course Management System

echo "🕉️  Spiritual Course Management - Setup Script"
echo "=============================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL not found. You'll need PostgreSQL for local testing."
    echo "   Install from: https://www.postgresql.org/download/"
else
    echo "✓ PostgreSQL found: $(psql --version)"
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created. Please update it with your settings."
else
    echo ""
    echo "✓ .env file already exists."
fi

# Create test database if PostgreSQL is available
if command -v psql &> /dev/null; then
    echo ""
    read -p "Create test database 'course_management_test'? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        createdb course_management_test 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✓ Test database created successfully."
        else
            echo "⚠️  Database might already exist or there was an error."
        fi
    fi
fi

echo ""
echo "=============================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Update .env file with your database settings (if needed)"
echo ""
echo "3. Run the application:"
echo "   ./run.sh"
echo "   or"
echo "   python app.py"
echo ""
echo "4. Run tests:"
echo "   pytest test_app.py -v"
echo ""
echo "🕉️  May your coding journey be enlightening!"
echo "=============================================="
