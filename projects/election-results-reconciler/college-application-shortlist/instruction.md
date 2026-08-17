## Task
I am looking for Computer Science programs. Help me build a shortlist of my top 5 universities. My budget is $40,000/year max for tuition. I need schools that guarantee at least one year of on campus housing and offer merit scholarships of $10,000 or more. I don't want to end up in the middle of nowhere, so skip any rural campuses.

I want to actually compare them properly. For each school, compute the full 4 year cost factoring in tuition inflation and housing costs, and figure out the ROI based on average starting salary for CS grads. Then build me a weighted comparison matrix so I can see how they stack up across program ranking, net cost, ROI, salary, and housing and rank them by that composite score, not just program ranking, make sure to list them.

## Rules
Use the search skills to pull real data from the bundled databases. Don't create numbers or use schools from your own knowledge.
Do not use your own math instead use the compute and matrix building skills for the financial analysis.

## Output Format (JSON file & CSV file)

- Produce a single JSON file to `/app/output/shortlist.json`, it should look like this code snippet.

```{
  "shortlist": [
    {
      "rank": 1,
      "university": "Some University",
      "state": "Ohio",
      "city": "Columbus",
      "setting": "Urban",
      "program": "Computer Science",
      "program_ranking": 10,
      "annual_tuition_out_of_state": 35000,
      "best_scholarship": "Dean Scholarship",
      "best_scholarship_amount": 12000,
      "monthly_housing_cost": 1050,
      "housing_guaranteed_years": 2,
      "has_co_op": false,
      "avg_starting_salary": 95000,
      "total_4yr_net_cost": 140000.00,
      "roi_ratio": 0.678,
      "payback_years": 1.47,
      "col_factor": 0.85,
      "yearly_breakdown": [
        {"year": 1, "tuition": 35000, "housing": 12600, "living_expenses": 3060, "gross_cost": 50660, "scholarship": 12000, "net_cost": 38660},
        {"year": 2, "tuition": 36050, "housing": 12852, "living_expenses": 3060, "gross_cost": 51962, "scholarship": 12000, "net_cost": 39962}
      ]
    }
  ],
  "criteria": {
    "program": "Computer Science",
    "max_annual_tuition": 40000,
    "min_scholarship_amount": 10000,
    "required_housing_guaranteed_years": 1,
    "excluded_settings": ["rural"],
    "weights": {
      "program_ranking": 0.30,
      "net_annual_cost": 0.25,
      "roi_ratio": 0.20,
      "avg_starting_salary": 0.15,
      "housing_guaranteed_years": 0.10
    }
  },
  "tools_called": ["search_universities", "search_programs", "search_scholarships", "search_housing", "compute_affordability", "build_comparison_matrix"]
}```

- Produce a single CSV file to `/app/output/comparison_matrix.csv`
the CSV file will conain columns for each criterion's raw value, normalized score (0–1), weighted score, plus a composite_score and rank column, one row per university and they should be sorted by composite score descending.