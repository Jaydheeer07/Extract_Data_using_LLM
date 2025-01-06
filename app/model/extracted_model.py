from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class LineItem(BaseModel):
    description: str
    quantity: Optional[int] = None  # Make quantity optional
    unit_price: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    total_price: Decimal = Field(..., max_digits=10, decimal_places=2)
    gst: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)


class InvoiceInfo(BaseModel):
    document_type: Literal["invoice", "statement"]  # Required field
    invoice_number: Optional[str] = None  # Optional for statements
    invoice_date: Optional[date] = None  # Optional for statements
    total_amount: Decimal = Field(..., decimal_places=2)  # Required field
    vendor_name: str  # Required field
    customer_name: str  # Required field
    due_date: Optional[date] = None  # Optional field
    tax_amount: Optional[Decimal] = Field(None, decimal_places=2)  # Optional field
    line_items: Optional[List[LineItem]] = None  # Optional field
    PO_number: Optional[str] = None  # New field for invoices (optional)
    statement_date: Optional[date] = None  # New field for statements
    reference: Optional[str] = None  # New field for statements
    statement_due_date: Optional[date] = None  # New field for statements

    @field_validator(
        "invoice_date",
        "due_date",
        "statement_date",
        "statement_due_date",
        mode="before",
    )
    def parse_date(cls, value):
        if value is None:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        # Convert date fields to ISO format strings
        data = super().model_dump(**kwargs)
        if self.invoice_date:
            data["invoice_date"] = self.invoice_date.isoformat()
        if self.due_date:
            data["due_date"] = self.due_date.isoformat()
        if self.statement_date:
            data["statement_date"] = self.statement_date.isoformat()
        if self.statement_due_date:
            data["statement_due_date"] = self.statement_due_date.isoformat()

        # Convert Decimal fields to floats
        if isinstance(self.total_amount, Decimal):
            data["total_amount"] = float(self.total_amount)
        if isinstance(self.tax_amount, Decimal):
            data["tax_amount"] = (
                float(self.tax_amount) if self.tax_amount is not None else None
            )

        # Convert Decimal fields in line_items
        if self.line_items:
            for item in data["line_items"]:
                if "unit_price" in item and isinstance(item["unit_price"], Decimal):
                    item["unit_price"] = float(item["unit_price"])
                if "total_price" in item and isinstance(item["total_price"], Decimal):
                    item["total_price"] = float(item["total_price"])
                if "gst" in item and isinstance(item["gst"], Decimal):
                    item["gst"] = (
                        float(item["gst"]) if item["gst"] is not None else None
                    )

        return data
