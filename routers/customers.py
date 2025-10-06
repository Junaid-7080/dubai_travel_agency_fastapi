# ===== routers/customers.py =====
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func, and_, or_
from typing import List, Optional
from datetime import datetime
import re
import logging

from models import Customer, User, UserRole
from schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerFilter, 
    CustomerStats, APIResponse
)
from database import get_session
from auth import get_current_user, get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["Customer Management"])

# ===== Validation Functions =====
def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_mobile(mobile: str) -> bool:
    """Validate mobile number format (international format)"""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', mobile)
    # Check if it's between 7 and 15 digits (international standard)
    return 7 <= len(digits_only) <= 15

def validate_passport_number(passport_number: str) -> bool:
    """Validate passport number format"""
    # Basic validation - alphanumeric, 6-12 characters
    pattern = r'^[A-Za-z0-9]{6,12}$'
    return re.match(pattern, passport_number) is not None

def validate_customer_data(customer_data: CustomerCreate) -> List[str]:
    """Validate customer data and return list of errors"""
    errors = []
    
    if not validate_email(customer_data.email):
        errors.append("Invalid email format")
    
    if not validate_mobile(customer_data.mobile):
        errors.append("Invalid mobile number format")
    
    if not validate_passport_number(customer_data.passport_number):
        errors.append("Invalid passport number format")
    
    if customer_data.passport_expiry <= datetime.utcnow():
        errors.append("Passport has expired")
    
    if customer_data.date_of_birth >= datetime.utcnow():
        errors.append("Date of birth cannot be in the future")
    
    if customer_data.gender not in ["male", "female", "other"]:
        errors.append("Gender must be 'male', 'female', or 'other'")
    
    return errors

# ===== Customer CRUD Operations =====

@router.post("/", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user)
):
    """Create a new customer"""
    # Validate customer data
    validation_errors = validate_customer_data(customer_data)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation errors: {', '.join(validation_errors)}"
        )
    
    # Check if customer with same email already exists
    statement = select(Customer).where(Customer.email == customer_data.email)
    existing_customer = session.exec(statement).first()
    
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists"
        )
    
    # Check if customer with same passport number already exists
    statement = select(Customer).where(Customer.passport_number == customer_data.passport_number)
    existing_passport = session.exec(statement).first()
    
    if existing_passport:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this passport number already exists"
        )
    
    # Create new customer
    customer = Customer(**customer_data.dict())
    session.add(customer)
    session.commit()
    session.refresh(customer)
    
    logger.info(f"Customer created: {customer.id} - {customer.name}")
    
    return customer

@router.get("/", response_model=List[CustomerResponse])
async def get_customers(
    search: Optional[str] = Query(None, description="Search by name, email, or passport number"),
    nationality: Optional[str] = Query(None, description="Filter by nationality"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    language: Optional[str] = Query(None, description="Filter by language"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user)
):
    """Get all customers with filtering and pagination"""
    # Build query
    statement = select(Customer)
    
    # Apply filters
    conditions = []
    
    if search:
        search_condition = or_(
            Customer.name.ilike(f"%{search}%"),
            Customer.email.ilike(f"%{search}%"),
            Customer.passport_number.ilike(f"%{search}%")
        )
        conditions.append(search_condition)
    
    if nationality:
        conditions.append(Customer.nationality == nationality)
    
    if is_active is not None:
        conditions.append(Customer.is_active == is_active)
    
    if language:
        conditions.append(Customer.language == language)
    
    if conditions:
        statement = statement.where(and_(*conditions))
    
    # Apply pagination
    offset = (page - 1) * size
    statement = statement.offset(offset).limit(size)
    
    # Order by creation date (newest first)
    statement = statement.order_by(Customer.created_at.desc())
    
    customers = session.exec(statement).all()
    return customers

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user)
):
    """Get a specific customer by ID"""
    statement = select(Customer).where(Customer.id == customer_id)
    customer = session.exec(statement).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user)
):
    """Update a customer"""
    statement = select(Customer).where(Customer.id == customer_id)
    customer = session.exec(statement).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Validate updated data if provided
    if customer_data.email and not validate_email(customer_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    if customer_data.mobile and not validate_mobile(customer_data.mobile):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mobile number format"
        )
    
    if customer_data.passport_number and not validate_passport_number(customer_data.passport_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid passport number format"
        )
    
    # Check for duplicate email if email is being updated
    if customer_data.email and customer_data.email != customer.email:
        statement = select(Customer).where(
            and_(Customer.email == customer_data.email, Customer.id != customer_id)
        )
        existing_customer = session.exec(statement).first()
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer with this email already exists"
            )
    
    # Check for duplicate passport if passport is being updated
    if customer_data.passport_number and customer_data.passport_number != customer.passport_number:
        statement = select(Customer).where(
            and_(Customer.passport_number == customer_data.passport_number, Customer.id != customer_id)
        )
        existing_passport = session.exec(statement).first()
        if existing_passport:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer with this passport number already exists"
            )
    
    # Update customer
    update_data = customer_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    customer.updated_at = datetime.utcnow()
    session.add(customer)
    session.commit()
    session.refresh(customer)
    
    logger.info(f"Customer updated: {customer.id} - {customer.name}")
    
    return customer

@router.delete("/{customer_id}", response_model=APIResponse)
async def delete_customer(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user)
):
    """Delete a customer (soft delete by setting is_active to False)"""
    statement = select(Customer).where(Customer.id == customer_id)
    customer = session.exec(statement).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Soft delete - set is_active to False
    customer.is_active = False
    customer.updated_at = datetime.utcnow()
    session.add(customer)
    session.commit()
    
    logger.info(f"Customer deactivated: {customer.id} - {customer.name}")
    
    return APIResponse(
        success=True,
        message=f"Customer {customer.name} has been deactivated"
    )

@router.post("/{customer_id}/activate", response_model=APIResponse)
async def activate_customer(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user)
):
    """Activate a customer"""
    statement = select(Customer).where(Customer.id == customer_id)
    customer = session.exec(statement).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    customer.is_active = True
    customer.updated_at = datetime.utcnow()
    session.add(customer)
    session.commit()
    
    logger.info(f"Customer activated: {customer.id} - {customer.name}")
    
    return APIResponse(
        success=True,
        message=f"Customer {customer.name} has been activated"
    )

@router.get("/stats/overview", response_model=CustomerStats)
async def get_customer_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user)
):
    """Get customer statistics"""
    # Total customers
    total_customers = session.exec(select(func.count(Customer.id))).first()
    
    # Active customers
    active_customers = session.exec(
        select(func.count(Customer.id)).where(Customer.is_active == True)
    ).first()
    
    # Inactive customers
    inactive_customers = total_customers - active_customers
    
    # Customers by nationality
    nationality_stats = session.exec(
        select(Customer.nationality, func.count(Customer.id))
        .where(Customer.is_active == True)
        .group_by(Customer.nationality)
    ).all()
    customers_by_nationality = {nationality: count for nationality, count in nationality_stats}
    
    # Customers by language
    language_stats = session.exec(
        select(Customer.language, func.count(Customer.id))
        .where(Customer.is_active == True)
        .group_by(Customer.language)
    ).all()
    customers_by_language = {language.value: count for language, count in language_stats}
    
    return CustomerStats(
        total_customers=total_customers,
        active_customers=active_customers,
        inactive_customers=inactive_customers,
        customers_by_nationality=customers_by_nationality,
        customers_by_language=customers_by_language
    )

@router.get("/search/email/{email}", response_model=CustomerResponse)
async def get_customer_by_email(
    email: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user)
):
    """Get customer by email address"""
    statement = select(Customer).where(Customer.email == email)
    customer = session.exec(statement).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return customer

@router.get("/search/passport/{passport_number}", response_model=CustomerResponse)
async def get_customer_by_passport(
    passport_number: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user)
):
    """Get customer by passport number"""
    statement = select(Customer).where(Customer.passport_number == passport_number)
    customer = session.exec(statement).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return customer

