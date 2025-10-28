# ABOUTME: This file contains validation logic for business rules.
# ABOUTME: It includes validators for CIF consistency across invoices.

from src.models import Invoice

class CIFConsistencyValidator:
    """Validates that a company's CIF remains consistent across all processed invoices."""

    def __init__(self):
        self.company_cif_map: dict[str, str] = {}

    def validate(self, invoice_data: dict) -> list[str]:
        """Validates the CIF consistency for the given invoice's client and provider.

        Args:
            invoice_data: A dictionary containing 'provider' and 'client' dictionaries,
                          each with 'name' and 'cif' keys.

        Returns:
            A list of error messages if inconsistencies are found, otherwise an empty list.
        """
        errors: list[str] = []

        # Validate provider
        provider_data = invoice_data.get("provider")
        if provider_data:
            self._validate_company(provider_data, errors)

        # Validate client
        client_data = invoice_data.get("client")
        if client_data:
            self._validate_company(client_data, errors)

        return errors

    def _validate_company(self, company_data: dict, errors: list[str]):
        """Helper method to validate a single company's CIF consistency."""
        company_name = company_data.get("name")
        company_cif = company_data.get("cif")

        if not company_name or not company_cif:
            # Optionally, log a warning or raise an error if name/cif are missing
            return

        if company_name in self.company_cif_map:
            if self.company_cif_map[company_name] != company_cif:
                errors.append(
                    f"Inconsistency found for company '{company_name}': "
                    f"new CIF '{company_cif}' does not match existing CIF '{self.company_cif_map[company_name]}'."
                )
        else:
            self.company_cif_map[company_name] = company_cif
