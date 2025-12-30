# 🕉️ Spiritual Course Management System

A beautiful, spiritual-themed course management application built with FastAPI and jQuery, designed for simplicity and elegance.

## Overview

This application allows administrators to create and manage courses while students can sign up and view their enrolled courses. The application features a calming spiritual aesthetic with purple gradients and smooth interactions.

## Features

### Student Features
- Sign up with email and password
- Login to view enrolled courses
- View all courses they're enrolled in
- Beautiful, responsive UI with spiritual theme

### Admin Features
- Login with admin credentials
- Create, edit, and delete courses
- View all registered students
- Assign courses to students
- Remove students from courses
- View all students enrolled in a specific course

## Technology Stack

- **Backend**: Python 3.11, FastAPI
- **Frontend**: HTML5, jQuery 3.7.1
- **Database**: PostgreSQL (Vercel Postgres for production)
- **Authentication**: JWT tokens with bcrypt password hashing
- **Deployment**: Vercel

## Project Structure

```
slokav1/
├── app.py              # Main FastAPI application
├── db.py               # Database management with logging
├── auth.py             # Authentication management
├── config.py           # Configuration for prod/test modes
├── index.html          # Single-page frontend
├── test_app.py         # Comprehensive test suite
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel deployment configuration
├── runtime.txt         # Python runtime version
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore file
└── README.md           # This file
```

## Environment Modes

The application supports two modes:

### Production Mode (`/prod`)
- Uses Vercel Postgres database
- Requires `POSTGRES_URL` environment variable
- Stricter CORS settings
- INFO level logging

### Test Mode (`/test`)
- Uses local PostgreSQL database
- Relaxed CORS settings
- DEBUG level logging
- Default mode for local development

Set mode via `APP_MODE` environment variable:
```bash
export APP_MODE=prod  # or test
```

## Installation & Setup

### Prerequisites
- Python 3.11 or higher
- PostgreSQL (for local testing)
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   cd slokav1
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup local database**
   ```bash
   # Create PostgreSQL database
   createdb course_management_test
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and set TEST_DATABASE_URL if needed
   ```

6. **Run the application**
   ```bash
   # Test mode (default)
   python app.py

   # Or use uvicorn directly
   uvicorn app:app --reload --port 8000
   ```

7. **Access the application**
   - Open browser: http://localhost:8000
   - API docs: http://localhost:8000/api/docs

### Default Credentials

**Admin Login:**
- Username: `admin`
- Password: `admin123`

## Running Tests

The project includes comprehensive test coverage for all endpoints and functionality.

```bash
# Run all tests
pytest test_app.py -v

# Run with detailed output
pytest test_app.py -v -s

# Run specific test class
pytest test_app.py::TestStudentAuth -v
```

### Test Coverage

- ✅ Health check endpoint
- ✅ Student signup (success, duplicate email, invalid email, weak password)
- ✅ Student login (success, wrong password, non-existent user)
- ✅ Admin login (success, wrong password)
- ✅ Course management (create, read, update, delete)
- ✅ Authorization checks (admin-only endpoints)
- ✅ Student enrollment management
- ✅ JWT token creation and verification
- ✅ Password hashing and verification
- ✅ Email and password validation

## Vercel Deployment

### Prerequisites
- Vercel account
- Vercel CLI installed: `npm install -g vercel`
- Vercel Postgres database created

### Deployment Steps

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Create Vercel Postgres Database**
   - Go to Vercel dashboard
   - Create new Postgres database
   - Copy the `POSTGRES_URL` connection string

3. **Configure environment variables**
   In Vercel project settings, add:
   ```
   POSTGRES_URL=<your-vercel-postgres-url>
   JWT_SECRET=<generate-a-secure-random-string>
   APP_MODE=prod
   CORS_ORIGINS=https://yourdomain.vercel.app
   LOG_LEVEL=INFO
   ```

4. **Deploy**
   ```bash
   vercel
   ```

5. **Deploy to production**
   ```bash
   vercel --prod
   ```

### Post-Deployment

The database schema will be automatically initialized on the first startup, and a default admin user will be created.

## API Endpoints

### Authentication

#### Student Signup
```
POST /api/students/signup
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "password123",
  "name": "Student Name"  // optional
}
```

#### Student Login
```
POST /api/students/login
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "password123"
}
```

#### Admin Login
```
POST /api/admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

### Courses

#### Get All Courses (Public)
```
GET /api/courses
```

#### Create Course (Admin Only)
```
POST /api/courses
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "title": "Course Title",
  "description": "Course description"
}
```

#### Update Course (Admin Only)
```
PUT /api/courses/{course_id}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "title": "Updated Title",
  "description": "Updated description"
}
```

#### Delete Course (Admin Only)
```
DELETE /api/courses/{course_id}
Authorization: Bearer <admin-token>
```

### Students

#### Get All Students (Admin Only)
```
GET /api/students
Authorization: Bearer <admin-token>
```

### Enrollments

#### Enroll Student (Admin Only)
```
POST /api/enrollments
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "student_id": 1,
  "course_id": 1
}
```

#### Unenroll Student (Admin Only)
```
DELETE /api/enrollments/{student_id}/{course_id}
Authorization: Bearer <admin-token>
```

#### Get Student's Courses
```
GET /api/students/{student_id}/courses
Authorization: Bearer <student-or-admin-token>
```

#### Get Course's Students (Admin Only)
```
GET /api/courses/{course_id}/students
Authorization: Bearer <admin-token>
```

### Health Check
```
GET /api/health
```

## Logging

The application features extensive logging at all levels:

### What is Logged

1. **Database Operations**
   - All SQL statements executed
   - Query parameters
   - Number of rows affected/returned
   - Connection status

2. **Authentication**
   - Login attempts (success/failure)
   - Token creation and verification
   - Password validation

3. **API Requests**
   - All endpoint accesses
   - Authorization checks
   - Request validation

4. **Errors**
   - Full stack traces
   - Failed SQL queries with parameters
   - Authentication failures
   - Validation errors

### Log Levels

- **DEBUG**: All SQL statements, detailed operation info
- **INFO**: Important operations, successful authentications
- **WARNING**: Invalid tokens, authorization failures
- **ERROR**: Exceptions, failed operations with stack traces

### Viewing Logs

**Local Development:**
```bash
# Logs appear in console when running the app
python app.py
```

**Vercel:**
```bash
# View logs via CLI
vercel logs

# Or check the Vercel dashboard
```

## Database Schema

### Students Table
```sql
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Admins Table
```sql
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Courses Table
```sql
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_by INTEGER REFERENCES admins(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Enrollments Table
```sql
CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, course_id)
);
```

## Security Features

1. **Password Hashing**: Bcrypt with salt
2. **JWT Authentication**: Secure token-based auth
3. **SQL Injection Protection**: Parameterized queries
4. **CORS Configuration**: Configurable per environment
5. **Authorization Checks**: Role-based access control
6. **Input Validation**: Pydantic models with email validation
7. **Password Strength**: Minimum 6 characters required

## Configuration Options

All configuration is managed in `config.py`:

### Environment Variables

- `APP_MODE`: `prod` or `test` (default: `test`)
- `POSTGRES_URL`: Production database URL (required in prod mode)
- `TEST_DATABASE_URL`: Test database URL (optional, has default)
- `JWT_SECRET`: Secret key for JWT tokens (required in prod)
- `JWT_ALGORITHM`: Algorithm for JWT (default: `HS256`)
- `CORS_ORIGINS`: Comma-separated allowed origins (prod only)
- `LOG_LEVEL`: Logging level (default: `DEBUG` for test, `INFO` for prod)

## Troubleshooting

### Database Connection Issues

**Error**: "Database connection failed"

**Solution**:
1. Ensure PostgreSQL is running
2. Check database URL in .env
3. Verify database exists: `psql -l`
4. Check credentials and permissions

### Import Errors

**Error**: "ModuleNotFoundError"

**Solution**:
```bash
pip install -r requirements.txt
```

### Port Already in Use

**Error**: "Address already in use"

**Solution**:
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn app:app --port 8001
```

### Vercel Deployment Issues

**Error**: "Build failed"

**Solution**:
1. Check `vercel.json` configuration
2. Verify all environment variables are set
3. Check logs: `vercel logs`
4. Ensure Python version in `runtime.txt` is supported

### Test Database Issues

**Error**: Tests failing due to database

**Solution**:
```bash
# Drop and recreate test database
dropdb course_management_test
createdb course_management_test

# Run tests again
pytest test_app.py -v
```

## Future Enhancements

Potential improvements for future versions:

- [ ] Course categories and tags
- [ ] Student progress tracking
- [ ] Course materials upload
- [ ] Email verification for students
- [ ] Password reset functionality
- [ ] Course search and filtering
- [ ] Student profiles with avatars
- [ ] Course ratings and reviews
- [ ] Notifications system
- [ ] Admin analytics dashboard
- [ ] Export student/course data to CSV
- [ ] Multi-admin support with permissions
- [ ] Course prerequisites
- [ ] Completion certificates

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check this README
2. Review the code comments
3. Check application logs
4. Run the test suite to identify issues

## Contributing

This is a simple educational project. Feel free to fork and modify as needed.

## Acknowledgments

- Built with FastAPI - https://fastapi.tiangolo.com/
- Styled with spiritual themes for peaceful learning
- Deployed on Vercel - https://vercel.com/

---

**Made with 🕉️ for spiritual learning and growth**
