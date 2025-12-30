import logging
import traceback
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Database:
    """Database management with extensive logging and error handling"""

    def __init__(self, config: Config):
        self.config = config
        self.connection = None
        logger.info(f"Initializing Database with config: {config}")

    def connect(self):
        """Establish database connection"""
        try:
            logger.info(f"Connecting to database: {self.config.database_url[:20]}...")
            self.connection = psycopg2.connect(
                self.config.database_url,
                cursor_factory=RealDictCursor
            )
            self.connection.autocommit = False
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {str(e)}")
                logger.error(traceback.format_exc())

    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[List[Dict]]:
        """Execute a SQL query with logging"""
        cursor = None
        try:
            if not self.connection:
                self.connect()

            cursor = self.connection.cursor()

            # Log the SQL statement
            logger.debug(f"Executing SQL: {query}")
            if params:
                logger.debug(f"Parameters: {params}")

            cursor.execute(query, params)

            result = None
            if fetch:
                result = cursor.fetchall()
                logger.debug(f"Query returned {len(result) if result else 0} rows")
            else:
                self.connection.commit()
                logger.debug(f"Query executed successfully, {cursor.rowcount} rows affected")

            return result

        except Exception as e:
            self.connection.rollback()
            logger.error(f"Query execution failed: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {params}")
            logger.error(traceback.format_exc())
            raise
        finally:
            if cursor:
                cursor.close()

    def initialize_schema(self):
        """Create database tables if they don't exist"""
        logger.info("Initializing database schema")

        # Students table
        students_table = """
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        logger.info("Creating students table")
        self.execute_query(students_table, fetch=False)

        # Admin users table (for future use, seeded with default admin)
        admins_table = """
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        logger.info("Creating admins table")
        self.execute_query(admins_table, fetch=False)

        # Courses table
        courses_table = """
        CREATE TABLE IF NOT EXISTS courses (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            created_by INTEGER REFERENCES admins(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        logger.info("Creating courses table")
        self.execute_query(courses_table, fetch=False)

        # Student-Course assignments table
        enrollments_table = """
        CREATE TABLE IF NOT EXISTS enrollments (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, course_id)
        )
        """
        logger.info("Creating enrollments table")
        self.execute_query(enrollments_table, fetch=False)

        logger.info("Database schema initialization completed")

    def seed_admin(self, username: str, password_hash: str):
        """Create default admin if not exists"""
        try:
            logger.info(f"Seeding admin user: {username}")
            query = """
            INSERT INTO admins (username, password_hash)
            VALUES (%s, %s)
            ON CONFLICT (username) DO NOTHING
            """
            self.execute_query(query, (username, password_hash), fetch=False)
            logger.info("Admin user seeded successfully")
        except Exception as e:
            logger.error(f"Failed to seed admin: {str(e)}")
            logger.error(traceback.format_exc())

    # Student operations
    def create_student(self, email: str, password_hash: str, name: str = None) -> Optional[Dict]:
        """Create a new student"""
        try:
            logger.info(f"Creating student with email: {email}")
            query = """
            INSERT INTO students (email, password_hash, name)
            VALUES (%s, %s, %s)
            RETURNING id, email, name, created_at
            """
            result = self.execute_query(query, (email, password_hash, name))
            logger.info(f"Student created successfully: {result[0] if result else None}")
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to create student: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def get_student_by_email(self, email: str) -> Optional[Dict]:
        """Get student by email"""
        try:
            logger.info(f"Fetching student by email: {email}")
            query = "SELECT * FROM students WHERE email = %s"
            result = self.execute_query(query, (email,))
            logger.info(f"Student found: {result[0]['id'] if result else 'Not found'}")
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to fetch student: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def get_all_students(self) -> List[Dict]:
        """Get all students"""
        try:
            logger.info("Fetching all students")
            query = "SELECT id, email, name, created_at FROM students ORDER BY created_at DESC"
            result = self.execute_query(query)
            logger.info(f"Fetched {len(result) if result else 0} students")
            return result or []
        except Exception as e:
            logger.error(f"Failed to fetch students: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    # Course operations
    def create_course(self, title: str, description: str, created_by: int) -> Optional[Dict]:
        """Create a new course"""
        try:
            logger.info(f"Creating course: {title}")
            query = """
            INSERT INTO courses (title, description, created_by)
            VALUES (%s, %s, %s)
            RETURNING id, title, description, created_at
            """
            result = self.execute_query(query, (title, description, created_by))
            logger.info(f"Course created successfully: {result[0] if result else None}")
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to create course: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def update_course(self, course_id: int, title: str, description: str) -> Optional[Dict]:
        """Update an existing course"""
        try:
            logger.info(f"Updating course ID: {course_id}")
            query = """
            UPDATE courses
            SET title = %s, description = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, title, description, updated_at
            """
            result = self.execute_query(query, (title, description, course_id))
            logger.info(f"Course updated successfully: {result[0] if result else None}")
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to update course: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def delete_course(self, course_id: int) -> bool:
        """Delete a course"""
        try:
            logger.info(f"Deleting course ID: {course_id}")
            query = "DELETE FROM courses WHERE id = %s"
            self.execute_query(query, (course_id,), fetch=False)
            logger.info(f"Course deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete course: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def get_all_courses(self) -> List[Dict]:
        """Get all courses"""
        try:
            logger.info("Fetching all courses")
            query = "SELECT id, title, description, created_at, updated_at FROM courses ORDER BY created_at DESC"
            result = self.execute_query(query)
            logger.info(f"Fetched {len(result) if result else 0} courses")
            return result or []
        except Exception as e:
            logger.error(f"Failed to fetch courses: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def get_course_by_id(self, course_id: int) -> Optional[Dict]:
        """Get course by ID"""
        try:
            logger.info(f"Fetching course ID: {course_id}")
            query = "SELECT * FROM courses WHERE id = %s"
            result = self.execute_query(query, (course_id,))
            logger.info(f"Course found: {result[0] if result else 'Not found'}")
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to fetch course: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    # Enrollment operations
    def enroll_student(self, student_id: int, course_id: int) -> Optional[Dict]:
        """Enroll a student in a course"""
        try:
            logger.info(f"Enrolling student {student_id} in course {course_id}")
            query = """
            INSERT INTO enrollments (student_id, course_id)
            VALUES (%s, %s)
            ON CONFLICT (student_id, course_id) DO NOTHING
            RETURNING id, student_id, course_id, enrolled_at
            """
            result = self.execute_query(query, (student_id, course_id))
            logger.info(f"Enrollment successful: {result[0] if result else 'Already enrolled'}")
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to enroll student: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def unenroll_student(self, student_id: int, course_id: int) -> bool:
        """Unenroll a student from a course"""
        try:
            logger.info(f"Unenrolling student {student_id} from course {course_id}")
            query = "DELETE FROM enrollments WHERE student_id = %s AND course_id = %s"
            self.execute_query(query, (student_id, course_id), fetch=False)
            logger.info("Unenrollment successful")
            return True
        except Exception as e:
            logger.error(f"Failed to unenroll student: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def get_student_courses(self, student_id: int) -> List[Dict]:
        """Get all courses for a student"""
        try:
            logger.info(f"Fetching courses for student {student_id}")
            query = """
            SELECT c.id, c.title, c.description, e.enrolled_at
            FROM courses c
            INNER JOIN enrollments e ON c.id = e.course_id
            WHERE e.student_id = %s
            ORDER BY e.enrolled_at DESC
            """
            result = self.execute_query(query, (student_id,))
            logger.info(f"Fetched {len(result) if result else 0} courses for student")
            return result or []
        except Exception as e:
            logger.error(f"Failed to fetch student courses: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def get_course_students(self, course_id: int) -> List[Dict]:
        """Get all students enrolled in a course"""
        try:
            logger.info(f"Fetching students for course {course_id}")
            query = """
            SELECT s.id, s.email, s.name, e.enrolled_at
            FROM students s
            INNER JOIN enrollments e ON s.id = e.student_id
            WHERE e.course_id = %s
            ORDER BY e.enrolled_at DESC
            """
            result = self.execute_query(query, (course_id,))
            logger.info(f"Fetched {len(result) if result else 0} students for course")
            return result or []
        except Exception as e:
            logger.error(f"Failed to fetch course students: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    # Admin operations
    def get_admin_by_username(self, username: str) -> Optional[Dict]:
        """Get admin by username"""
        try:
            logger.info(f"Fetching admin by username: {username}")
            query = "SELECT * FROM admins WHERE username = %s"
            result = self.execute_query(query, (username,))
            logger.info(f"Admin found: {result[0]['id'] if result else 'Not found'}")
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to fetch admin: {str(e)}")
            logger.error(traceback.format_exc())
            raise
