"""Text processing tools"""

import regex as re


def normalize_names(
    names: list[str],
    wordlength: int | None = None,
    maxwords: int | None = None,
):
    """Normalize a list of feature names"""
    result = []
    for n in names:
        words = re.split(r"[ \|,\._-]", n.lower().strip())

        if wordlength is not None:
            words = [w[:wordlength] for w in words]
        if maxwords is not None:
            words = words[:maxwords]

        n = "_".join(words)
        result.append(n)
    if len(set(result)) != len(result):
        raise ValueError("processed names not unique")

    return result
