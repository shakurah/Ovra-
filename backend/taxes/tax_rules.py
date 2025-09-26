# tax_rules.py

class TaxRuleStub:
    """
    Placeholder for future tax calculations.
    Currently supports VAT, deductions, and Form 303 reference.
    """

    VAT_RATE = 0.21  # example rate 21%

    def __init__(self):
        # Future: store invoices, amounts, deductions, etc.
        self.transactions = []

    def calculate_vat(self, amount):
        """
        Placeholder for VAT calculation.
        """
        # TODO: implement proper VAT calculation
        return None

    def apply_deductions(self, amount):
        """
        Placeholder for deductions.
        """
        # TODO: implement deductions logic
        return amount

    def generate_form_303(self):
        """
        Placeholder to generate data for Form 303.
        """
        # TODO: return data in required format
        return {}
