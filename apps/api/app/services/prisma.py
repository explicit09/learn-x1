import os
import asyncio
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Generic
from pydantic import BaseModel
from prisma import Prisma
from prisma.errors import PrismaError
from fastapi import HTTPException, status

# Initialize Prisma client
prisma = Prisma()

# Type variable for generic database operations
T = TypeVar('T')

class PrismaService(Generic[T]):
    """Service for interacting with Prisma ORM."""
    
    def __init__(self):
        """Initialize the Prisma client."""
        self.prisma = prisma
        self.connected = False
    
    async def connect(self):
        """Connect to the database."""
        if not self.connected:
            await self.prisma.connect()
            self.connected = True
    
    async def disconnect(self):
        """Disconnect from the database."""
        if self.connected:
            await self.prisma.disconnect()
            self.connected = False
    
    async def get(self, model: str, id: str) -> Optional[Dict[str, Any]]:
        """Get a record by ID."""
        try:
            await self.connect()
            model_instance = getattr(self.prisma, model)
            result = await model_instance.find_unique(where={"id": id})
            return result
        except PrismaError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    async def get_many(
        self, 
        model: str, 
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[Dict[str, str]] = None,
        skip: int = 0,
        take: int = 100,
        include: Optional[Dict[str, bool]] = None
    ) -> List[Dict[str, Any]]:
        """Get multiple records with filtering and pagination."""
        try:
            await self.connect()
            model_instance = getattr(self.prisma, model)
            result = await model_instance.find_many(
                where=where,
                order_by=order_by,
                skip=skip,
                take=take,
                include=include
            )
            return result
        except PrismaError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    async def create(self, model: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        try:
            await self.connect()
            print(f"\n=== Creating {model} ===\nData:", data)
            
            # Verify model exists
            if not hasattr(self.prisma, model):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid model: {model}"
                )
            
            # Get model instance
            model_instance = getattr(self.prisma, model)
            
            # Attempt to create record
            try:
                result = await model_instance.create(data=data)
                print(f"\n=== Successfully created {model} ===\nResult:", result)
                return result
            except Exception as e:
                print(f"\n=== Error creating {model} ===\nError:", str(e))
                print("Error details:", e.__dict__)
                
                # Check for common errors
                error_str = str(e).lower()
                if "unique constraint" in error_str:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"A {model} with these details already exists"
                    )
                elif "foreign key constraint" in error_str:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Referenced record not found"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Error creating {model}: {str(e)}"
                    )
                    
        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"\n=== Unexpected error creating {model} ===\nError:", str(e))
            print("Error details:", e.__dict__)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {str(e)}"
            )
    
    async def update(self, model: str, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record."""
        try:
            await self.connect()
            model_instance = getattr(self.prisma, model)
            result = await model_instance.update(
                where={"id": id},
                data=data
            )
            return result
        except PrismaError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    async def delete(self, model: str, id: str) -> Dict[str, Any]:
        """Delete a record."""
        try:
            await self.connect()
            model_instance = getattr(self.prisma, model)
            result = await model_instance.delete(where={"id": id})
            return result
        except PrismaError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    async def count(self, model: str, where: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        try:
            await self.connect()
            model_instance = getattr(self.prisma, model)
            result = await model_instance.count(where=where)
            return result
        except PrismaError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

# Create a singleton instance of the PrismaService
prisma_service = PrismaService()
