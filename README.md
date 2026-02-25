# 💰 ZZP Tax Calculator

A Python-based tool for calculating Dutch Box 1 income tax for freelancers (ZZP - Zelfstandige zonder personeel) and regular employees in the Netherlands.

## 📖 Overview

The **ZZP Tax** project provides a set of scripts and Jupyter notebooks to estimate annual income tax, applicable tax credits, and health insurance contributions (Zvw). The tax rates, thresholds, and credits are highly configurable through JSON data files, making it simple to update for different tax years (currently supporting 2025 and 2026).

## ✨ Features

- **Box 1 Income Tax Calculation**: Accurately calculates income tax based on the progressive tax brackets.
- **ZZP Deductions**: Automatic application of *Zelfstandigenaftrek* (self-employed deduction), *Startersaftrek* (starter deduction), and *MKB-winstvrijstelling* (SME profit exemption).
- **Tax Credits**: Calculation of *Arbeidskorting* (labor tax credit) and *Algemene heffingskorting* (general tax credit) based on generated income levels.
- **Zvw Calculation**: Estimates the income-dependent health insurance contribution (*Zorgverzekeringswet*).
- **Extensible Configuration**: Tax rules are dynamically loaded from `box1.json`, allowing for seamless year-over-year updates.
- **Interactive Notebook**: Includes `zzp_tax.ipynb` for interactive data exploration, calculation, and visualization.

## 📁 General Project Structure

- `belasting.py`: Core logic module containing the `IncomeTax` class and calculation functions.
- `box1.json`: Configuration store for tax rates, brackets, deductions, and credits across different years.
- `zzp_tax.ipynb`: Jupyter Notebook for interactive testing, analysis, and plotting capabilities.
- `pyproject.toml`: Project metadata and dependency management (using `uv`).

## 📋 Requirements

- Python >= 3.12
- `jinja2` >= 3.1.6
- `matplotlib` >= 3.10.8
- `pandas` >= 3.0.1

## 🚀 Installation

This project utilizes `uv` for fast dependency management. To set up the environment locally:

```bash
# Clone the repository
git clone git@github.com:modus95/ZZP_tax.git
cd ZZP_tax

# Sync dependencies and create a virtual environment
uv sync
```

Alternatively, standard pip installation is possible:
```bash
pip install jinja2 matplotlib pandas
```

## ⚡ Quick Start
### Using the Python Module directly

You can import and use the core tax calculation function securely in your Python code:

```python
from belasting import box1_tax_calculate

# Example: Calculate 2026 tax for a ZZP professional with an €80,000 gross income
result = box1_tax_calculate(
    income=80000.0,
    year=2026,
    zzp=True,
    costs={"laptop": 1500.0, "travel": 500.0}
)

for key, value in result.items():
    print(f"{key}: {value}")
```

### Interactive Jupyter Analysis

Launch the Jupyter notebook to visualize tax implications actively:

```bash
uv run jupyter notebook zzp_tax.ipynb
```
