import asyncio
import os
from dotenv import load_dotenv
from prisma import Prisma

# Load environment variables from parent directory's .env file
load_dotenv(dotenv_path='../../.env')

async def main():
    prisma = Prisma()
    await prisma.connect()
    try:
        users = await prisma.user.find_many()
        print("Users:", users)
    except Exception as e:
        print("Error:", str(e))
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
