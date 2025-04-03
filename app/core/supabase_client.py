import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from app.model.extracted_model import InvoiceInfo, LineItem
from app.config import settings

logger = logging.getLogger(__name__)

class PostgresClient:
    """Client for interacting with PostgreSQL database"""
    
    def __init__(self):
        """Initialize PostgreSQL client with environment variables"""
        # Try to get connection string from settings first, then from environment
        self.connection_string = settings.POSTGRES_CONNECTION_STRING or os.getenv("SUPABASE_URL")
        self.connection = None
        
        if self.connection_string:
            try:
                self.connection = psycopg2.connect(self.connection_string)
                logger.info("PostgreSQL connection initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL connection: {str(e)}")
        else:
            logger.warning("PostgreSQL connection string not found in environment variables")
    
    def is_connected(self) -> bool:
        """Check if PostgreSQL client is connected"""
        if self.connection:
            try:
                # Check if connection is still alive
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
            except Exception:
                # Try to reconnect
                try:
                    self.connection = psycopg2.connect(self.connection_string)
                    return True
                except Exception as e:
                    logger.error(f"Failed to reconnect to PostgreSQL: {str(e)}")
                    return False
        return False
    
    def save_invoice(self, invoice_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Save invoice data to PostgreSQL"""
        if not self.is_connected():
            return {"success": False, "error": "PostgreSQL client not connected"}
        
        try:
            # Determine document type and table
            document_type = invoice_data.get("document_type")
            if not document_type:
                return {"success": False, "error": "Missing document_type in data"}
                
            table_name = "invoices" if document_type == "invoice" else "statements"
            
            # Extract line items and convert to JSON
            line_items = invoice_data.pop("line_items", [])
            line_items_json = Json([item.model_dump() if hasattr(item, 'model_dump') else item for item in line_items])
            
            # Define fields for each table
            invoice_fields = [
                "document_type", "invoice_number", "invoice_date", "total_amount", 
                "vendor_name", "customer_name", "due_date", "tax_amount", 
                "PO_number", "reference", "line_items", "uploaded_at", "filename"
            ]
            
            statement_fields = [
                "document_type", "statement_date", "total_amount", 
                "vendor_name", "customer_name", "reference", "statement_due_date",
                "PO_number", "line_items", "uploaded_at", "filename"
            ]
            
            # Create a new dict with only the fields for the specific table
            allowed_fields = invoice_fields if table_name == "invoices" else statement_fields
            filtered_dict = {k: v for k, v in invoice_data.items() if k in allowed_fields}
            
            # Add line items as JSON and metadata
            filtered_dict["line_items"] = line_items_json
            filtered_dict["uploaded_at"] = datetime.now()
            filtered_dict["filename"] = filename
            
            # Create cursor with dictionary factory
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Build the SQL query dynamically
                columns = list(filtered_dict.keys())
                placeholders = ["%s"] * len(columns)
                values = [filtered_dict[col] for col in columns]
                
                # Insert into appropriate table
                query = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING id
                """
                
                cursor.execute(query, values)
                result = cursor.fetchone()
                
                if not result:
                    return {"success": False, "error": "Failed to insert data"}
                
                # Get the inserted record ID
                record_id = result["id"]
                
                # Commit the transaction
                self.connection.commit()
                
                return {
                    "success": True, 
                    "record_id": record_id,
                    "table": table_name
                }
            
        except Exception as e:
            # Rollback in case of error
            self.connection.rollback()
            logger.error(f"Error saving to PostgreSQL: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_recent_documents(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent documents from both invoices and statements tables"""
        if not self.is_connected():
            return {"success": False, "error": "PostgreSQL client not connected"}
        
        try:
            # Create cursor with dictionary factory
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get recent invoices
                cursor.execute("""
                SELECT * FROM invoices
                ORDER BY uploaded_at DESC
                LIMIT %s
                """, (limit,))
                
                invoices = cursor.fetchall()
                
                # Get recent statements
                cursor.execute("""
                SELECT * FROM statements
                ORDER BY uploaded_at DESC
                LIMIT %s
                """, (limit,))
                
                statements = cursor.fetchall()
                
                return {
                    "success": True,
                    "invoices": invoices,
                    "statements": statements
                }
            
        except Exception as e:
            logger.error(f"Error fetching recent documents: {str(e)}")
            return {"success": False, "error": str(e)}
            
    def save_rating(self, filename: str, document_type: str, model: str, rating: int, 
                   comment: str = None, document_id: int = None) -> Dict[str, Any]:
        """Save user rating for extraction quality"""
        if not self.is_connected():
            return {"success": False, "error": "PostgreSQL client not connected"}
        
        try:
            # Create cursor with dictionary factory
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check if the ratings table exists, create it if not
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS ratings (
                    id SERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    model TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    comment TEXT,
                    document_id INTEGER NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Insert the rating
                query = """
                INSERT INTO ratings 
                (filename, document_type, model, rating, comment, document_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """
                
                values = (
                    filename,
                    document_type,
                    model,
                    rating,
                    comment,
                    document_id,
                    datetime.now()
                )
                
                cursor.execute(query, values)
                result = cursor.fetchone()
                
                if not result:
                    return {"success": False, "error": "Failed to insert rating"}
                
                # Get the inserted record ID
                record_id = result["id"]
                
                # Commit the transaction
                self.connection.commit()
                
                return {
                    "success": True, 
                    "record_id": record_id
                }
            
        except Exception as e:
            # Rollback in case of error
            self.connection.rollback()
            logger.error(f"Error saving rating to PostgreSQL: {str(e)}")
            return {"success": False, "error": str(e)}
            
    def get_document_ratings(self, document_id: int = None, document_type: str = None) -> Dict[str, Any]:
        """Get ratings for a specific document or document type"""
        if not self.is_connected():
            return {"success": False, "error": "PostgreSQL client not connected"}
        
        try:
            # Create cursor with dictionary factory
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check if the ratings table exists
                cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'ratings'
                )
                """)
                
                table_exists = cursor.fetchone()["exists"]
                if not table_exists:
                    return {"success": True, "ratings": []}
                
                # Build query based on parameters
                query = "SELECT * FROM ratings"
                params = []
                
                if document_id is not None:
                    query += " WHERE document_id = %s"
                    params.append(document_id)
                elif document_type is not None:
                    query += " WHERE document_type = %s"
                    params.append(document_type)
                
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query, params)
                ratings = cursor.fetchall()
                
                return {
                    "success": True,
                    "ratings": ratings
                }
            
        except Exception as e:
            logger.error(f"Error fetching ratings: {str(e)}")
            return {"success": False, "error": str(e)}


# Create a singleton instance
postgres = PostgresClient()
