from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

def update_table_row(
    db: Session,
    table_name: str,
    id_value: str,
    id_column: str = 'id',
    update_data: Optional[Dict[str, Any]] = None,
    return_updated: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Generic function to update a row in any table
    
    Args:
        db: Database session
        table_name: Name of the table to update
        id_value: Value of the ID to identify the row
        id_column: Name of the ID column (default: 'id')
        update_data: Dictionary of column names and values to update
        return_updated: Whether to return the updated row
        
    Returns:
        The updated row as a dictionary if return_updated is True, else None
    """
    if not update_data:
        return None
    
    # Remove None values and prepare data
    update_data = {k: v for k, v in update_data.items() if v is not None}
    if not update_data:
        return None
    
    # Add updated_at if the column exists
    update_data['updated_at'] = 'NOW()'
    update_data['id_param'] = id_value
    
    # Build the SET clause
    set_clause = ", ".join(f"{k} = :{k}" for k in update_data.keys())
    
    # Build and execute the query
    query = f"""
        UPDATE {table_name}
        SET {set_clause}
        WHERE {id_column} = :id_param
    """
    
    if return_updated:
        query += " RETURNING *"
    
    result = db.execute(text(query), update_data)
    
    if return_updated:
        row = result.mappings().first()
        return dict(row) if row else None
    
    return None
