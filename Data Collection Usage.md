# Data Collection Usage

Use the pipeline from Python (no terminal prompt required):

```python
from run_pipeline import run_pipeline

result = run_pipeline(course_name="Bandon Dunes", limit=1)
print(result["status"])
print(result["course_dir"])
print(result["written_files"])
```

Output location:
- `data/<sanitized_course_name>/`

CSV files and typical rows:
- `search_result.csv`: 1 row per matched course that is processed
- `course_overview.csv`: 1 row per processed course
- `tee_box_holes.csv`: one row per hole per tee setup (usually many rows)

For each processed course, `written_files` returns the exact CSV paths.
