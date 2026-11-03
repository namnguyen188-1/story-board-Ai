# -*- coding: utf-8 -*-
"""
Character Isolator & Appearance Disambiguator
=============================================
Ensures strict separation and zero cross-contamination of character appearance
descriptions in multi-character cinematic dramas.
"""

import re
import unicodedata
from typing import Optional, List, Dict, Any


def normalize_vn_text(text: str) -> str:
    """Removes Vietnamese tone marks and lowercases for fuzzy match comparison."""
    if not text:
        return ""
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').lower()


def extract_single_character_description(chars_text: str, target_name: str) -> str:
    """
    Extracts strictly the appearance description belonging to `target_name`
    from a multi-character description block, avoiding any attribute bleeding
    or concatenation bugs.
    """
    if not chars_text or not target_name:
        return (chars_text or "").strip()

    raw_text = str(chars_text).strip()
    if not raw_text:
        return ""

    norm_target = normalize_vn_text(target_name).strip()
    target_words = [w for w in re.split(r'\W+', norm_target) if len(w) > 1]

    # Split by newline OR by CHAR_ tag prefix OR bullet points OR bracketed role tags
    chunks = re.split(
        r'(?=(?:^|\n|\.\s+|;\s+)(?:CHAR_[A-Z0-9_]+|\[(?:PRIMARY FOCUS|SUPPORTING|REACTION|ACTOR)[^\]]*\]|[-*•]\s*|[A-Za-z0-9_\u00C0-\u1EF9\s]{2,30}:))',
        raw_text,
        flags=re.IGNORECASE
    )
    candidates = [c.strip() for c in chunks if c and c.strip()]

    # If only 1 candidate and it does NOT look like multiple CHAR_ tags
    if len(candidates) <= 1 and raw_text.count("CHAR_") <= 1:
        # Check if another character's name is in here while target is NOT
        # If target is in it, return raw_text
        if re.search(r'\b' + re.escape(norm_target) + r'\b', normalize_vn_text(raw_text)):
            return raw_text

    def clean_chunk(txt: str) -> str:
        # Remove leading punctuation and brackets
        t = re.sub(r'^[.;,\s]+', '', txt).strip()
        t = re.sub(r'^\[(?:PRIMARY FOCUS|SUPPORTING|REACTION|ACTOR)[^\]]*\]\s*', '', t, flags=re.IGNORECASE).strip()
        return t

    # Pass 1: exact target name with word boundaries
    for c in candidates:
        norm_c = normalize_vn_text(c)
        if re.search(r'\b' + re.escape(norm_target) + r'\b', norm_c):
            return clean_chunk(c)

    # Pass 2: all target words match as words
    for c in candidates:
        norm_c = normalize_vn_text(c)
        if target_words and all(re.search(r'\b' + re.escape(w) + r'\b', norm_c) for w in target_words):
            return clean_chunk(c)

    # Pass 3: prominent target words (>2 chars, excluding common pronouns like ong, ba, anh, chi, em, mr, ms)
    prominent_words = [
        w for w in target_words
        if len(w) >= 3 and w not in ('anh', 'chi', 'ong', 'ba', 'em', 'chu', 'co', 'bac')
    ]
    if prominent_words:
        for c in candidates:
            norm_c = normalize_vn_text(c)
            if any(re.search(r'\b' + re.escape(w) + r'\b', norm_c) for w in prominent_words):
                return clean_chunk(c)

    # Line-by-line fallback
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    for line in lines:
        norm_l = normalize_vn_text(line)
        if re.search(r'\b' + re.escape(norm_target) + r'\b', norm_l):
            return clean_chunk(line)
        if prominent_words and any(re.search(r'\b' + re.escape(w) + r'\b', norm_l) for w in prominent_words):
            return clean_chunk(line)

    # If raw_text contains multiple CHAR_ tags or mentions multiple characters,
    # DO NOT return the whole block blindly to prevent cross-contamination.
    if raw_text.count("CHAR_") > 1 or "\n" in raw_text:
        # Return fallback for target_name rather than corrupting with other character's face
        return f"{target_name}, authentic cinematic actor in locked wardrobe"

    return raw_text
