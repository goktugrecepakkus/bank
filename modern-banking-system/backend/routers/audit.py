from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from security import get_current_user, get_current_admin
from typing import List

# Extending the ledger router
router = APIRouter(prefix="/ledger", tags=["Ledger & Transfers"])

# ... (Previous routes will be merged into the existing ledger router in the replace step)
