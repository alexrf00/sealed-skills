"""Output-side leak detection: lexical overlap, canaries, and embedding similarity.

Everything here runs on the provider after the model answers and before the answer
leaves the provider boundary.
"""

from __future__ import annotations

import base64
import binascii
import re
import unicodedata

import numpy as np

_WORD = re.compile(r"[a-z0-9]+(?:['’][a-z]+)?")
_B64_RUN = re.compile(r"[A-Za-z0-9+/=\s]{32,}")
_ZERO_WIDTH = re.compile(r"[​-‏⁠﻿]")


def words(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text).lower()
    return _WORD.findall(text)


def decode_obfuscations(text: str, reversals: bool = True) -> str:
    """Defender-side normalisation: undo cheap encodings an attacker may request.

    - base64 runs are decoded and appended
    - zero-width characters are removed
    - single characters or words separated by | / - / . / newlines are rejoined
    - text written backwards is appended reversed
    """
    text = _ZERO_WIDTH.sub("", text)
    extra = []
    for run in _B64_RUN.findall(text):
        compact = re.sub(r"\s+", "", run)
        compact = compact.rstrip("=")
        compact = compact[: len(compact) - len(compact) % 4]  # tolerate truncated or malformed tails
        if len(compact) < 32:
            continue
        try:
            decoded = base64.b64decode(compact, validate=False)
            s = decoded.decode("utf-8", errors="ignore")
            if sum(c.isalpha() or c.isspace() for c in s) > 0.8 * max(len(s), 1):
                extra.append(s)
        except (binascii.Error, ValueError):
            pass
    # spaced-out letters: "t h e  r u l e" -> "the rule"
    if re.search(r"(?:\b\w\b[ .|\-]){8,}", text):
        extra.append(re.sub(r"(?<=\b\w)[ .|\-](?=\w\b)", "", text))
    # word separators: "the | rule | says" -> "the rule says"
    extra.append(re.sub(r"\s*[|/•·]\s*", " ", text))
    if reversals:
        extra.append(" ".join(reversed(words(text))))
        extra.append(text[::-1])
    return "\n".join([text] + extra)


# ---------- lexical ----------

def lcs_len(a: list[str], b: list[str]) -> int:
    """Length of the longest common subsequence, bit-parallel (Hyyrö 2004)."""
    if not a or not b:
        return 0
    masks: dict[str, int] = {}
    for i, tok in enumerate(a):
        masks[tok] = masks.get(tok, 0) | (1 << i)
    full = (1 << len(a)) - 1
    v = full
    for tok in b:
        u = v & masks.get(tok, 0)
        v = ((v + u) | (v - u)) & full
    return len(a) - bin(v).count("1")


def rouge_l_recall(reference: list[str], candidate: list[str]) -> float:
    return lcs_len(reference, candidate) / max(len(reference), 1)


def longest_common_run(a: list[str], b: list[str]) -> int:
    """Longest contiguous run of words shared by a and b (binary search over n-gram sets)."""
    if not a or not b:
        return 0

    def shared(n: int) -> bool:
        grams = {tuple(a[i:i + n]) for i in range(len(a) - n + 1)}
        return any(tuple(b[i:i + n]) in grams for i in range(len(b) - n + 1))

    lo, hi = 0, min(len(a), len(b))
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if shared(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


def contains_phrase(text: str, phrase: str) -> bool:
    t, p = words(text), words(phrase)
    return longest_common_run(p, t) == len(p)


# ---------- semantic ----------

def sentence_windows(text: str, size: int = 2) -> list[str]:
    sents = [s.strip() for s in re.split(r"(?<=[.!?:])\s+|\n+", text) if len(s.strip()) > 20]
    if len(sents) <= size:
        return [" ".join(sents)] if sents else []
    return [" ".join(sents[i:i + size]) for i in range(len(sents) - size + 1)]


def max_cosine(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0:
        return 0.0
    a = a / np.linalg.norm(a, axis=1, keepdims=True)
    b = b / np.linalg.norm(b, axis=1, keepdims=True)
    return float((a @ b.T).max())


class LeakFilter:
    """Blocks a response if it reproduces the skill.

    lexical: longest shared word run >= run_threshold after de-obfuscation, or a canary appears
    semantic: max cosine(output window, skill chunk) >= sem_threshold (needs an embedder)
    """

    def __init__(self, skill_text: str, canaries: list[str], run_threshold: int = 12,
                 embedder=None, sem_threshold: float | None = None):
        self.skill_words = words(skill_text)
        self.canaries = canaries
        self.run_threshold = run_threshold
        self.embedder = embedder
        self.sem_threshold = sem_threshold
        self._skill_vecs = None
        if embedder is not None:
            self._skill_vecs = embedder(sentence_windows(skill_text, size=1))

    def lexical_score(self, output: str) -> int:
        return longest_common_run(self.skill_words, words(decode_obfuscations(output)))

    def canary_hit(self, output: str) -> bool:
        expanded = decode_obfuscations(output)
        return any(contains_phrase(expanded, c) for c in self.canaries)

    def semantic_score(self, output: str) -> float:
        if self.embedder is None:
            return 0.0
        wins = sentence_windows(output, size=1)
        if not wins:
            return 0.0
        return max_cosine(self.embedder(wins), self._skill_vecs)

    def blocks(self, output: str, use_lexical=True, use_semantic=False) -> bool:
        if use_lexical and (self.lexical_score(output) >= self.run_threshold or self.canary_hit(output)):
            return True
        if use_semantic and self.sem_threshold is not None and self.semantic_score(output) >= self.sem_threshold:
            return True
        return False
