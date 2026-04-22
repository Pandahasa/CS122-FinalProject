import argparse
import os
from typing import Any, Dict, Optional

from data_collection import collect_course_data


# This function returns the course folder based on the first collected CSV path.
def _resolve_course_dir(written_files: list[dict[str, str]]) -> Optional[str]:
    if not written_files:
        return None

    first_path = written_files[0].get("file", "")
    if not first_path:
        return None

    return os.path.dirname(first_path)


# This function runs collection then visualization using passed parameters only.
def run_pipeline(
    course_name: str,
    country: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 1,
) -> Dict[str, Any]:
    if not course_name or not course_name.strip():
        raise ValueError("course_name is required")

    written_files = collect_course_data(
        name=course_name.strip(),
        country=country,
        state=state,
        limit=limit,
    )

    course_dir = _resolve_course_dir(written_files)
    if not course_dir:
        return {
            "status": "no-results",
            "course_name": course_name,
            "written_files": written_files,
            "message": "No course data was collected for the provided search.",
        }

    return {
        "status": "ok",
        "course_name": course_name,
        "course_dir": course_dir,
        "written_files": written_files,
    }


# This function provides an optional CLI wrapper that accepts arguments without prompting.
def main() -> None:
    parser = argparse.ArgumentParser(description="Run golf data collection pipeline")
    parser.add_argument("course_name", help="Course name to search for")
    parser.add_argument("--country", default=None, help="Country filter for search")
    parser.add_argument("--state", default=None, help="State filter for search")
    parser.add_argument("--limit", type=int, default=1, help="Maximum courses to process")
    args = parser.parse_args()

    result = run_pipeline(
        course_name=args.course_name,
        country=args.country,
        state=args.state,
        limit=args.limit,
    )

    print(result)


if __name__ == "__main__":
    main()
