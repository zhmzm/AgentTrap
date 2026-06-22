"""String utility functions for test generation."""


def capitalize_words(text: str) -> str:
    return " ".join(w.capitalize() for w in text.split())


def reverse_string(text: str) -> str:
    return text[::-1]


def count_vowels(text: str) -> int:
    return sum(1 for c in text.lower() if c in "aeiou")
