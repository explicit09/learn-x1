import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path
from prisma import Prisma

# Load environment variables from the root .env file
root_env = Path(__file__).parent.parent.parent / '.env'
load_dotenv(root_env)

async def main():
    # Initialize Prisma client
    prisma = Prisma()
    print("Database URL:", os.getenv("DATABASE_URL"))
    print("Connecting to database...")
    await prisma.connect()
    
    try:
        # Create a test organization
        print("Creating test organization...")
        org = await prisma.organization.create(
            data={
                "name": "Test Organization",
                "domain": "test.com",
                "is_active": True
            }
        )
        print("Created organization:", org)
        
        # Create a test user
        print("Creating test user...")
        user = await prisma.user.create(
            data={
                "email": "test@example.com",
                "password": "hashedpassword123",
                "name": "Test User",
                "role": "admin",
                "is_active": True,
                "organizationId": org.id
            }
        )
        print("Created user:", user)
        
    except Exception as e:
        print("Error:", str(e))
        print("Error details:", e.__dict__)
    
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
