"""Module for processing and visualizing NL Box1 tax data."""

import csv
import argparse
from typing import Union, List
import matplotlib.pyplot as plt

import belasting as blst


def main(
    year: int,
    incomes: Union[float, List[float]],
    zzp: bool,
    plot: bool,
    costs: Union[float, List[float]] = None):
    """Calculate Box1 tax"""

    if not isinstance(incomes, list):
        incomes = [incomes]

    if costs is not None and isinstance(costs, list):
        costs = {'total_costs': sum(costs)}    

    res = [blst.box1_tax_calculate(income, year, zzp, costs) for income in incomes]

    if res:
        keys = res[0].keys()
        with open(f'box1_tax_{year}.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(res)

        print(f"Box1 tax for {year} calculated and saved to box1_tax_{year}.csv")

    if plot and isinstance(incomes, list) and len(incomes) > 1:
        title = f'Box1 tax for {year}'
        if zzp:
            title += ' (ZZP)'

        plt.figure(figsize=(10, 6))
        plt.plot(
            [r['annual_income'] for r in res],
            [r['income_netto_monthly'] for r in res]
            )
        plt.title(title)
        plt.xlabel('Annual Income (k)')
        plt.ylabel('Net Monthly Income')
        plt.grid(True)

        plt.savefig(f'box1_tax_{year}.png')
        print(f"Plot saved to box1_tax_{year}.png")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Calculate Box1 tax')
    parser.add_argument('-y', '--year', type=int, required=True, help='Year')
    parser.add_argument('-i', '--income', type=float, nargs='+', required=True, help='Income(s)')
    parser.add_argument('-Z', '--zzp',  default=False, action='store_true', help='ZZP')
    parser.add_argument('-p', '--plot',  default=False, action='store_true', help='Plot results')
    parser.add_argument('-C', '--costs', type=float, nargs='*', help='Costs')
    args = parser.parse_args()

    main(args.year, args.income, args.zzp, args.plot, args.costs)
