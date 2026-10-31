"""
Question scope guard (NFR-07).

Runs before retrieval. Refuses questions that are obscene or that ask about the application itself
(credentials, server or database details, other users' data, the assistant's own instructions). Off-topic
questions in general are left to the relevance gate (RAG_MIN_SIMILARITY_SCORE), which already refuses them.

A flagged term is ignored when it also occurs in the document text, so questions about papers that study
these topics (offensive language, password security, prompt injection) still reach retrieval.
"""

import re
import unicodedata
from typing import Iterable, List, Optional, Tuple

# Whole-word obscene or sexual terms (lower case; matched with word boundaries, plural/-ing forms allowed)
OBSCENE_TERMS = [
    "fuck", "fucking", "fucker", "motherfucker", "shit", "bullshit", "bitch", "bastard", "asshole", "dickhead",
    "cunt", "slut", "whore", "porn", "porno", "pornography", "nude", "nudes", "blowjob", "handjob", "dildo",
    "horny", "masturbate", "masturbation", "orgasm", "penis", "vagina", "boobs", "tits", "cock", "pussy",
    "rape", "nigger", "nigga", "faggot", "retard",
]

# App-sensitive phrases (regex, lower case). Each is a request about the system, its secrets or other users.
APP_SENSITIVE_PATTERNS = [
    r"\bpass(?:word|words|code|phrase)s?\b",
    r"\bapi[\s_-]?keys?\b",
    r"\bsecret[\s_-]?keys?\b",
    r"\b(?:access|refresh|auth|bearer|jwt)[\s_-]?tokens?\b",
    r"\bcredentials?\b",
    r"\blog[\s-]?in (?:details|info|information)\b",
    r"\badmin(?:istrator)? (?:account|password|panel|access|user)s?\b",
    r"\bdatabase (?:password|credentials|connection|dump|schema|tables?|contents|url|host)\b",
    r"\b(?:server|backend|host) (?:config(?:uration)?|ip|address|settings|environment|logs?)\b",
    r"(?:^|\s)\.env\b",
    r"\benvironment variables?\b",
    r"\bother users?(?:'s|s')?\b",
    r"\b(?:another|someone else'?s?|other people'?s?) (?:user|account|documents?|files?|papers?|library|libraries)\b",
    r"\b(?:list|show|give me|tell me) (?:all |the )?(?:users|accounts|usernames|emails)\b",
    r"\bsystem prompt\b",
    r"\byour (?:instructions|prompt|system prompt|rules|guidelines|configuration)\b",
    r"\bignore (?:all |any |the )?(?:previous|prior|above|earlier) (?:instructions|prompts?|rules)\b",
    r"\bjailbreak\b",
    r"\bdeveloper mode\b",
]

_OBSCENE_RE = re.compile(r"\b(" + "|".join(re.escape(t) for t in OBSCENE_TERMS) + r")(?:s|es|ing|ed)?\b")
_APP_RES = [re.compile(p) for p in APP_SENSITIVE_PATTERNS]


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    return re.sub(r"\s+", " ", text).strip()


def _flags(question: str) -> List[Tuple[str, str]]:
    """[(category, matched text)] for every flagged term in the question."""
    q = _normalise(question)
    found = [("obscene", m.group(0)) for m in _OBSCENE_RE.finditer(q)]
    for rx in _APP_RES:
        found += [("app_sensitive", m.group(0).strip()) for m in rx.finditer(q)]
    return found


def screen_question(question: str, document_texts: Optional[Iterable[str]] = None) -> Optional[str]:
    """
    Returns the refusal reason ("obscene" or "app_sensitive") or None when the question may proceed.
    A flagged term that also occurs in the document text is not counted.
    """
    flags = _flags(question)
    if not flags:
        return None
    doc = _normalise(" ".join(document_texts)) if document_texts is not None else ""
    for category, term in flags:
        if not doc or term not in doc:
            return category
    return None
