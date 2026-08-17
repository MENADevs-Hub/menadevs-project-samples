# customer-data-cleaning-pipeline

A config-driven Python pipeline that cleans raw customer CSV exports. It loads data
against a declared schema, normalizes fields, validates them against a rule engine,
removes near-duplicate records with fuzzy matching, and writes cleaned output plus an
auditable data-quality report.

## Why this project

Raw customer exports are messy: inconsistent phone formats, malformed emails, duplicate
records, missing fields. This pipeline turns them into a clean, validated dataset while
producing an auditable report of what was rejected and why.

## Pipeline stages

```text
load → normalize → validate → deduplicate → report
```

| Stage | Module | Responsibility |
|-------|--------|----------------|
| Load | `loader.py` | Read CSV and validate the header against `config/schema.yaml` |
| Normalize | `normalizers.py` | Standardize phone (`+<digits>`), name casing, whitespace, postal code |
| Validate | `validators.py` | Apply rules from `config/validation_rules.yaml` (required, email, phone, regex, range, enum) |
| Deduplicate | `deduplicator.py` | Fuzzy/similarity dedup with a configurable threshold and blocking key |
| Report | `reporter.py` | Write `cleaned.csv`, `rejected.csv`, `duplicates.csv`, and `report.json` |

> **Stage order note:** normalization runs before validation so the rule engine always
> sees cleaned values (lowercased email, `+`-prefixed phone, collapsed whitespace).

## Installation

Requires Python 3.11 or later.

```bash
git clone https://github.com/code-corpus/customer-data-cleaning-pipeline.git
cd customer-data-cleaning-pipeline
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

```bash
python -m pipeline.cli \
    --input  data/raw/customers_raw.csv \
    --output data/output \
    --config config
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--input` | yes | — | Path to the raw customer CSV file |
| `--output` | no | — | Directory for cleaned output and reports |
| `--config` | no | `config` | Path to the configuration directory |

Running without `--output` logs the pipeline summary but does not write any files.

### Example run

```
INFO pipeline: loaded 10 rows from data/raw/customers_raw.csv
INFO pipeline: normalized 10 rows
INFO pipeline: validated rows: 5 valid, 5 rejected
INFO pipeline: deduplicated: 4 unique, 1 duplicates
INFO pipeline: summary: input=10 cleaned=4 rejected=5 duplicates=1
INFO pipeline: cleaned rows   → data/output/cleaned.csv
INFO pipeline: rejected rows  → data/output/rejected.csv
INFO pipeline: duplicates     → data/output/duplicates.csv
INFO pipeline: quality report → data/output/report.json
```

## Output files

All files are written to the directory given by `--output`. The directory is created
automatically if it does not exist. **`data/output/` is gitignored** — outputs are
runtime artifacts, not source files.

| File | Contents |
|------|----------|
| `cleaned.csv` | Rows that passed validation and deduplication, with normalized field values |
| `rejected.csv` | One row per rule violation. A customer rejected for two reasons appears twice. Extra columns: `violation_field`, `violation_rule`, `violation_code` |
| `duplicates.csv` | Rows removed as near-duplicates. Extra column: `similarity_score` |
| `report.json` | `total_input`, `cleaned`, `rejected`, `duplicates`, `quality_score` (= `cleaned / total_input`) |

## Configuration

All behavior is driven by three YAML files in `config/`.

### `config/schema.yaml`

Declares the expected columns and their types. The loader raises an error if a required
column is missing from the CSV header.

```yaml
columns:
  - name: email
    type: string
    required: true
```

Supported types: `string`, `date`, `int`, `float`.

### `config/validation_rules.yaml`

Applies named rules to individual fields after normalization.

| Rule | Behavior |
|------|----------|
| `required` | Field must be non-empty |
| `email` | Must match `user@domain.tld` pattern |
| `phone` | Digit count must be within `min_digits`–`max_digits` |
| `regex` | Value must match the given `pattern` |
| `enum` | Value must be one of the listed `values` |
| `range` | Numeric value must fall within `min`–`max` |

### `config/pipeline.yaml`

Controls normalization, deduplication, and the default output directory.

```yaml
normalization:
  phone:
    default_country_code: "1"
  name:
    title_case: true
    collapse_whitespace: true
  postal_code:
    uppercase: true

deduplication:
  blocking_key: email_domain      # group rows by email domain before comparing
  similarity_threshold: 0.9       # SequenceMatcher ratio required to flag a duplicate
  key_fields: [email, full_name]  # fields used to compute similarity

output:
  directory: data/output
```

## Project layout

```text
customer-data-cleaning-pipeline/
├── config/
│   ├── pipeline.yaml            normalization, dedup, and output settings
│   ├── schema.yaml              CSV column declarations
│   └── validation_rules.yaml   per-field validation rules
├── data/
│   ├── raw/                     synthetic dirty sample CSV
│   └── output/                  runtime outputs (gitignored)
├── src/pipeline/
│   ├── cli.py                   entry point — argument parsing and wiring
│   ├── config.py                YAML loading and schema parsing
│   ├── deduplicator.py          fuzzy deduplication
│   ├── loader.py                schema-aware CSV loader
│   ├── logging_setup.py         structured logging configuration
│   ├── normalizers.py           field normalizers
│   ├── orchestrator.py          stage chaining → PipelineResult
│   ├── reporter.py              output file writer → ReportSummary
│   └── validators.py            rule engine
├── tests/                       unit and integration tests
├── .github/workflows/ci.yml     CI: secret scan, lint, tests, build
├── .pre-commit-config.yaml      pre-commit hooks (ruff, file checks, TruffleHog)
└── pyproject.toml               build config, dependencies, ruff and pytest settings
```

## Running tests

```bash
pytest -q
```

## License

MIT — see [LICENSE](LICENSE).
