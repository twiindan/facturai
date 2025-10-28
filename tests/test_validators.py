# ABOUTME: This file contains unit tests for the validation logic.
# ABOUTME: It ensures that business rules are correctly enforced.

import pytest
from src.models import Invoice, Company
from src.validators import CIFConsistencyValidator

@pytest.fixture
def validator():
    """Returns a fresh instance of the validator for each test."""
    return CIFConsistencyValidator()

def test_consistent_cif_passes(validator: CIFConsistencyValidator):
    """Tests that no errors are returned for consistent CIFs."""
    invoice_data1 = {"provider": {"name": "Provider A", "cif": "B12345678"}, "client": {"name": "Client X", "cif": "A87654321"}}
    invoice_data2 = {"provider": {"name": "Provider A", "cif": "B12345678"}, "client": {"name": "Client Y", "cif": "C11111111"}}
    
    errors1 = validator.validate(invoice_data1)
    errors2 = validator.validate(invoice_data2)
    
    assert not errors1
    assert not errors2

def test_inconsistent_cif_fails(validator: CIFConsistencyValidator):
    """
    Tests that an error is returned for an inconsistent CIF.
    This test simulates two invoices with the same provider name but different CIFs.
    """
    invoice_data1 = {"provider": {"name": "Provider A", "cif": "B12345678"}, "client": {"name": "Client X", "cif": "A87654321"}}
    invoice_data2 = {"provider": {"name": "Provider A", "cif": "B87654321"}, "client": {"name": "Client Y", "cif": "C11111111"}}

    errors1 = validator.validate(invoice_data1)
    errors2 = validator.validate(invoice_data2)

    assert not errors1
    assert len(errors2) == 1
    assert "Inconsistency found for company 'Provider A'" in errors2[0]

def test_client_and_provider_inconsistency(validator: CIFConsistencyValidator):
    """
    Tests that inconsistencies are caught for both clients and providers.
    This test simulates a scenario where a company acts as both client and provider,
    and its CIF is inconsistent.
    """
    invoice_data1 = {"provider": {"name": "Company One", "cif": "111"}, "client": {"name": "Company Two", "cif": "222"}}
    invoice_data2 = {"provider": {"name": "Company Three", "cif": "333"}, "client": {"name": "Company One", "cif": "111"}}
    invoice_data3 = {"provider": {"name": "Company Two", "cif": "999"}, "client": {"name": "Company Four", "cif": "444"}} # Inconsistent client

    validator.validate(invoice_data1)
    validator.validate(invoice_data2)
    errors3 = validator.validate(invoice_data3)

    assert len(errors3) == 1
    assert "Inconsistency found for company 'Company Two'" in errors3[0]
    assert "new CIF '999' does not match existing CIF '222'" in errors3[0]

def test_multiple_inconsistencies(validator: CIFConsistencyValidator):
    """
    Tests that multiple inconsistencies in a single invoice are caught.
    This test simulates an invoice where both provider and client CIFs are inconsistent.
    """
    validator.validate({"provider": {"name": "P1", "cif": "P1_CIF"}, "client": {"name": "C1", "cif": "C1_CIF"}})
    
    invoice_with_errors = {"provider": {"name": "P1", "cif": "P1_CIF_WRONG"}, "client": {"name": "C1", "cif": "C1_CIF_WRONG"}}
    errors = validator.validate(invoice_with_errors)

    assert len(errors) == 2
