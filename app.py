import logging
import traceback
import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from config import Config
from db import Database
from auth import AuthManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Determine mode from environment variable
MODE = os.getenv("APP_MODE", "test")
config = Config(mode=MODE)
logger.info(f"Starting application in {MODE} mode")
logger.info(f"Configuration: {config}")

# Initialize FastAPI app
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = Database(config)
auth_manager = AuthManager(config)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database schema and seed admin on startup"""
    try:
        logger.info("Application startup: Initializing database")
        db.connect()
        db.initialize_schema()

        # Seed default admin (username: admin, password: admin123)
        admin_password_hash = auth_manager.hash_password("admin123")
        db.seed_admin("admin", admin_password_hash)

        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    try:
        logger.info("Application shutdown: Closing database connection")
        db.disconnect()
    except Exception as e:
        logger.error(f"Application shutdown error: {str(e)}")
        logger.error(traceback.format_exc())


# Pydantic Models
class StudentSignup(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class StudentLogin(BaseModel):
    email: EmailStr
    password: str

class AdminLogin(BaseModel):
    username: str
    password: str

class CourseCreate(BaseModel):
    title: str
    description: str

class CourseUpdate(BaseModel):
    title: str
    description: str

class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int


# Dependency for authentication
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Verify JWT token and return current user"""
    try:
        if not authorization:
            logger.warning("No authorization header provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required"
            )

        # Extract token from "Bearer <token>"
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning(f"Invalid authorization header format: {authorization}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )

        token = parts[1]
        payload = auth_manager.verify_token(token)

        if not payload:
            logger.warning("Invalid or expired token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        logger.debug(f"Authenticated user: {payload}")
        return payload

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


# Root endpoint - serve the frontend
@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    try:
        logger.info("Serving root page")
        return FileResponse("index.html")
    except Exception as e:
        logger.error(f"Error serving root page: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        logger.debug("Health check requested")
        return {
            "status": "healthy",
            "mode": MODE,
            "version": config.app_version
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )


# Student Authentication Endpoints
@app.post("/api/students/signup")
async def student_signup(student: StudentSignup):
    """Student signup endpoint"""
    try:
        logger.info(f"Student signup request: {student.email}")

        # Validate email
        if not auth_manager.validate_email(student.email):
            raise HTTPException(status_code=400, detail="Invalid email format")

        # Validate password
        is_valid, error_msg = auth_manager.validate_password(student.password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Check if student already exists
        existing_student = db.get_student_by_email(student.email)
        if existing_student:
            logger.warning(f"Student already exists: {student.email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash password and create student
        password_hash = auth_manager.hash_password(student.password)
        new_student = db.create_student(student.email, password_hash, student.name)

        # Create access token
        token = auth_manager.create_access_token(
            data={"sub": str(new_student["id"]), "email": new_student["email"]},
            user_type="student"
        )

        logger.info(f"Student created successfully: {new_student['id']}")
        return {
            "message": "Student created successfully",
            "student": {
                "id": new_student["id"],
                "email": new_student["email"],
                "name": new_student["name"]
            },
            "token": token
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Student signup failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Signup failed")


@app.post("/api/students/login")
async def student_login(credentials: StudentLogin):
    """Student login endpoint"""
    try:
        logger.info(f"Student login request: {credentials.email}")

        # Get student from database
        student = db.get_student_by_email(credentials.email)
        if not student:
            logger.warning(f"Student not found: {credentials.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Verify password
        if not auth_manager.verify_password(credentials.password, student["password_hash"]):
            logger.warning(f"Invalid password for student: {credentials.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create access token
        token = auth_manager.create_access_token(
            data={"sub": str(student["id"]), "email": student["email"]},
            user_type="student"
        )

        logger.info(f"Student logged in successfully: {student['id']}")
        return {
            "message": "Login successful",
            "student": {
                "id": student["id"],
                "email": student["email"],
                "name": student["name"]
            },
            "token": token
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Student login failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Login failed")


# Admin Authentication Endpoints
@app.post("/api/admin/login")
async def admin_login(credentials: AdminLogin):
    """Admin login endpoint"""
    try:
        logger.info(f"Admin login request: {credentials.username}")

        # Get admin from database
        admin = db.get_admin_by_username(credentials.username)
        if not admin:
            logger.warning(f"Admin not found: {credentials.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Verify password
        if not auth_manager.verify_password(credentials.password, admin["password_hash"]):
            logger.warning(f"Invalid password for admin: {credentials.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create access token
        token = auth_manager.create_access_token(
            data={"sub": str(admin["id"]), "username": admin["username"]},
            user_type="admin"
        )

        logger.info(f"Admin logged in successfully: {admin['id']}")
        return {
            "message": "Login successful",
            "admin": {
                "id": admin["id"],
                "username": admin["username"]
            },
            "token": token
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin login failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Login failed")


# Course Endpoints (Admin only)
@app.get("/api/courses")
async def get_courses():
    """Get all courses (public endpoint)"""
    try:
        logger.info("Fetching all courses")
        courses = db.get_all_courses()
        return {"courses": courses}
    except Exception as e:
        logger.error(f"Failed to fetch courses: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to fetch courses")


@app.post("/api/courses")
async def create_course(course: CourseCreate, current_user: dict = Depends(get_current_user)):
    """Create a new course (admin only)"""
    try:
        # Verify admin role
        if current_user.get("type") != "admin":
            logger.warning(f"Unauthorized course creation attempt by user type: {current_user.get('type')}")
            raise HTTPException(status_code=403, detail="Admin access required")

        logger.info(f"Creating course: {course.title}")

        new_course = db.create_course(
            course.title,
            course.description,
            int(current_user["sub"])
        )

        logger.info(f"Course created successfully: {new_course['id']}")
        return {
            "message": "Course created successfully",
            "course": new_course
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Course creation failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to create course")


@app.put("/api/courses/{course_id}")
async def update_course(
    course_id: int,
    course: CourseUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a course (admin only)"""
    try:
        # Verify admin role
        if current_user.get("type") != "admin":
            logger.warning(f"Unauthorized course update attempt by user type: {current_user.get('type')}")
            raise HTTPException(status_code=403, detail="Admin access required")

        logger.info(f"Updating course: {course_id}")

        # Check if course exists
        existing_course = db.get_course_by_id(course_id)
        if not existing_course:
            raise HTTPException(status_code=404, detail="Course not found")

        updated_course = db.update_course(course_id, course.title, course.description)

        logger.info(f"Course updated successfully: {course_id}")
        return {
            "message": "Course updated successfully",
            "course": updated_course
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Course update failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to update course")


@app.delete("/api/courses/{course_id}")
async def delete_course(course_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a course (admin only)"""
    try:
        # Verify admin role
        if current_user.get("type") != "admin":
            logger.warning(f"Unauthorized course deletion attempt by user type: {current_user.get('type')}")
            raise HTTPException(status_code=403, detail="Admin access required")

        logger.info(f"Deleting course: {course_id}")

        # Check if course exists
        existing_course = db.get_course_by_id(course_id)
        if not existing_course:
            raise HTTPException(status_code=404, detail="Course not found")

        db.delete_course(course_id)

        logger.info(f"Course deleted successfully: {course_id}")
        return {"message": "Course deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Course deletion failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to delete course")


# Student Endpoints
@app.get("/api/students")
async def get_students(current_user: dict = Depends(get_current_user)):
    """Get all students (admin only)"""
    try:
        # Verify admin role
        if current_user.get("type") != "admin":
            logger.warning(f"Unauthorized students fetch attempt by user type: {current_user.get('type')}")
            raise HTTPException(status_code=403, detail="Admin access required")

        logger.info("Fetching all students")
        students = db.get_all_students()
        return {"students": students}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch students: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to fetch students")


# Enrollment Endpoints
@app.post("/api/enrollments")
async def enroll_student(enrollment: EnrollmentCreate, current_user: dict = Depends(get_current_user)):
    """Enroll a student in a course (admin only)"""
    try:
        # Verify admin role
        if current_user.get("type") != "admin":
            logger.warning(f"Unauthorized enrollment attempt by user type: {current_user.get('type')}")
            raise HTTPException(status_code=403, detail="Admin access required")

        logger.info(f"Enrolling student {enrollment.student_id} in course {enrollment.course_id}")

        # Verify course exists
        course = db.get_course_by_id(enrollment.course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        new_enrollment = db.enroll_student(enrollment.student_id, enrollment.course_id)

        if not new_enrollment:
            logger.info("Student already enrolled in this course")
            return {"message": "Student already enrolled in this course"}

        logger.info(f"Enrollment successful: {new_enrollment['id']}")
        return {
            "message": "Student enrolled successfully",
            "enrollment": new_enrollment
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enrollment failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to enroll student")


@app.delete("/api/enrollments/{student_id}/{course_id}")
async def unenroll_student(
    student_id: int,
    course_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Unenroll a student from a course (admin only)"""
    try:
        # Verify admin role
        if current_user.get("type") != "admin":
            logger.warning(f"Unauthorized unenrollment attempt by user type: {current_user.get('type')}")
            raise HTTPException(status_code=403, detail="Admin access required")

        logger.info(f"Unenrolling student {student_id} from course {course_id}")

        db.unenroll_student(student_id, course_id)

        logger.info("Unenrollment successful")
        return {"message": "Student unenrolled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unenrollment failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to unenroll student")


@app.get("/api/students/{student_id}/courses")
async def get_student_courses(student_id: int, current_user: dict = Depends(get_current_user)):
    """Get all courses for a student"""
    try:
        # Students can only view their own courses, admins can view any
        if current_user.get("type") == "student" and int(current_user["sub"]) != student_id:
            logger.warning(f"Unauthorized access attempt to student {student_id} courses")
            raise HTTPException(status_code=403, detail="Access denied")

        logger.info(f"Fetching courses for student {student_id}")
        courses = db.get_student_courses(student_id)
        return {"courses": courses}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch student courses: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to fetch student courses")


@app.get("/api/courses/{course_id}/students")
async def get_course_students(course_id: int, current_user: dict = Depends(get_current_user)):
    """Get all students enrolled in a course (admin only)"""
    try:
        # Verify admin role
        if current_user.get("type") != "admin":
            logger.warning(f"Unauthorized course students fetch by user type: {current_user.get('type')}")
            raise HTTPException(status_code=403, detail="Admin access required")

        logger.info(f"Fetching students for course {course_id}")
        students = db.get_course_students(course_id)
        return {"students": students}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch course students: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to fetch course students")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
