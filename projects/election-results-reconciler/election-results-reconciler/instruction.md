I'm running a post election audit and need help comparing two records of the same election. The official certified results and the hand entered tally sheets should match, but the tally data was typed in manually so there are probably some errors.

The official results are in `/root/official_results.csv`. Each row has a precinct, a candidate, their vote count, and how many voters are registered there.

The tally sheets are in `/root/tally_sheets.json`. Same election, same precincts and candidates, but entered by hand. Expect things like numbers formatted as 1,249, small typos in precinct names, a missing candidate row, or a vote count that's higher than the registered voters.

Compare both sources and write a report to `/root/audit_report.json`. For each discrepancy, include:

1. `precinct` and `candidate`, set candidate to `null` if the whole precinct is missing
2. `discrepancy_type`: `vote_count_mismatch`, `impossible_value` when tally votes exceed registered voters, `candidate_missing`, or `precinct_missing`. A missing precinct is one entry, not one per candidate.
3. `severity`: `low` for differences of 10 or under, `medium` for 11 to 100, `high` for over 100 or any missing/impossible issue
4. `official_votes`, `tally_votes`, and `difference`, using `null` where a value doesn't exist

Also include a `summary` section with total precincts in each source, how many matched, how many had at least one issue, total discrepancy count, and a breakdown by severity and by type.

Use Python with only the standard library. Use fuzzy matching to align precinct names between the two sources. Don't modify the input files.

Success criteria: `/root/audit_report.json` exists, is valid JSON, and every discrepancy has the correct type, severity, vote counts, and difference.