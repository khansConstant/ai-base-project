from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Union
from app.database.base import get_db
from sqlalchemy.sql import text
from app.services import lead_service
from datetime import datetime
import logging
from app.celery_config import celery_app
from sqlalchemy import func 

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leads", tags=["leads"])

@router.post(
    "/enrich",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enrich one or multiple leads",
    response_model=Dict[str, Any],
    description="""
    Enrich one or multiple leads asynchronously using Celery.
    
    This endpoint accepts either a single lead or a list of leads (up to 100).
    Each lead should contain the following fields:
    - name (str): Full name of the lead
    - email (str): Email address (must be unique)
    - designation (str): Job title/position
    - company (str): Company name
    """
)
async def enrich_leads(
    leads_data: Union[Dict[str, Any], List[Dict[str, Any]]],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    try:
        # Convert single lead to list for uniform processing
        is_single = not isinstance(leads_data, list)
        leads_list = [leads_data] if is_single else leads_data
        
        # Validate input
        if not leads_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No lead data provided"
            )
            
        if len(leads_list) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 leads can be processed at once"
            )
        
        # Validate each lead
        required_fields = {'id','name', 'email', 'designation', 'company'}
        for i, lead in enumerate(leads_list, 1):
            if not isinstance(lead, dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Lead at position {i} is not a valid object"
                )
            
            missing_fields = required_fields - set(lead.keys())
            if missing_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Lead at position {i} is missing required fields: {', '.join(missing_fields)}"
                )
        
        # Process leads asynchronously
        task_results = []
        print(leads_list,'lead_list')
        for lead in leads_list:
            try:
                db_lead = db.execute(
                    text("""
                            SELECT 
                                l.id AS lead_id,
                                c.id as company_id,
                                l.name As name,
                                c.name As company_name,
                                l.lead_details,
                                l.designation,
                                l.email,
                                l.google_results,
                                l.linkedin_url,
                                l.linkedin_details_raw,
                                l.linkedin_details,
                                l.lead_score,
                                l.company_search_results,
                                l.lead_stage,
                                l.stage_metadata,
                                c.linkedin_url AS company_linkedin_url,
                                c.linkedin_details AS company_linkedin_details,
                                c.linkedin_analysis AS company_linkedin_analysis,
                                c.glassdoor_url,
                                c.glassdoor_details,
                                c.glassdoor_analysis,
                                c.company_insights,
                                ej.status AS enrichment_status,
                                ej.result AS enrichment_result

                            FROM leads l
                            LEFT JOIN companies c
                                ON l.company_id = c.id
                            LEFT JOIN enrichment_jobs ej
                                ON ej.lead_id = l.id
                            WHERE l.id = :id
                    """),
                    {'id': lead['id']}
                ).fetchone()

                if not db_lead:
                    logger.warning(f"No lead found in DB for ID {lead['id']}")
                    continue

                # Convert Row → dict (works in SQLAlchemy 1.4+)
                db_lead_dict = dict(db_lead._mapping)

                task = celery_app.send_task('enrich_lead_task', args=[db_lead_dict])

                task_results.append({
                    'email': lead['email'],
                    'task_id': str(task.id),
                    'status': 'pending'
                })

                logger.info(f"Enrichment task queued for {lead['email']} with task ID: {task.id}")

            except Exception as e:
                logger.error(f"Failed to queue task for {lead.get('email', 'unknown')}: {str(e)}")
                task_results.append({
                    'email': lead.get('email', 'unknown'),
                    'error': str(e),
                    'status': 'failed'
                })

        return {
            'success': True,
            'message': f"Successfully queued {len(leads_list)} leads for enrichment",
            'results': task_results,
            'is_single': is_single
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in enrich_leads endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lead",
    response_model=Dict[str, Any],
    description="""
    Creates a new lead in the database.
    
    Required fields:
    - name: Full name of the lead
    - email: Email address (must be unique)
    
    Optional fields:
    - company: Company name (will be created if it doesn't exist)
    - designation: Job title/position
    - lead_stage: Current stage of the lead (default: 'new')
    - messages: JSON array of messages
    - lead_details: JSON object with additional lead details
    - linkedin_url: LinkedIn profile URL
    - Any other fields from the leads table schema
    """
)
async def create_lead(lead_data: Dict[str, Any], db: Session = Depends(get_db)):
    try:
        # Basic validation
        if not all(key in lead_data for key in ['name', 'email','designation','company']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name, email, designation and company are required"
            )
            
        # Create the lead
        result = lead_service.create_lead(db=db, lead_data=lead_data)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create lead"
            )
            
        return result
        
    except Exception as e:
        error_msg = str(e).lower()
        if "duplicate" in error_msg or "already exists" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A lead with this email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating lead: {str(e)}"
        )

@router.put(
    "/{lead_id}",
    summary="Update a lead",
    response_model=Dict[str, Any],
    description="""
    Updates an existing lead.
    
    You can update any field from the leads table schema.
    If you provide a 'company' field, it will be used to create or link to an existing company.
    """
)
async def update_lead(
    lead_id: str,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    try:
        result = lead_service.update_lead(
            db=db,
            lead_id=lead_id,
            update_data=update_data
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
            
        return result
        
    except Exception as e:
        error_msg = str(e).lower()
        if "duplicate" in error_msg or "already exists" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A lead with this email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating lead: {str(e)}"
        )

@router.get(
    "/",
    summary="Get all leads",
    response_model=List[Dict[str, Any]],
    description="""
    Retrieves a paginated list of leads with optional filtering.
    
    Query Parameters:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100, max: 1000)
    - company: Filter by company name (partial match)
    - lead_stage: Filter by lead stage
    - email: Filter by exact email match
    """
)
async def read_leads(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    lead_stage: Optional[str] = Query(None, description="Filter by lead stage"),
    email: Optional[str] = Query(None, description="Filter by exact email"),
    db: Session = Depends(get_db)
):
    try:
        # Build filters
        filters = {}
        if company:
            filters['company'] = company
        if lead_stage:
            filters['lead_stage'] = lead_stage
        if email:
            filters['email'] = email
            
        return lead_service.get_leads(
            db=db,
            skip=skip,
            limit=limit,
            filters=filters
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving leads: {str(e)}"
        )

@router.get(
    "/{lead_id}",
    summary="Get lead by ID",
    response_model=Dict[str, Any],
    description="Retrieves a single lead by its ID"
)
async def read_lead(lead_id: str, db: Session = Depends(get_db)):
    try:
        lead = lead_service.get_lead(db, lead_id=lead_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        return lead
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving lead: {str(e)}"
        )
