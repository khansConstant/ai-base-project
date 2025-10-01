from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid
from sqlalchemy import func 
from .company_service import get_or_create_company
from ..utils.db_utils import update_table_row

def create_lead(db: Session, lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new lead in the database
    
    Args:
        db: Database session
        lead_data: Dictionary containing lead data
        
    Returns:
        The created lead as a dictionary
    """
    try:
        # Handle company first
        company = None
        if 'company' in lead_data and lead_data.get('company'):
            company = get_or_create_company(db, lead_data['company'])
        
        # Prepare lead data
        lead_dict = {
            'id': str(uuid.uuid4()),  # Generate a unique ID for the lead
            'name': lead_data.get('name'),
            'email': lead_data.get('email'),
            'designation': lead_data.get('designation'),
            'company_id': company['id'] if company else None,
            'lead_stage': 'new',  # Default stage
        }
        
        # Add optional JSON fields if they exist
        json_fields = ['messages', 'lead_details', 'linkedin_details_raw', 
                       'linkedin_details', 'lead_score', 'engagement_metrics',
                       'stage_metadata', 'content', 'glassdoor_comments']
        
        for field in json_fields:
            if field in lead_data:
                lead_dict[field] = lead_data[field]
        
        # Build the INSERT query
        columns = ", ".join(lead_dict.keys())
        values = ", ".join(f":{k}" for k in lead_dict.keys())
        
        query = f"""
            INSERT INTO leads ({columns})
            VALUES ({values})
            RETURNING *
        """
        
        # Execute the query
        result = db.execute(text(query), lead_dict)

        # Fetch the inserted lead (including the id)
        inserted_lead = result.mappings().first()  # This will give the first inserted record

        if inserted_lead:
            # Extract the id from the inserted lead
            lead_id = inserted_lead['id']

            # Insert into enrichment_jobs table
            enrichment_query = "INSERT INTO enrichment_jobs (lead_id, status) VALUES (:lead_id, 'pending')"

            db.execute(text(enrichment_query), {'lead_id': lead_id})

            db.commit()

            # Return the created lead including the id
            return dict(inserted_lead)  # Return the lead as a dictionary
        else:
            db.rollback()
            return None
        
    except Exception as e:
        db.rollback()
        raise e

def update_lead(
    db: Session, 
    lead_id: str, 
    update_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Update lead fields
    
    Args:
        db: Database session
        lead_id: ID of the lead to update
        update_data: Dictionary of fields to update
        
    Returns:
        The updated lead as a dictionary if successful, None otherwise
    """
    try:
        # Handle company update if needed
        if 'company' in update_data and update_data['company']:
            company = get_or_create_company(db, update_data.pop('company'))
            update_data['company_id'] = company['id']
        
        # Update the lead
        return update_table_row(
            db=db,
            table_name='leads',
            id_value=lead_id,
            update_data=update_data
        )
        
    except Exception as e:
        db.rollback()
        raise e

def get_lead(db: Session, lead_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a lead by ID
    
    Args:
        db: Database session
        lead_id: ID of the lead to retrieve
        
    Returns:
        The lead as a dictionary if found, None otherwise
    """
    result = db.execute(
        text("""
            SELECT l.*, c.name as company_name
            FROM leads l
            LEFT JOIN companies c ON l.company_id = c.id
            WHERE l.id = :lead_id
        """),
        {'lead_id': lead_id}
    )
    lead = result.mappings().first()
    return dict(lead) if lead else None

def get_leads(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Get a list of leads with optional filtering
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        filters: Dictionary of filters to apply
        
    Returns:
        List of leads as dictionaries
    """
    query = """
        SELECT l.*, c.name as company_name
        FROM leads l
        LEFT JOIN companies c ON l.company_id = c.id
    """
    
    params = {}
    where_clauses = []
    
    # Add filters if provided
    if filters:
        for key, value in filters.items():
            if value is not None:
                param_name = f"filter_{key}"
                where_clauses.append(f"l.{key} = :{param_name}")
                params[param_name] = value
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    # Add sorting and pagination
    query += """
        ORDER BY l.created_at DESC
        OFFSET :skip LIMIT :limit
    """
    params.update({'skip': skip, 'limit': limit})
    
    # Execute the query
    result = db.execute(text(query), params)
    return [dict(row) for row in result.mappings()]
