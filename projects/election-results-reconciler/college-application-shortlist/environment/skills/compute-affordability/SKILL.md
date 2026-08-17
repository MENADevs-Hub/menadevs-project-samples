---
name: compute-affordability
description: Compute 4-year net cost projections and ROI for a university. Takes tuition, scholarship, housing, city (for cost-of-living), and expected salary. Accounts for tuition/housing inflation. Use this skill when you need to compare the true financial cost of attending different universities over 4 years.
---

# Compute Affordability

Calculate a 4-year financial projection including yearly breakdown, total net cost, and ROI.

## Installation

```bash
pip install pandas
```

## Quick Start

```python
from compute_affordability import AffordabilityCalculator

calc = AffordabilityCalculator()
result = calc.run(
    annual_tuition=36068,
    scholarship_amount=12000,
    monthly_housing_cost=1050,
    city="Champaign",
    avg_starting_salary=110000,
)
print(result["total_4yr_net_cost"])   # total net cost over 4 years
print(result["roi_ratio"])            # salary / total cost
print(result["payback_years"])        # years to recoup cost
print(result["yearly_breakdown"])     # list of per-year dicts
```

## Parameters

- `annual_tuition` – Annual out-of-state tuition ($)
- `scholarship_amount` – Annual renewable scholarship ($)
- `monthly_housing_cost` – Monthly on-campus housing cost ($)
- `city` – City name for cost-of-living adjustment
- `avg_starting_salary` – Expected starting salary post-graduation ($)
- `years` – Projection length (default 4)

## Output Fields

- `yearly_breakdown` – List of per-year cost dicts (tuition, housing, living, gross, net)
- `total_4yr_net_cost` – Sum of net costs across all years
- `total_scholarship_value` – Sum of scholarship across all years
- `roi_ratio` – Starting salary ÷ total 4-year net cost
- `payback_years` – Total cost ÷ starting salary
- `col_factor` – Cost-of-living multiplier from dataset
- `median_city_rent` – Reference median 1BR rent for the city

## Built-in Assumptions

- 3% annual tuition inflation
- 2% annual housing inflation
- $1,200/year books & supplies, $2,400/year personal expenses (scaled by COL factor)
