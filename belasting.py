"""Module for Dutch Box 1 tax calculations."""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


def load_box1(year: int, json_file_path: str = 'box1.json') -> Dict[str, Any]:
    """Loads the Box 1 tax configuration from a JSON file.

    Args:
        year: The tax year to load.
        json_file_path: Path to the JSON configuration file.

    Returns:
        A dictionary containing the tax configuration for the specified year.

    Raises:
        ValueError: If the specified year is not found in the configuration.
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for config in data:
        if config.get('year') == year:
            return config
            
    raise ValueError(f"Data for year {year} not found in {json_file_path}")


@dataclass
class TaxCredit:
    """Represents a specific tax credit and its computed amount."""
    name: str
    amount: float = 0.0


class IncomeTax:
    """Computes the annual Dutch income tax (Box 1) and applicable tax credits."""

    def __init__(
        self,
        box1: Dict[str, Any],
        income: float,
        labour_income: Optional[float] = None,
    ):
        """Initializes the IncomeTax calculator.
        
        Args:
            box1: Tax configuration settings for Box 1.
            income: Total taxable income base.
            labour_income: Income specifically derived from labour (affects arbeidskorting).
        """
        self.box1 = box1
        self.income = float(income)
        self.labour_income = float(labour_income) if labour_income is not None else None

    @property
    def tax_credits(self) -> List[TaxCredit]:
        """Calculates and returns the list of applicable tax credits."""
        applied_credits = []

        for tax_credit_config in self.box1.get('tax_credits', []):
            # Each item in 'tax_credits' is expected to be a dict with a single key-value pair
            name, thresholds = next(iter(tax_credit_config.items()))
            tax_credit = TaxCredit(name=name)

            # Determine the income basis for this specific credit
            income_base = self.income
            if self.labour_income is not None and name == 'arbeidskorting':
                income_base = self.labour_income

            lower_bound = 0.0
            for bracket in thresholds:
                if income_base <= bracket['threshold']:
                    tax_credit.amount = max(
                        0.0, (income_base - lower_bound) * bracket['rate'] + bracket['bias']
                    )
                    break
                lower_bound = bracket['threshold']

            applied_credits.append(tax_credit)

        return applied_credits

    @property
    def total_tax_credit(self) -> float:
        """The total amount of all calculated tax credits."""
        return sum(tc.amount for tc in self.tax_credits)

    @property
    def income_tax(self) -> float:
        """Annual income tax calculated before applying any tax credits."""
        income_tax = 0.0
        lower_bound = 0.0

        for bracket in self.box1.get('box1_rates', []):
            upper_bound = min(self.income, bracket['threshold'])
            if upper_bound > lower_bound:
                income_tax += (upper_bound - lower_bound) * bracket['rate']
            if upper_bound == self.income:
                break
            lower_bound = upper_bound

        return income_tax

    @property
    def income_tax_netto(self) -> float:
        """Total net income tax to be paid after deducting tax credits."""
        # Tax cannot be negative
        return max(0.0, self.income_tax - self.total_tax_credit)


def box1_tax_calculate(
    year: int,
    **kwargs
) -> Dict[str, Any]:
    """Calculates Box 1 taxes for an individual.
    
    Args:
        year: The tax year.
        annual_income: Total annual gross income, or a list of separate income streams.
        is_arbeid: List of booleans corresponding to `annual_income` denoting 
                   if a stream is labour income. Required if `annual_income` is a list.
        property_price: The WOZ value of the property owned, if applicable.
        
    Returns:
        A dictionary containing the detailed breakdown of tax calculations.
    """
    box1_config = load_box1(year)

    annual_income = kwargs.get('annual_income', 0.0)
    is_arbeid = kwargs.get('is_arbeid', None)
    property_price = kwargs.get('property_price', None)

    total_income = 0.0
    labour_income = None

    if isinstance(annual_income, list):
        if not is_arbeid or len(annual_income) != len(is_arbeid):
            raise ValueError(
                "When 'annual_income' is a list, 'is_arbeid' must be"
                " provided with the same length.")

        labour_income = sum(income for income, is_lab in zip(annual_income, is_arbeid) if is_lab)
        total_income = sum(annual_income)
    else:
        total_income = float(annual_income)

    # Property tax (eigenwoningforfait) added to the tax base
    eigenwoningforfait = 0.0
    if property_price and 'eigenwoningforfait' in box1_config:
        for bracket in box1_config['eigenwoningforfait']:
            if property_price <= bracket['threshold']:
                eigenwoningforfait = property_price * bracket['rate']
                break

        # Deduct the mortgage interest deduction rate if present
        if 'eigenwoning_aftrek' in box1_config:
            eigenwoningforfait *= (1.0 - box1_config['eigenwoning_aftrek']['rate'])

    total_tax_base = total_income + eigenwoningforfait

    tax_calculator = IncomeTax(
        box1=box1_config,
        income=total_tax_base,
        labour_income=labour_income
    )

    box1_tax_netto = tax_calculator.income_tax_netto
    income_netto = total_income - box1_tax_netto

    # Extract specific tax credits for reporting
    tax_credits = tax_calculator.tax_credits
    arbeidskorting = sum(tc.amount for tc in tax_credits if tc.name == 'arbeidskorting')
    general_tax_credit = sum(
        tc.amount for tc in tax_credits if tc.name in (
            'algeemene_heffingskorting', 'algemene_heffingskorting')
    )

    # Calculate effective tax rate safely
    effective_rate = (box1_tax_netto / total_income) if total_income > 0 else 0.0

    return {
        'year': year,
        'annual_income': sum(annual_income) if isinstance(annual_income, list) else annual_income,
        'tax_base': round(total_tax_base, 2),
        'arbeidskorting': round(arbeidskorting, 2),
        'algeemene_korting': round(general_tax_credit, 2),
        'total_tax_korting': round(tax_calculator.total_tax_credit, 2),
        'box1_tax': round(tax_calculator.income_tax, 2),
        'box1_tax_netto': round(box1_tax_netto, 2),
        'effective_tax_rate': f'{effective_rate:.2%}',
        'income_netto': round(income_netto, 2),
        'income_netto_monthly': round(income_netto / 12, 2)
    }


# def zzp_box1_tax_calculate(
#     year: int,
#     annual_income: Union[float, List[float]] = 0.0,
#     is_arbeid: Optional[List[bool]] = None,
#     property_price: Optional[float] = None,
#     zzp: bool = False,
#     costs: Optional[Dict[str, float]] = None,
#     apply_zvw: bool = False,
#     **kwargs
# ) -> Dict[str, Any]:
#     """Calculates Box 1 taxes specifically handling ZZP (freelancer) deductions and costs.
    
#     Args:
#         year: The tax year.
#         annual_income: Total annual gross income, or a list of separate income streams.
#         is_arbeid: List of booleans corresponding to `annual_income` denoting if a stream is labour income.
#         property_price: The WOZ value of the property owned, if applicable.
#         zzp: Whether the taxpayer qualifies for ZZP deductions.
#         costs: A dictionary mapping expense names to their values.
#         apply_zvw: Whether to calculate and deduct the Zorgverzekeringswet (Zvw) contribution.
        
#     Returns:
#         A dictionary containing the detailed breakdown of ZZP tax calculations.
#     """
#     box1_config = load_box1(year)
    
#     total_income = 0.0
#     labour_income = 0.0

#     if isinstance(annual_income, list):
#         if not is_arbeid or len(annual_income) != len(is_arbeid):
#             raise ValueError("When 'annual_income' is a list, 'is_arbeid' must be provided with the same length.")

#         labour_income = sum(income for income, is_lab in zip(annual_income, is_arbeid) if is_lab)
#         total_income = sum(annual_income)
#     else:
#         total_income = float(annual_income)
#         labour_income = total_income

#     # Property tax (eigenwoningforfait) added to the tax base
#     eigenwoningforfait = 0.0
#     if property_price and 'eigenwoningforfait' in box1_config:
#         for bracket in box1_config['eigenwoningforfait']:
#             if property_price <= bracket['threshold']:
#                 eigenwoningforfait = property_price * bracket['rate']
#                 break
        
#         if 'eigenwoning_aftrek' in box1_config:
#             eigenwoningforfait *= (1.0 - box1_config['eigenwoning_aftrek']['rate'])

#     tax_base = total_income + eigenwoningforfait

#     # Reduce tax base by business costs
#     total_cost = sum(costs.values()) if costs else 0.0
#     tax_base -= total_cost

#     # Apply ZZP deductions (e.g., zelfstandigenaftrek) and MKB profit exemption
#     total_deduction = 0.0
#     if zzp:
#         total_deduction = sum(d['amount'] for d in box1_config.get('tax_deductions', []))
        
#     tax_base -= total_deduction
    
#     if zzp and 'mkb_winstvrijstelling' in box1_config:
#         tax_base *= (1.0 - box1_config['mkb_winstvrijstelling']['rate'])

#     # Tax base cannot be negative after deductions
#     tax_base = max(0.0, tax_base)

#     # Apply Zorgverzekeringswet (Health insurance contribution)
#     health_insurance = 0.0
#     if apply_zvw and 'zorgverzekeringswet' in box1_config:
#         zvw = box1_config['zorgverzekeringswet']
#         # Health insurance calculated over taxable base (up to maximum income threshold)
#         health_insurance = min(tax_base, zvw['max_income']) * zvw['rate']

#     tax_calculator = IncomeTax(
#         box1=box1_config,
#         income=tax_base,
#         labour_income=labour_income,
#         costs=costs,
#         zzp=zzp
#     )

#     box1_tax_netto = tax_calculator.income_tax_netto
#     income_netto = total_income - total_cost - box1_tax_netto - health_insurance

#     # Extract specific tax credits for reporting
#     tax_credits = tax_calculator.tax_credits
#     arbeidskorting = sum(tc.amount for tc in tax_credits if tc.name == 'arbeidskorting')
#     # Use tuple matching in case of typo in JSON
#     general_tax_credit = sum(tc.amount for tc in tax_credits if tc.name in ('algeemene_heffingskorting', 'algemene_heffingskorting'))
    
#     # Calculate effective tax rate safely
#     effective_rate = (box1_tax_netto / tax_base) if tax_base > 0 else 0.0

#     return {
#         'year': year,
#         'zzp': zzp,
#         'annual_income': annual_income,
#         'total_cost': round(total_cost, 2),
#         'zzp_deduction': round(total_deduction, 2),
#         'tax_base': round(tax_base, 2),
#         'arbeidskorting': round(arbeidskorting, 2),
#         'algeemene_korting': round(general_tax_credit, 2),
#         'total_tax_korting': round(tax_calculator.total_tax_credit, 2),
#         'box1_tax': round(tax_calculator.income_tax, 2),
#         'box1_tax_netto': round(box1_tax_netto, 2),
#         'effective_tax_rate': f'{effective_rate:.2%}',
#         'health_insurance': round(health_insurance, 2),
#         'health_insurance_monthly': round(health_insurance / 12, 2),
#         'income_netto': round(income_netto, 2),
#         'income_netto_monthly': round(income_netto / 12, 2)
#     }