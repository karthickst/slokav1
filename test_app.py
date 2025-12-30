import pytest
import os
from fastapi.testclient import TestClient
from config import Config
from db import Database
from auth import AuthManager
from app import app

# Set test mode
os.environ["APP_MODE"] = "test"

# Test client
client = TestClient(app)

# Test configuration
config = Config(mode="test")
db = Database(config)
auth_manager = AuthManager(config)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Setup test database before running tests"""
    print("\n=== Setting up test database ===")
    db.connect()

    # Drop all tables to start fresh
    try:
        db.execute_query("DROP TABLE IF EXISTS enrollments CASCADE", fetch=False)
        db.execute_query("DROP TABLE IF EXISTS courses CASCADE", fetch=False)
        db.execute_query("DROP TABLE IF EXISTS students CASCADE", fetch=False)
        db.execute_query("DROP TABLE IF EXISTS admins CASCADE", fetch=False)
    except Exception as e:
        print(f"Warning: Error dropping tables: {e}")

    # Initialize schema
    db.initialize_schema()

    # Seed admin
    admin_password_hash = auth_manager.hash_password("admin123")
    db.seed_admin("admin", admin_password_hash)

    print("=== Test database setup completed ===\n")

    yield

    # Cleanup
    print("\n=== Cleaning up test database ===")
    db.disconnect()


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test health check returns healthy status"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["mode"] == "test"
        print("✓ Health check test passed")


class TestStudentAuth:
    """Test student authentication endpoints"""

    def test_student_signup_success(self):
        """Test successful student signup"""
        response = client.post("/api/students/signup", json={
            "email": "test@example.com",
            "password": "password123",
            "name": "Test Student"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["student"]["email"] == "test@example.com"
        assert data["student"]["name"] == "Test Student"
        print("✓ Student signup success test passed")

    def test_student_signup_duplicate_email(self):
        """Test signup with duplicate email fails"""
        response = client.post("/api/students/signup", json={
            "email": "test@example.com",
            "password": "password123",
            "name": "Another Student"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
        print("✓ Duplicate email test passed")

    def test_student_signup_invalid_email(self):
        """Test signup with invalid email fails"""
        response = client.post("/api/students/signup", json={
            "email": "invalid-email",
            "password": "password123"
        })
        assert response.status_code == 422  # Validation error
        print("✓ Invalid email test passed")

    def test_student_signup_weak_password(self):
        """Test signup with weak password fails"""
        response = client.post("/api/students/signup", json={
            "email": "weak@example.com",
            "password": "123"
        })
        assert response.status_code == 400
        assert "at least 6 characters" in response.json()["detail"].lower()
        print("✓ Weak password test passed")

    def test_student_login_success(self):
        """Test successful student login"""
        response = client.post("/api/students/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["student"]["email"] == "test@example.com"
        print("✓ Student login success test passed")

    def test_student_login_wrong_password(self):
        """Test login with wrong password fails"""
        response = client.post("/api/students/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()
        print("✓ Wrong password test passed")

    def test_student_login_nonexistent_user(self):
        """Test login with non-existent user fails"""
        response = client.post("/api/students/login", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })
        assert response.status_code == 401
        print("✓ Nonexistent user test passed")


class TestAdminAuth:
    """Test admin authentication endpoints"""

    def test_admin_login_success(self):
        """Test successful admin login"""
        response = client.post("/api/admin/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["admin"]["username"] == "admin"
        print("✓ Admin login success test passed")

    def test_admin_login_wrong_password(self):
        """Test admin login with wrong password fails"""
        response = client.post("/api/admin/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Admin wrong password test passed")


class TestCourses:
    """Test course management endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token before each test"""
        response = client.post("/api/admin/login", json={
            "username": "admin",
            "password": "admin123"
        })
        self.admin_token = response.json()["token"]

        # Get student token
        response = client.post("/api/students/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        self.student_token = response.json()["token"]
        self.student_id = response.json()["student"]["id"]

    def test_get_courses_public(self):
        """Test getting courses without authentication"""
        response = client.get("/api/courses")
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        print("✓ Get courses public test passed")

    def test_create_course_success(self):
        """Test successful course creation by admin"""
        response = client.post(
            "/api/courses",
            json={
                "title": "Meditation Basics",
                "description": "Learn the fundamentals of meditation"
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["course"]["title"] == "Meditation Basics"
        print("✓ Create course success test passed")

    def test_create_course_unauthorized(self):
        """Test course creation without admin token fails"""
        response = client.post(
            "/api/courses",
            json={
                "title": "Unauthorized Course",
                "description": "Should fail"
            }
        )
        assert response.status_code == 401
        print("✓ Create course unauthorized test passed")

    def test_create_course_student_forbidden(self):
        """Test course creation by student fails"""
        response = client.post(
            "/api/courses",
            json={
                "title": "Student Course",
                "description": "Should fail"
            },
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        assert response.status_code == 403
        print("✓ Create course student forbidden test passed")

    def test_update_course_success(self):
        """Test successful course update"""
        # Create a course first
        create_response = client.post(
            "/api/courses",
            json={
                "title": "Original Title",
                "description": "Original description"
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        course_id = create_response.json()["course"]["id"]

        # Update the course
        response = client.put(
            f"/api/courses/{course_id}",
            json={
                "title": "Updated Title",
                "description": "Updated description"
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["course"]["title"] == "Updated Title"
        print("✓ Update course success test passed")

    def test_update_nonexistent_course(self):
        """Test updating non-existent course fails"""
        response = client.put(
            "/api/courses/99999",
            json={
                "title": "Updated Title",
                "description": "Updated description"
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == 404
        print("✓ Update nonexistent course test passed")

    def test_delete_course_success(self):
        """Test successful course deletion"""
        # Create a course first
        create_response = client.post(
            "/api/courses",
            json={
                "title": "To Be Deleted",
                "description": "Will be deleted"
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        course_id = create_response.json()["course"]["id"]

        # Delete the course
        response = client.delete(
            f"/api/courses/{course_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == 200
        print("✓ Delete course success test passed")

    def test_delete_course_unauthorized(self):
        """Test course deletion by student fails"""
        # Create a course first
        create_response = client.post(
            "/api/courses",
            json={
                "title": "Protected Course",
                "description": "Cannot be deleted by student"
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        course_id = create_response.json()["course"]["id"]

        # Try to delete as student
        response = client.delete(
            f"/api/courses/{course_id}",
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        assert response.status_code == 403
        print("✓ Delete course unauthorized test passed")


class TestEnrollments:
    """Test enrollment management endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for enrollment tests"""
        # Get admin token
        response = client.post("/api/admin/login", json={
            "username": "admin",
            "password": "admin123"
        })
        self.admin_token = response.json()["token"]

        # Get student token and ID
        response = client.post("/api/students/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        self.student_token = response.json()["token"]
        self.student_id = response.json()["student"]["id"]

        # Create a test course
        response = client.post(
            "/api/courses",
            json={
                "title": "Enrollment Test Course",
                "description": "For testing enrollments"
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.course_id = response.json()["course"]["id"]

    def test_enroll_student_success(self):
        """Test successful student enrollment"""
        response = client.post(
            "/api/enrollments",
            json={
                "student_id": self.student_id,
                "course_id": self.course_id
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == 200
        print("✓ Enroll student success test passed")

    def test_enroll_student_duplicate(self):
        """Test duplicate enrollment"""
        # First enrollment
        client.post(
            "/api/enrollments",
            json={
                "student_id": self.student_id,
                "course_id": self.course_id
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        # Duplicate enrollment
        response = client.post(
            "/api/enrollments",
            json={
                "student_id": self.student_id,
                "course_id": self.course_id
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == 200
        assert "already enrolled" in response.json()["message"].lower()
        print("✓ Duplicate enrollment test passed")

    def test_enroll_student_unauthorized(self):
        """Test enrollment by student fails"""
        response = client.post(
            "/api/enrollments",
            json={
                "student_id": self.student_id,
                "course_id": self.course_id
            },
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        assert response.status_code == 403
        print("✓ Enroll student unauthorized test passed")

    def test_get_student_courses(self):
        """Test getting student's enrolled courses"""
        # Enroll student first
        client.post(
            "/api/enrollments",
            json={
                "student_id": self.student_id,
                "course_id": self.course_id
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        # Get student courses
        response = client.get(
            f"/api/students/{self.student_id}/courses",
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        assert len(data["courses"]) > 0
        print("✓ Get student courses test passed")

    def test_get_student_courses_unauthorized(self):
        """Test getting another student's courses fails"""
        # Create another student
        client.post("/api/students/signup", json={
            "email": "another@example.com",
            "password": "password123"
        })

        # Try to access first student's courses
        response = client.get(
            f"/api/students/{self.student_id}/courses",
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        # Should succeed for own courses
        assert response.status_code == 200
        print("✓ Get student courses authorization test passed")

    def test_get_course_students(self):
        """Test getting students enrolled in a course"""
        response = client.get(
            f"/api/courses/{self.course_id}/students",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "students" in data
        print("✓ Get course students test passed")

    def test_unenroll_student_success(self):
        """Test successful unenrollment"""
        # Enroll first
        client.post(
            "/api/enrollments",
            json={
                "student_id": self.student_id,
                "course_id": self.course_id
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        # Unenroll
        response = client.delete(
            f"/api/enrollments/{self.student_id}/{self.course_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == 200
        print("✓ Unenroll student success test passed")


class TestStudentManagement:
    """Test student management endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token"""
        response = client.post("/api/admin/login", json={
            "username": "admin",
            "password": "admin123"
        })
        self.admin_token = response.json()["token"]

    def test_get_all_students_admin(self):
        """Test admin can get all students"""
        response = client.get(
            "/api/students",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "students" in data
        assert len(data["students"]) > 0
        print("✓ Get all students admin test passed")

    def test_get_all_students_unauthorized(self):
        """Test getting all students without auth fails"""
        response = client.get("/api/students")
        assert response.status_code == 401
        print("✓ Get all students unauthorized test passed")


class TestAuthManager:
    """Test authentication manager functionality"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = auth_manager.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
        print("✓ Hash password test passed")

    def test_verify_password(self):
        """Test password verification"""
        password = "testpassword123"
        hashed = auth_manager.hash_password(password)
        assert auth_manager.verify_password(password, hashed) == True
        assert auth_manager.verify_password("wrongpassword", hashed) == False
        print("✓ Verify password test passed")

    def test_create_and_verify_token(self):
        """Test token creation and verification"""
        data = {"sub": "123", "email": "test@example.com"}
        token = auth_manager.create_access_token(data, "student")

        payload = auth_manager.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["type"] == "student"
        print("✓ Create and verify token test passed")

    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        payload = auth_manager.verify_token("invalid.token.here")
        assert payload is None
        print("✓ Verify invalid token test passed")

    def test_validate_email(self):
        """Test email validation"""
        assert auth_manager.validate_email("test@example.com") == True
        assert auth_manager.validate_email("invalid-email") == False
        assert auth_manager.validate_email("@example.com") == False
        assert auth_manager.validate_email("test@") == False
        print("✓ Validate email test passed")

    def test_validate_password(self):
        """Test password validation"""
        valid, _ = auth_manager.validate_password("password123")
        assert valid == True

        valid, msg = auth_manager.validate_password("12345")
        assert valid == False
        assert "at least 6 characters" in msg.lower()

        valid, msg = auth_manager.validate_password("")
        assert valid == False
        print("✓ Validate password test passed")


def run_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("Running Comprehensive Test Suite")
    print("="*60 + "\n")

    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_tests()
