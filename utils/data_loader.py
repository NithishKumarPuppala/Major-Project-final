import json
import csv
from typing import Dict, List, Tuple


def load_roles(json_path: str) -> List[Dict]:
    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data["roles"]


def load_skills(json_path: str) -> List[str]:
    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    skills = data.get("technical", []) + data.get("soft", [])
    return sorted(set(skills))


def load_job_descriptions(csv_path: str) -> Dict[str, str]:
    descriptions = {}
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            descriptions[row["role_key"]] = row["description"]
    return descriptions

