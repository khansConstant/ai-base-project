import json
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
    
def update_company_with_enrichment(db: Session, company_id: str, final_state: Dict[str, Any]) -> bool:
    """
    Update company with enriched data from final_state
    
    Args:
        db: Database session
        company_id: ID of the company to update
        final_state: Dictionary containing enriched data
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    try:
        print(final_state.get('company_linkedin_url'),'company_linkedin_url')
        print(final_state.get('glassdoor_url'),'glassdoor_url')
        print(final_state.get('company_search_results'),'company_search_results')
        print(final_state.get('company_linkedin_details'),'company_linkedin_details')
        print(final_state.get('company_linkedin_analysis'),'company_linkedin_analysis')
        print(final_state.get('glassdoor_details'),'glassdoor_details')
        print(final_state.get('glassdoor_analysis'),'glassdoor_analysis')
        print(final_state.get('company_insights'),'company_insights')

        update_data = {
            'linkedin_url': final_state.get('company_linkedin_url'),
            'glassdoor_url': final_state.get('glassdoor_url'),
            'website': (final_state.get('company_search_results') or {}),
            'linkedin_details': final_state.get('company_linkedin_details'),
            'linkedin_analysis': final_state.get('company_linkedin_analysis'),
            'glassdoor_details': final_state.get('glassdoor_details'),
            'glassdoor_analysis': final_state.get('glassdoor_analysis'),
            'company_insights': final_state.get('company_insights'),
        }
        
        print(update_data,'update_data')
        # Serialize dicts and lists, handle JSON strings
        for key, value in update_data.items():
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except:
                    pass
            if isinstance(value, (dict, list)):
                update_data[key] = json.dumps(value, default=str)
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if update_data:
            set_clause = ", ".join(f"{k} = :{k}" for k in update_data.keys())
            
            query = f"""
                UPDATE companies
                SET {set_clause}, updated_at = NOW()
                WHERE id = :id
                RETURNING *
            """
            
            update_data['id'] = company_id
            
            result = db.execute(text(query), update_data)
            db.commit()
            company = result.mappings().first()
            return company is not None
        
        return True  # No updates needed
    
    except Exception as e:
        db.rollback()
        raise e


def update_enrichment_job(db: Session, lead_id: str, status: str = 'completed', result: Optional[Dict[str, Any]] = None) -> bool:
    """
    Update enrichment job status and result
    
    Args:
        db: Database session
        lead_id: ID of the lead for the enrichment job
        status: Status to set (default 'completed')
        result: Optional result dictionary
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    try:
        update_data = {
            'status': status,
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if update_data:
            set_clause = ", ".join(f"{k} = :{k}" for k in update_data.keys())
            
            update_data['lead_id'] = lead_id
            
            query = f"""
                UPDATE enrichment_jobs 
                SET {set_clause}, updated_at = NOW()
                WHERE lead_id = :lead_id
                RETURNING *
            """
            
            update_data['lead_id'] = lead_id

            print(update_data,'update_data_enrichment_job')
            print(query,'query_enrichment_job')
            
            result = db.execute(text(query), update_data)
            db.commit()
            job = result.mappings().first()
            return job is not None
        return True  # No updates needed
        
    except Exception as e:
        db.rollback()
        raise e
