import re
from typing import Dict, List, Set, Tuple

import spacy
from nltk.tokenize import wordpunct_tokenize


_NLP = None


def get_nlp():
    global _NLP
    if _NLP is None:
        try:
            _NLP = spacy.load("en_core_web_sm")
        except Exception:
            # Fallback to a blank model if the small model is not installed.
            _NLP = spacy.blank("en")
    return _NLP


def extract_skills(text: str, skill_set: Set[str]) -> List[str]:
    tokens = [t.lower() for t in wordpunct_tokenize(text)]
    text_lower = " ".join(tokens)
    found = set()

    # Match exact skill phrases from the dictionary (1-3 words).
    for skill in skill_set:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found.add(skill)

    return sorted(found)


def extract_education(text: str) -> List[str]:
    degrees = [
        "b.e", "b.tech", "b.sc", "bca", "bba",
        "m.e", "m.tech", "m.sc", "mca", "mba",
        "phd", "diploma",
    ]
    lines = _split_lines(text)
    edu = []
    for line in lines:
        line_lower = line.lower()
        if any(deg in line_lower for deg in degrees) or "university" in line_lower or "college" in line_lower:
            edu.append(line.strip())
    return _dedupe(edu)


def extract_experience(text: str) -> List[str]:
    lines = _split_lines(text)
    exp_lines = _collect_section(lines, ["experience", "work experience", "employment"])
    if exp_lines:
        return _dedupe(exp_lines)

    # Fallback: pick lines with year ranges.
    year_lines = [ln for ln in lines if re.search(r"\b(19|20)\d{2}\b", ln)]
    return _dedupe(year_lines)


def extract_projects(text: str) -> List[str]:
    lines = _split_lines(text)
    proj_lines = _collect_section(lines, ["projects", "academic projects"])
    return _dedupe(proj_lines)


def extract_entities(text: str) -> Tuple[List[str], List[str]]:
    nlp = get_nlp()
    doc = nlp(text)
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
    return _dedupe(orgs), _dedupe(dates)


def build_summary(
    text: str, skill_set: Set[str]
) -> Dict[str, List[str]]:
    skills = extract_skills(text, skill_set)
    education = extract_education(text)
    experience = extract_experience(text)
    projects = extract_projects(text)
    orgs, dates = extract_entities(text)

    return {
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects,
        "orgs": orgs,
        "dates": dates,
    }


def _split_lines(text: str) -> List[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _collect_section(lines: List[str], headings: List[str]) -> List[str]:
    collected = []
    capture = False
    for line in lines:
        line_lower = line.lower()
        if any(h in line_lower for h in headings):
            capture = True
            continue
        if capture and re.match(r"^[A-Z][A-Za-z\\s]+:$", line):
            # New section heading.
            break
        if capture:
            collected.append(line)
    return collected


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    unique = []
    for item in items:
        key = item.strip()
        if key and key not in seen:
            unique.append(key)
            seen.add(key)
    return unique

