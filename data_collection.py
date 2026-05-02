import csv
import os
import re
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

API_KEY = os.getenv("GOLF_API_KEY")
BASE_URL = os.getenv("GOLF_API_BASE_URL")
CSV_DATA_DIR = os.getenv("CSV_DATA_DIR", "data")
REQUEST_TIMEOUT = int(os.getenv("GOLF_API_TIMEOUT", "15"))


# This function validates required environment configuration values.
def _validate_config() -> bool:
    missing_vars = []
    if not API_KEY:
        missing_vars.append("GOLF_API_KEY")
    if not BASE_URL:
        missing_vars.append("GOLF_API_BASE_URL")

    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False

    return True


# This function builds a full API URL from a relative path.
def _build_url(path: str) -> str:
    return f"{BASE_URL.rstrip('/')}/{path.lstrip('/')}"


# This function makes an API request and returns parsed JSON.
def _request_json(path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    if not _validate_config():
        return None

    query_params = dict(params or {})
    headers = {"Authorization": f"Key {API_KEY}"}

    try:
        response = requests.get(
            _build_url(path),
            params=query_params,
            headers=headers or None,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        response_text = ""
        if exc.response is not None:
            response_text = (exc.response.text or "").strip()
            if len(response_text) > 500:
                response_text = response_text[:500] + "..."

        parsed = urlparse(_build_url(path))
        safe_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        print(f"Request failed for {safe_url}: HTTP {status}")
        if response_text:
            print(f"API response: {response_text}")
        return None
    except requests.exceptions.RequestException as exc:
        print(f"Request failed for {_build_url(path)}: {exc}")
        return None
    except ValueError:
        print(f"Response from {_build_url(path)} was not valid JSON")
        return None


# This function returns the first non-empty value for a list of keys.
def _pick_first(item: Dict[str, Any], keys: Iterable[str], default: Any = "") -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return default


# This function normalizes list-like or dict-like input into row dictionaries.
def _extract_list(container: Any) -> List[Dict[str, Any]]:
    if isinstance(container, list):
        return [item for item in container if isinstance(item, dict)]
    if isinstance(container, dict):
        return [container]
    return []


# This function extracts course records from a search response payload.
def _extract_search_courses(search_json: Any) -> List[Dict[str, Any]]:
    if isinstance(search_json, list):
        return [item for item in search_json if isinstance(item, dict)]

    if not isinstance(search_json, dict):
        return []

    for top_key in ("courses", "results", "data", "items"):
        top_value = search_json.get(top_key)
        if isinstance(top_value, list):
            return [item for item in top_value if isinstance(item, dict)]
        if isinstance(top_value, dict):
            for nested_key in ("courses", "results", "data", "items"):
                nested_value = top_value.get(nested_key)
                if isinstance(nested_value, list):
                    return [item for item in nested_value if isinstance(item, dict)]

    return []


# This function finds the main course object in a course details payload.
def _extract_course_root(course_json: Any) -> Dict[str, Any]:
    if not isinstance(course_json, dict):
        return {}

    for key in ("course", "data", "result"):
        nested = course_json.get(key)
        if isinstance(nested, dict):
            return nested

    return course_json


# This function extracts tee box objects from the course payload.
def _extract_tee_boxes(course_root: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("tees", "teeBoxes", "tee_boxes"):
        tees = course_root.get(key)
        if isinstance(tees, list):
            return [tee for tee in tees if isinstance(tee, dict)]
        if isinstance(tees, dict):
            parsed_tees: List[Dict[str, Any]] = []
            for tee_group, tee_values in tees.items():
                if isinstance(tee_values, list):
                    for tee_item in tee_values:
                        if isinstance(tee_item, dict):
                            tee_row = dict(tee_item)
                            tee_row.setdefault("teeGroup", tee_group)
                            parsed_tees.append(tee_row)
            return parsed_tees
    return []


# This function extracts hole objects from a tee box payload.
def _extract_holes(tee_box: Dict[str, Any]) -> List[Dict[str, Any]]:
    holes = tee_box.get("holes")

    if isinstance(holes, list):
        return [hole for hole in holes if isinstance(hole, dict)]

    if isinstance(holes, dict):
        parsed_holes = []
        for hole_number, hole_data in holes.items():
            if isinstance(hole_data, dict):
                hole_row = dict(hole_data)
                hole_row.setdefault("holeNumber", hole_number)
                parsed_holes.append(hole_row)
        return parsed_holes

    return []


# This function converts a course name into a filesystem-safe directory name.
def _sanitize_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", (value or "").strip())
    cleaned = cleaned.strip("_")
    return cleaned or "unknown_course"


# This function safely converts a value to an integer when possible.
def _to_int(value: Any) -> Optional[int]:
    try:
        if value in (None, ""):
            return None
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


# This function safely converts a value to a float when possible.
def _to_float(value: Any) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


# This function derives missing overview metrics from tee and hole data.
def _derive_overview_from_tees(course_root: Dict[str, Any]) -> Dict[str, Any]:
    candidates: List[Dict[str, Any]] = []

    for tee_box in _extract_tee_boxes(course_root):
        tee_course_rating = _pick_first(tee_box, ("courseRating", "course_rating", "rating"), "")
        tee_slope_rating = _pick_first(tee_box, ("slopeRating", "slope_rating", "slope"), "")

        total_yardage = 0
        total_par = 0
        hole_count = 0

        for hole in _extract_holes(tee_box):
            hole_count += 1
            yardage = _to_int(_pick_first(hole, ("yardage", "yards", "distance", "distance_yards"), ""))
            par = _to_int(_pick_first(hole, ("par", "hole_par"), ""))

            if yardage is not None:
                total_yardage += yardage
            if par is not None:
                total_par += par

        if hole_count > 0:
            candidates.append({
                "hole_count": hole_count,
                "total_yardage": total_yardage,
                "total_par": total_par,
                "course_rating": tee_course_rating,
                "slope_rating": tee_slope_rating,
            })

    if not candidates:
        return {}

    # Prefer the most complete and longest playable tee setup.
    best = max(
        candidates,
        key=lambda item: (
            item["hole_count"],
            item["total_yardage"],
            _to_float(item["course_rating"]) or 0.0,
            _to_float(item["slope_rating"]) or 0.0,
        ),
    )

    return {
        "Total Yardage": best["total_yardage"] or "",
        "Par": best["total_par"] or "",
        "Course Rating": best["course_rating"] or "",
        "Slope Rating": best["slope_rating"] or "",
    }


# This function searches for courses by name with optional location filters.
def search_courses(name: str, country: Optional[str] = None, state: Optional[str] = None) -> Optional[Any]:
    if not name:
        print("Course name is required for search")
        return None

    query_params: Dict[str, Any] = {"search_query": name}
    if country:
        query_params["country"] = country
    if state:
        query_params["state"] = state

    return _request_json("v1/search", query_params)


# This function fetches detailed course information by course ID.
def get_course_details(course_id: Any) -> Optional[Any]:
    if course_id in (None, ""):
        print("Course ID is required to fetch course details")
        return None

    return _request_json(f"v1/courses/{course_id}")


# This function maps raw search response data into CSV-ready rows.
def parse_search_results(search_json: Any) -> List[Dict[str, Any]]:
    rows = []
    for course in _extract_search_courses(search_json):
        location = course.get("location") if isinstance(course.get("location"), dict) else {}
        row = {
            "Course ID": _pick_first(course, ("id", "courseId", "course_id"), ""),
            "Course Name": _pick_first(course, ("name", "courseName", "course_name"), "Unknown Course"),
            "Club Name": _pick_first(course, ("clubName", "club", "facilityName", "club_name"), ""),
            "City": _pick_first(course, ("city",), _pick_first(location, ("city",), "")),
            "State": _pick_first(course, ("state", "stateCode", "province"), _pick_first(location, ("state",), "")),
            "Country": _pick_first(course, ("country", "countryCode"), _pick_first(location, ("country",), "")),
        }
        rows.append(row)
    return rows


# This function maps raw course details into a single overview row.
def parse_course_overview(course_json: Any) -> List[Dict[str, Any]]:
    course_root = _extract_course_root(course_json)
    derived = _derive_overview_from_tees(course_root)

    total_yardage = _pick_first(course_root, ("totalYardage", "total_yardage", "yardage", "yards"), "")
    par = _pick_first(course_root, ("par", "totalPar", "total_par"), "")
    course_rating = _pick_first(course_root, ("courseRating", "course_rating", "rating"), "")
    slope_rating = _pick_first(course_root, ("slopeRating", "slope_rating", "slope"), "")

    return [{
        "Course ID": _pick_first(course_root, ("id", "courseId", "course_id"), ""),
        "Course Name": _pick_first(course_root, ("name", "courseName", "course_name"), "Unknown Course"),
        "Total Yardage": total_yardage if total_yardage not in (None, "") else derived.get("Total Yardage", ""),
        "Par": par if par not in (None, "") else derived.get("Par", ""),
        "Course Rating": course_rating if course_rating not in (None, "") else derived.get("Course Rating", ""),
        "Slope Rating": slope_rating if slope_rating not in (None, "") else derived.get("Slope Rating", ""),
    }]


# This function maps tee and hole data into CSV-ready tee box rows.
def parse_tee_box_data(course_json: Any) -> List[Dict[str, Any]]:
    course_root = _extract_course_root(course_json)
    course_name = _pick_first(course_root, ("name", "courseName", "course_name"), "Unknown Course")

    rows: List[Dict[str, Any]] = []
    for tee_box in _extract_tee_boxes(course_root):
        tee_name = _pick_first(tee_box, ("teeName", "tee_name", "name", "tee", "teeGroup"), "Unknown Tee")
        tee_color = _pick_first(tee_box, ("color", "teeColor"), "")
        if tee_color in (None, ""):
            tee_color = tee_name
        tee_course_rating = _pick_first(tee_box, ("courseRating", "course_rating", "rating"), "")
        tee_slope_rating = _pick_first(tee_box, ("slopeRating", "slope_rating", "slope"), "")

        for hole_index, hole in enumerate(_extract_holes(tee_box), start=1):
            hole_number = _pick_first(hole, ("holeNumber", "hole_number", "hole", "number"), "")
            if hole_number in (None, ""):
                hole_number = hole_index

            rows.append({
                "Course Name": course_name,
                "Tee Box Name": tee_name,
                "Tee Color": tee_color,
                "Tee Course Rating": tee_course_rating,
                "Tee Slope Rating": tee_slope_rating,
                "Hole Number": hole_number,
                "Par": _pick_first(hole, ("par", "hole_par"), ""),
                "Yardage": _pick_first(hole, ("yardage", "yards", "distance", "distance_yards"), ""),
            })

    return rows


# This function writes row dictionaries to a CSV file.
def save_to_csv(data: Any, filename: str) -> bool:
    rows = _extract_list(data)
    if not rows:
        print(f"No rows to write for {filename}")
        return False

    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)

    fieldnames: List[str] = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    try:
        with open(filename, "w", newline="", encoding="utf-8") as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=fieldnames, extrasaction="ignore")
            dict_writer.writeheader()
            dict_writer.writerows(rows)
        return True
    except OSError as exc:
        print(f"Error saving CSV {filename}: {exc}")
        return False


# This function coordinates search, fetch, parse, and CSV export steps.
def collect_course_data(
    name: str,
    country: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, str]]:
    search_json = search_courses(name=name, country=country, state=state)
    if search_json is None:
        return []

    search_rows = parse_search_results(search_json)
    if not search_rows:
        print("No courses were returned from search")
        return []

    if limit > 0:
        search_rows = search_rows[:limit]

    written_files: List[Dict[str, str]] = []

    for search_row in search_rows:
        course_name = search_row.get("Course Name", "Unknown Course")
        course_id = search_row.get("Course ID", "")
        course_dir = os.path.join(CSV_DATA_DIR, _sanitize_name(course_name))

        search_path = os.path.join(course_dir, "search_result.csv")
        if save_to_csv([search_row], search_path):
            written_files.append({"course": course_name, "file": search_path})

        if not course_id:
            continue

        details_json = get_course_details(course_id)
        if details_json is None:
            continue

        overview_rows = parse_course_overview(details_json)
        tee_rows = parse_tee_box_data(details_json)

        overview_path = os.path.join(course_dir, "course_overview.csv")
        if save_to_csv(overview_rows, overview_path):
            written_files.append({"course": course_name, "file": overview_path})

        tee_path = os.path.join(course_dir, "tee_box_holes.csv")
        if tee_rows and save_to_csv(tee_rows, tee_path):
            written_files.append({"course": course_name, "file": tee_path})

    return written_files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Collect golf course data and store it in CSV files")
    parser.add_argument("name", nargs="?", help="Course name to search for")
    parser.add_argument("--country", default=None, help="Country filter for search")
    parser.add_argument("--state", default=None, help="State filter for search")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of courses to process")
    args = parser.parse_args()

    course_name = args.name
    if not course_name:
        course_name = input("Enter course name to search for: ").strip()

    if not course_name:
        print("Course name is required")
        raise SystemExit(2)

    files = collect_course_data(
        name=course_name,
        country=args.country,
        state=args.state,
        limit=args.limit,
    )
    print(f"Completed. Wrote {len(files)} CSV file(s).")

