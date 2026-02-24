"""Module for Dutch Box1 tax calculations."""

import json
from dataclasses import dataclass


def load_box1(year: int, json_file_path: str = 'box1.json') -> dict:
    """Load Box1 tax config from JSON file"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data =  json.load(f)

    for d in data:
        if d['year'] == year:
            return d
    raise ValueError(f"Data for year {year} not found in {json_file_path}")


@dataclass
class TaxCredit:
    """Tax Credit"""
    name: str
    amount: float=0.0


@dataclass
class IncomeTax:
    """Annual NL income tax (Box1)"""
    box1: dict
    tax_base: float
    costs: dict = None
    zzp: bool=False

    @property
    def tax_credits(self) -> list[TaxCredit]:
        """The list of tax credits"""
        tax_credits = []

        for tax in self.box1['tax_credits']:
            name, thrs_list = next(iter(tax.items()))
            tc = TaxCredit(name=name)

            lb = 0
            for d in thrs_list:
                if self.tax_base <= d['threshold'] :
                    tc.amount = (self.tax_base - lb) * d['rate'] + d['bias']
                    break
                lb = d['threshold']

            tax_credits.append(tc)
        return tax_credits

    @property
    def total_tax_credit(self):
        """The total amount of tax credits"""
        return sum(tc.amount for tc in self.tax_credits)

    @property
    def income_tax(self):
        """Annual income tax without tax credits"""

        income_tax, lb = 0, 0
        for d in self.box1['box1_rates']:
            ub = min(self.tax_base, d['threshold'])
            income_tax += (ub - lb) * d['rate']
            if ub == self.tax_base:
                break
            lb = ub

        return income_tax


def box1_tax_calculate(
    income: float,
    year: int,
    zzp: bool=False,
    costs: dict=None,
    apply_zvw: bool=True
):
    """Calculate Box1 tax"""
    box1 = load_box1(year)

    tax_base = income

    # Reduce tax base by costs (0 - for non-ZZP)
    total_cost = sum(v for n,v in costs.items()) if costs else 0
    tax_base -= total_cost

    # Apply ZZP deductions and MKB profit exemption
    total_deduction = sum(d['amount'] for d in box1['tax_deductions']) if zzp else 0
    tax_base -= total_deduction
    if zzp:
        tax_base = tax_base * (1 - box1['mkb_winstvrijstelling']['rate'])

    # Apply Zorgverzekeringswet (health insurance)
    zvw = box1['zorgverzekeringswet']
    health_insurance = min(tax_base, zvw['max_income']) * zvw['rate'] if apply_zvw else 0

    tax = IncomeTax(box1=box1, tax_base=tax_base)
    box1_tax_netto = tax.income_tax -  tax.total_tax_credit

    income_netto = income - box1_tax_netto - health_insurance

    return {
        'year': year,
        'zzp': zzp,
        'annual_income': income,
        'total_cost': total_cost,
        'zzp_deduction': total_deduction,
        'tax_base': round(tax_base, 2),
        'arbeidskorting': round(
            sum(tc.amount for tc in tax.tax_credits if tc.name == 'arbeidskorting'),
            2),
        'algeemene_korting': round(
            sum(tc.amount for tc in tax.tax_credits if tc.name == 'algeemene_heffingskorting'),
            2),
        'total_tax_credit': round(tax.total_tax_credit, 2),
        'box1_tax': round(tax.income_tax, 2),
        'box1_tax_netto': round(box1_tax_netto, 2),
        'effective_tax_rate': f'{box1_tax_netto / tax_base:.2%}',
        'health_insurance': round(health_insurance, 2),
        'health_insurance_monthly': round(health_insurance / 12, 2),
        'income_netto': round(income_netto, 2),
        'income_netto_monthly': round(income_netto / 12, 2)
        }
