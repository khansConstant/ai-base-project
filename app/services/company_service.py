from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, Optional
import uuid

def get_or_create_company(db: Session, company_name: str) -> Dict[str, Any]:
    """Get a company by name or create it if it doesn't exist"""
    if not company_name:
        return None
        
    # Try to get existing company
    result = db.execute(
        text("SELECT * FROM companies WHERE name = :name"),
        {'name': company_name}
    )
    company = result.mappings().first()
    
    # If company doesn't exist, create it
    if not company:
        company_id = str(uuid.uuid4())
        db.execute(
            text("""
                INSERT INTO companies (id, name, created_at, updated_at)
                VALUES (:id, :name, NOW(), NOW())
                RETURNING *
            """),
            {'id': company_id, 'name': company_name}
        )
        db.commit()
        
        # Fetch the newly created company
        result = db.execute(
            text("SELECT * FROM companies WHERE id = :id"),
            {'id': company_id}
        )
        company = result.mappings().first()
    
    return dict(company) if company else None

def update_company(
    db: Session, 
    company_id: str, 
    update_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Update company fields"""
    if not update_data:
        return None
        
    # Build the SET clause dynamically
    set_clause = ", ".join(f"{k} = :{k}" for k in update_data.keys())
    
    # Add updated_at
    update_data['updated_at'] = 'NOW()'
    update_data['id'] = company_id
    
    query = f"""
        UPDATE companies 
        SET {set_clause}
        WHERE id = :id
        RETURNING *
    """
    
    result = db.execute(text(query), update_data)
    db.commit()
    company = result.mappings().first()
    return dict(company) if company else None
