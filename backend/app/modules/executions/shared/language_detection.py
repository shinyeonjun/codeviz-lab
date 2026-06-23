from __future__ import annotations

import re
from typing import Literal


ExecutionLanguage = Literal["python", "c", "java"]

LANGUAGE_LABELS: dict[str, str] = {
    "python": "Python",
    "c": "C",
    "java": "Java",
}


def detect_source_language(source_code: str) -> ExecutionLanguage | None:
    source = _remove_string_literals(source_code)
    scores = {
        "python": _score_python(source),
        "c": _score_c(source),
        "java": _score_java(source),
    }
    detected, score = max(scores.items(), key=lambda item: item[1])
    competing_score = max(value for key, value in scores.items() if key != detected)

    if score < 3:
        return None
    if score - competing_score < 2:
        return None
    return detected  # type: ignore[return-value]


def build_language_mismatch_message(
    *,
    selected_language: str,
    detected_language: str,
) -> str:
    selected_label = LANGUAGE_LABELS.get(selected_language, selected_language)
    detected_label = LANGUAGE_LABELS.get(detected_language, detected_language)
    return (
        f"선택한 언어는 {selected_label}인데, 입력한 코드는 {detected_label} 코드로 보입니다. "
        f"실행하지 않았습니다. 언어 선택을 {detected_label}로 바꾸거나 "
        f"{selected_label} 문법에 맞게 코드를 수정해 주세요."
    )


def get_language_mismatch_message(
    *,
    selected_language: str,
    source_code: str,
) -> str | None:
    detected_language = detect_source_language(source_code)
    if detected_language is None or detected_language == selected_language:
        return None
    return build_language_mismatch_message(
        selected_language=selected_language,
        detected_language=detected_language,
    )


def _remove_string_literals(source_code: str) -> str:
    return re.sub(r"(['\"])(?:\\.|(?!\1).)*\1", '""', source_code, flags=re.DOTALL)


def _score_python(source: str) -> int:
    score = 0
    if re.search(r"^\s*def\s+[A-Za-z_]\w*\s*\([^)]*\)\s*:", source, re.MULTILINE):
        score += 4
    if re.search(r"^\s*class\s+[A-Za-z_]\w*(?:\([^)]*\))?\s*:", source, re.MULTILINE):
        score += 3
    if re.search(r"^\s*(if|elif|else|for|while|try|except|finally|with)\b.*:\s*$", source, re.MULTILINE):
        score += 3
    if re.search(r"\bfor\s+[A-Za-z_]\w*\s+in\s+", source):
        score += 2
    if re.search(r"^\s*(from\s+[A-Za-z_][\w.]*\s+import|import\s+[A-Za-z_][\w.]*)", source, re.MULTILINE):
        score += 1
    if re.search(r"\bprint\s*\(", source) and ";" not in source:
        score += 1
    if re.search(r"\b(None|True|False)\b", source):
        score += 1
    return score


def _score_c(source: str) -> int:
    score = 0
    if re.search(r"^\s*#\s*include\s*[<\"]", source, re.MULTILINE):
        score += 4
    if re.search(r"\bint\s+main\s*\([^)]*\)\s*\{", source):
        score += 3
    if re.search(r"\b(printf|scanf|malloc|calloc|realloc|free)\s*\(", source):
        score += 2
    if re.search(r"\btypedef\s+struct\b|\bstruct\s+[A-Za-z_]\w*\s*\{", source):
        score += 2
    if re.search(r"->|\bNULL\b", source):
        score += 1
    if re.search(r"^\s*#\s*define\b", source, re.MULTILINE):
        score += 1
    return score


def _score_java(source: str) -> int:
    score = 0
    if re.search(r"\bpublic\s+class\s+[A-Za-z_]\w*\b", source):
        score += 4
    elif re.search(r"\bclass\s+[A-Za-z_]\w*\s*\{", source):
        score += 3
    if re.search(r"\bpublic\s+static\s+void\s+main\s*\(\s*String\s*\[\]\s+\w+\s*\)", source):
        score += 3
    if re.search(r"\bSystem\.out\.(print|println)\s*\(", source):
        score += 2
    if re.search(r"^\s*import\s+java\.", source, re.MULTILINE):
        score += 2
    if re.search(r"\bnew\s+(?:int|long|double|String|[A-Z][A-Za-z_]\w*)\s*(?:\[|\()", source):
        score += 1
    if re.search(r"\b(ArrayList|LinkedList|HashMap|HashSet|Queue|Stack|List|Map|Set)<", source):
        score += 1
    return score
