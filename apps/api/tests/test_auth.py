import pytest
from httpx import AsyncClient
from app.main import app
from app.services.prisma import prisma_service
from app.schemas.user import UserRole
import uuid

@pytest.mark.asyncio
class TestAuthRegistration:
    """Test cases for user registration."""
    
    async def setup_method(self):
        """Setup before each test."""
        self.client = AsyncClient(app=app, base_url="http://test")
        # Connect to test database
        await prisma_service.connect()
    
    async def teardown_method(self):
        """Cleanup after each test."""
        # Clean up test data
        await prisma_service.prisma.user.delete_many()
        await prisma_service.prisma.organization.delete_many()
        await prisma_service.disconnect()

    # Test data constants
    VALID_USER_DATA = {
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User",
        "organization_name": "Test Organization",
        "organization_domain": "test.com"
    }

    async def test_successful_registration_new_org(self):
        """Test successful registration with new organization."""
        response = await self.client.post(
            "/auth/register",
            json=self.VALID_USER_DATA
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "data" in data
        assert "message" in data
        assert data["message"] == "User registered successfully"
        
        # Check user data
        user = data["data"]
        assert user["email"] == self.VALID_USER_DATA["email"]
        assert user["name"] == self.VALID_USER_DATA["name"]
        assert "password" not in user  # Password should not be in response
        assert "organizationId" in user
        assert user["role"] == UserRole.ADMIN  # First user should be admin
        
        # Verify database state
        db_user = await prisma_service.prisma.user.find_unique(
            where={"id": user["id"]}
        )
        assert db_user is not None
        assert db_user.email == self.VALID_USER_DATA["email"]
        
        # Verify organization was created
        db_org = await prisma_service.prisma.organization.find_unique(
            where={"id": user["organizationId"]}
        )
        assert db_org is not None
        assert db_org.name == self.VALID_USER_DATA["organization_name"]

    async def test_successful_registration_existing_org(self):
        """Test successful registration with existing organization."""
        # First, create an organization
        org_data = {
            "name": "Existing Organization",
            "domain": "existing.com"
        }
        org = await prisma_service.prisma.organization.create(
            data=org_data
        )
        
        # Register with existing organization ID
        user_data = {
            "email": "test2@example.com",
            "password": "password123",
            "name": "Test User 2",
            "organizationId": org.id
        }
        
        response = await self.client.post(
            "/auth/register",
            json=user_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check user was assigned to existing organization
        user = data["data"]
        assert user["organizationId"] == org.id
        assert user["role"] == UserRole.ADMIN  # First user in org should be admin
        
        # Verify database state
        db_user = await prisma_service.prisma.user.find_unique(
            where={"id": user["id"]}
        )
        assert db_user is not None
        assert db_user.organization_id == org.id

    async def test_duplicate_email(self):
        """Test registration with duplicate email."""
        # First registration
        await self.client.post(
            "/auth/register",
            json=self.VALID_USER_DATA
        )
        
        # Second registration with same email
        response = await self.client.post(
            "/auth/register",
            json=self.VALID_USER_DATA
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "email already registered" in data["error"].lower()

    async def test_invalid_organization(self):
        """Test registration with invalid organization ID."""
        invalid_org_data = {
            "email": "test3@example.com",
            "password": "password123",
            "name": "Test User 3",
            "organizationId": str(uuid.uuid4())  # Random non-existent ID
        }
        
        response = await self.client.post(
            "/auth/register",
            json=invalid_org_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "organization not found" in data["error"].lower()

    async def test_missing_required_fields(self):
        """Test registration with missing required fields."""
        # Missing email
        data_missing_email = {
            "password": "password123",
            "name": "Test User"
        }
        
        response = await self.client.post(
            "/auth/register",
            json=data_missing_email
        )
        
        assert response.status_code == 422
        
        # Missing password
        data_missing_password = {
            "email": "test@example.com",
            "name": "Test User"
        }
        
        response = await self.client.post(
            "/auth/register",
            json=data_missing_password
        )
        
        assert response.status_code == 422
        
        # Missing name
        data_missing_name = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = await self.client.post(
            "/auth/register",
            json=data_missing_name
        )
        
        assert response.status_code == 422
        
        # Missing organization info (both name and ID)
        data_missing_org = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User"
        }
        
        response = await self.client.post(
            "/auth/register",
            json=data_missing_org
        )
        
        assert response.status_code == 422

    async def test_password_validation(self):
        """Test password validation rules."""
        # Test short password
        short_password_data = {
            "email": "test@example.com",
            "password": "short",  # Less than minimum length
            "name": "Test User",
            "organization_name": "Test Organization"
        }
        
        response = await self.client.post(
            "/auth/register",
            json=short_password_data
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert "password" in data["error"].lower()

@pytest.mark.asyncio
class TestAuthLogin:
    """Test cases for user login."""
    
    async def setup_method(self):
        """Setup before each test."""
        self.client = AsyncClient(app=app, base_url="http://test")
        await prisma_service.connect()
        
        # Create a test user
        self.user_data = {
            "email": "login_test@example.com",
            "password": "password123",
            "name": "Login Test User",
            "organization_name": "Login Test Org"
        }
        
        # Register the user
        await self.client.post(
            "/auth/register",
            json=self.user_data
        )
    
    async def teardown_method(self):
        """Cleanup after each test."""
        await prisma_service.prisma.user.delete_many()
        await prisma_service.prisma.organization.delete_many()
        await prisma_service.disconnect()
    
    async def test_successful_login(self):
        """Test successful login."""
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        response = await self.client.post(
            "/auth/login",
            json=login_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "data" in data
        assert "access_token" in data["data"]
        assert "token_type" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert "expires_at" in data["data"]
    
    async def test_invalid_credentials(self):
        """Test login with invalid credentials."""
        # Test with wrong password
        wrong_password_data = {
            "email": self.user_data["email"],
            "password": "wrongpassword"
        }
        
        response = await self.client.post(
            "/auth/login",
            json=wrong_password_data
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "incorrect email or password" in data["error"].lower()
        
        # Test with non-existent email
        non_existent_user_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = await self.client.post(
            "/auth/login",
            json=non_existent_user_data
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "incorrect email or password" in data["error"].lower()
    
    async def test_missing_login_fields(self):
        """Test login with missing fields."""
        # Missing email
        missing_email_data = {
            "password": "password123"
        }
        
        response = await self.client.post(
            "/auth/login",
            json=missing_email_data
        )
        
        assert response.status_code == 422
        
        # Missing password
        missing_password_data = {
            "email": self.user_data["email"]
        }
        
        response = await self.client.post(
            "/auth/login",
            json=missing_password_data
        )
        
        assert response.status_code == 422
