from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.services.nl_query import StatementQueryEngine

router = APIRouter(prefix="/api/query", tags=["Ask Your Statement"])

class QueryRequest(BaseModel):
    question: str

@router.post("/ask")
def ask_statement(req: QueryRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Answers natural language questions about your statement using a secure,
    structured query specification. Never generates or runs raw SQL.
    Returns computed answer, structured spec, and auditable source rows.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    return StatementQueryEngine.execute_query(req.question.strip(), db)

