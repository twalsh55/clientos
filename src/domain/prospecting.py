from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

SIGNAL_KEYWORDS = {
    "spreadsheet": 4,
    "excel": 4,
    "csv": 3,
    "manual": 4,
    "reconciliation": 4,
    "reporting": 3,
    "workflow": 3,
    "process": 2,
    "integration": 3,
    "automation": 4,
    "admin": 3,
    "dashboard": 3,
    "ops": 2,
    "operations": 3,
    "compliance": 3,
    "email": 2,
    "pdf": 2,
    "copy paste": 4,
    "copy/paste": 4,
    "crm": 5,
    "lead": 4,
    "leads": 4,
    "follow up": 5,
    "follow-up": 5,
    "pipeline": 5,
    "prospect": 4,
    "client": 4,
    "customer": 3,
    "handoff": 4,
    "reminder": 3,
    "notes": 3,
    "notion": 3,
    "gmail": 3,
    "meeting notes": 4,
    "next action": 4,
    "next step": 3,
    "go cold": 4,
    "cold lead": 4,
    "stale": 3,
}

INTENT_KEYWORDS = {
    "looking for": 5,
    "recommend": 5,
    "any tool": 6,
    "any software": 6,
    "tool": 4,
    "software": 4,
    "alternative": 5,
    "how are you solving": 6,
    "i wish there was": 7,
    "anyone else": 3,
    "frustrated": 4,
    "pain point": 5,
    "automation": 4,
    "help": 2,
    "need": 2,
    "tracking": 4,
    "still using": 5,
    "who owns": 4,
    "forgot to follow up": 6,
}

EXCLUDE_KEYWORDS = {
    "hiring",
    "job",
    "job opening",
    "for hire",
    "meme coin",
    "sports betting",
}

NOISE_PENALTIES = {
    "launch hn": 12,
    "show hn": 10,
    "yc w": 8,
    "gemini": 8,
    "cursor ai": 8,
    "computer vision": 6,
    "robotics": 6,
    "investing": 6,
    "investor": 5,
    "earnings": 4,
    "portfolio": 5,
}

WORKFLOW_ANCHORS = {
    "spreadsheet",
    "excel",
    "csv",
    "manual",
    "crm",
    "lead",
    "follow up",
    "follow-up",
    "pipeline",
    "client",
    "handoff",
    "reminder",
    "notes",
    "notion",
    "gmail",
    "meeting notes",
    "next action",
    "next step",
}

PAIN_ANCHORS = {
    "frustrated",
    "pain point",
    "how are you solving",
    "i wish there was",
    "looking for",
    "still using",
    "forgot to follow up",
    "go cold",
    "cold lead",
    "stale",
    "need",
    "help",
}


@dataclass(frozen=True, slots=True)
class SocialPost:
    source: str
    external_id: str
    title: str
    body: str
    author: str
    permalink: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ProspectMatch:
    post: SocialPost
    matched_query: str
    score: int
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProspectTokenUsage:
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass(frozen=True, slots=True)
class ProspectDraft:
    idea: str
    assessment: str
    confidence: str
    noise_flags: tuple[str, ...] = ()


def score_social_post(post: SocialPost, matched_query: str) -> ProspectMatch | None:
    haystack = f"{post.title}\n{post.body}".lower()
    title = post.title.lower()

    if any(keyword in haystack for keyword in EXCLUDE_KEYWORDS):
        return None

    score = 0
    reasons: list[str] = []

    for keyword, weight in SIGNAL_KEYWORDS.items():
        if keyword in haystack:
            score += weight
            reasons.append(f"mentions {keyword}")

    for keyword, weight in INTENT_KEYWORDS.items():
        if keyword in haystack:
            score += weight
            reasons.append(f"shows intent via {keyword}")

    if "?" in post.title or "?" in post.body:
        score += 2
        reasons.append("asks a question")

    if matched_query.lower() in haystack:
        score += 2
        reasons.append(f"matched query {matched_query}")

    explicit_workflow_pain = _has_explicit_workflow_pain(haystack)
    if explicit_workflow_pain:
        score += 4
        reasons.append("shows explicit workflow pain")

    if _is_launch_style_noise(title, haystack) and not explicit_workflow_pain:
        reasons.append("penalized launch-style post without explicit workflow pain")
        score -= 12

    for keyword, penalty in NOISE_PENALTIES.items():
        if keyword in haystack and not explicit_workflow_pain:
            score -= penalty
            reasons.append(f"penalized noisy context {keyword}")

    deduped_reasons = tuple(dict.fromkeys(reasons))
    if score < 8:
        return None

    return ProspectMatch(
        post=post,
        matched_query=matched_query,
        score=score,
        reasons=deduped_reasons,
    )


def _has_explicit_workflow_pain(haystack: str) -> bool:
    has_workflow_anchor = any(keyword in haystack for keyword in WORKFLOW_ANCHORS)
    has_pain_anchor = any(keyword in haystack for keyword in PAIN_ANCHORS)
    return has_workflow_anchor and has_pain_anchor


def _is_launch_style_noise(title: str, haystack: str) -> bool:
    return title.startswith("show hn:") or title.startswith("launch hn:") or "show hn" in haystack or "launch hn" in haystack
