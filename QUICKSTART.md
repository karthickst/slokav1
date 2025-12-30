# Quick Start Guide

## 1. Setup (First Time Only)

```bash
# Make setup script executable and run it
chmod +x setup.sh
./setup.sh
```

This will:
- Create virtual environment
- Install dependencies
- Create .env file
- Optionally create test database

## 2. Run the Application

```bash
# Make run script executable
chmod +x run.sh

# Run the application
./run.sh
```

Or manually:
```bash
source venv/bin/activate
python app.py
```

Access at: http://localhost:8000

### Stop the Application

```bash
# Make stop script executable
chmod +x stop.sh

# Stop the application
./stop.sh
```

This will:
- Find and stop all running app processes
- Free up port 8000
- Gracefully shutdown the server

## 3. Run Tests

```bash
# Make test script executable
chmod +x run_tests.sh

# Run tests
./run_tests.sh
```

Or manually:
```bash
source venv/bin/activate
pytest test_app.py -v
```

## 4. Default Credentials

**Admin Login:**
- Username: `admin`
- Password: `admin123`

**Student:** Sign up via the UI

## 5. Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

Don't forget to set environment variables in Vercel dashboard:
- `POSTGRES_URL` - Your Vercel Postgres URL
- `JWT_SECRET` - A secure random string
- `APP_MODE` - Set to `prod`

## API Endpoints

- Health: `GET /api/health`
- Student Signup: `POST /api/students/signup`
- Student Login: `POST /api/students/login`
- Admin Login: `POST /api/admin/login`
- All Courses: `GET /api/courses`
- Create Course: `POST /api/courses` (admin)
- API Docs: http://localhost:8000/api/docs

## Project Structure

```
slokav1/
├── app.py           # Main FastAPI app
├── db.py            # Database layer
├── auth.py          # Authentication
├── config.py        # Configuration
├── index.html       # Frontend
├── test_app.py      # Tests
├── setup.sh         # Setup script
├── run.sh           # Run script
├── stop.sh          # Stop script
└── run_tests.sh     # Test script
```

## Troubleshooting

**Database connection error?**
- Make sure PostgreSQL is running
- Check .env has correct TEST_DATABASE_URL
- Create database: `createdb course_management_test`

**Port 8000 in use?**
- Use stop script: `./stop.sh`
- Or manually: `lsof -ti:8000 | xargs kill -9`
- Or change port in app.py

**Module not found?**
- Activate venv: `source venv/bin/activate`
- Install deps: `pip install -r requirements.txt`

## Need More Help?

See README.md for detailed documentation.
