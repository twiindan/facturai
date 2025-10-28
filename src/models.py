# ABOUTME: This file defines the Pydantic models for the application.
# ABOUTME: It includes structures for invoices, companies, and other data entities.

from pydantic import BaseModel, Field
from typing import Optional

class Company(BaseModel):
    """Represents a company with its name and tax ID."""
    name: str = Field(..., alias="Nombre")
    cif: str = Field(..., alias="CIF/ NIF")

class Invoice(BaseModel):
    """Represents a single invoice document with extracted details."""
    provider_cif: str = Field(..., alias="CIF/ NIF Proveedor")
    provider_name: str = Field(..., alias="Nombre Proveedor")
    client_cif: str = Field(..., alias="CIF/ NIF Cliente")
    client_name: str = Field(..., alias="Nombre Cliente")
    invoice_number: str = Field(..., alias="Numero de Factura")
    invoice_date: str = Field(..., alias="Fecha de la factura")
    base_imponible: float = Field(..., alias="Base imponible")
    iva: float = Field(..., alias="IVA")
    retencion_irpf: Optional[float] = Field(..., alias="Retencion IRPF")
    total: float = Field(..., alias="TOTAL")
    iban: Optional[str] = Field(None, alias="IBAN")
    payment_method: Optional[str] = Field(None, alias="Forma de pago")

    # Helper to convert to a format suitable for CIF validation
    def to_cif_validation_format(self):
        return {
            "provider": {"name": self.provider_name, "cif": self.provider_cif},
            "client": {"name": self.client_name, "cif": self.client_cif}
        }
