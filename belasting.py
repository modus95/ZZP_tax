"""example"""
import json
from dataclasses import dataclass


def load_box1(json_file_path: str, year: int) -> dict:
    """Load Box1 tax config from JSON file"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data =  json.load(f)

    for d in data:
        if d['year'] == year:
            return d
    raise ValueError(f"Data for year {year} not found in {json_file_path}")


@dataclass
class Cost:
    """Business Cost"""
    name: str
    amount: float

@dataclass
class TaxDeduction:
    """Tax deduction"""
    name: str
    amount: float


@dataclass
class TaxCredit:
    """Tax Credit"""
    name: str
    amount: float=0.0


class IncomeTax():
    """Annual NL income tax (Box1)"""
    def __init__(self, box1: dict):
        self.box1 = box1
        self.tax_base = 0.0
        self.tax_credits = []
        self.total_tax_credit_ = 0.0
        self.income_tax = 0.0
        self.results = {}


    def _reset(self):
        """Reset internal state for a new calculation"""
        self.tax_base = 0.0
        self.tax_credits = []
        self.total_tax_credit_ = 0.0
        self.income_tax = 0.0
        self.results = {}


    def _tax_credits(self):
        """Calculate tax credits based on the tax base and Box1 credit rates"""

        for tax in self.box1['tax_credits']:
            name, thrs_list = next(iter(tax.items()))
            tc = TaxCredit(name=name)

            lb = 0
            for d in thrs_list:
                if self.tax_base <= d['threshold'] :
                    tc.amount = (self.tax_base - lb) * d['rate'] + d['bias']
                    break
                lb = d['threshold']

            self.tax_credits.append(tc)


    def _get_income_tax(self):
        """Calculate annual income tax"""

        lb = 0
        for d in self.box1['box1_rates']:
            ub = min(self.tax_base, d['threshold'])
            self.income_tax += (ub - lb) * d['rate']
            if ub == self.tax_base:
                break
            lb = ub

    def calculate(self, annual_income: float):
        """Calculate the annual income tax, credits, and net income breakdown"""

        self._reset()

        self.tax_base = annual_income

        # Income tax without korting (self.income_tax)
        self._get_income_tax()

        # Tax credits
        self._tax_credits()
        self.total_tax_credit_ = sum(tc.amount for tc in self.tax_credits)

        # Final income tax corrected by tax credits
        self.income_tax -= self.total_tax_credit_

        self.results = {
            'annual_income': annual_income,
            'tax_base': self.tax_base,
            'total_tax_credit': self.total_tax_credit_,
            'income_tax': self.income_tax,
            'effective_tax_rate': self.income_tax / self.tax_base,
            'income_netto': annual_income - self.income_tax,
            'income_netto_monthly': (annual_income - self.income_tax) / 12,
            }

        return self.results



# -----------------------


#     def __init__(self, cfg: dict):
#         self.cfg = cfg
#         self.income_tax = 0.0
#         self.tax_base = 0.0
#         self.costs = []
#         self.deductions = []
#         self.tax_credits = []
#         self.total_tax_credit_ = 0.0
#         self.base_income_ = 0.0
#         self.results = {}
#         self._reset()

#     def _reset(self):
#         """Reset internal state for a new calculation"""
#         self.income_tax = 0.0
#         self.tax_base = 0.0
#         self.costs = [Cost(name=d['name'], amount=d['amount']) for d in self.cfg['costs']]
#         self.deductions = [
#             TaxDeduction(
#                 name=d['name'],
#                 amount=d['amount']) for d in self.cfg['tax_deductions']]
#         self.tax_credits = []
#         self.total_tax_credit_ = 0.0
#         self.base_income_ = 0.0
#         self.results = {}


#     @property
#     def total_cost(self):
#         return sum(c.amount for c in self.costs)


#     @property
#     def total_deduction(self):
#         return sum(c.amount for c in self.deductions)


#     def _get_income_tax(self):

#         lb = 0
#         for d in self.cfg['income_tax_rates']:
#             ub = min(self.tax_base, d['threshold'])
#             self.income_tax += (ub - lb) * d['rate']
#             if ub == self.tax_base:
#                 break
#             lb = ub

    
#     def _tax_credits(self):
                
#         for tax in self.cfg['tax_credits']:
#             name, thrs_list = next(iter(tax.items()))
#             tc = TaxCredit(name=name)
            
#             lb = 0
#             for d in thrs_list:
#                 if self.tax_base <= d['threshold'] :
#                     tc.amount = (self.tax_base - lb) * d['rate'] + d['bias']
#                     break
#                 lb = d['threshold']      
            
#             self.tax_credits.append(tc)


#     def calculate(self, revenue: float):

#         self._reset()

#         self.base_income_ = revenue - self.total_cost
#         income_after_aftrek = self.base_income_ - self.total_deduction

#         self.tax_base = income_after_aftrek * (1 - self.cfg['mkb_winstvrijstelling']['rate'])
#         self._get_income_tax()   # Income tax without korting        
#         self._tax_credits()
#         self.total_tax_credit_ = sum(tc.amount for tc in self.tax_credits)

#         self.income_tax -= self.total_tax_credit_
#         self.results = {
#             'revenue': revenue,
#             'total_cost': self.total_cost,
#             'base_income': self.base_income_,
#             'total_deduction': self.total_deduction,
#             'tax_base': self.tax_base,
#             'total_tax_credit': self.total_tax_credit_,
#             'income_tax': self.income_tax,
#             'effective_tax_rate': self.income_tax / self.base_income_,
#             'income_netto': self.base_income_ - self.income_tax,
#             'income_netto_monthly': (self.base_income_ - self.income_tax) / 12,
#             }

#         return self.results
    