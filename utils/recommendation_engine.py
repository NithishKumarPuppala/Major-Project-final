import csv
from typing import Dict, List


def load_courses(csv_path: str) -> List[Dict[str, str]]:
    courses = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            courses.append(row)
    return courses


def recommend_courses(missing_skills: List[str], courses: List[Dict[str, str]], top_n: int = 5):
    missing_lower = {s.lower() for s in missing_skills}
    matched = []
    for course in courses:
        skill = course.get("skill", "").lower()
        if skill in missing_lower:
            matched.append(course)

    # If no direct matches, suggest popular basics.
    if not matched:
        matched = courses[: top_n * 2]

    return matched[:top_n]


def recommend_career_path(role: Dict[str, str], missing_skills: List[str]) -> str:
    if not missing_skills:
        return f"You are ready for {role['title']} roles. Focus on projects and interview prep."
    if len(missing_skills) <= 3:
        return f"Upskill in {', '.join(missing_skills)} to target {role['title']} roles."
    return f"Start with core skills for {role['title']} and build 2-3 projects to demonstrate them."

