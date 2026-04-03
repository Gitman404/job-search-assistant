import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class HHVacancy:
    external_id: str
    name: str
    employer: str
    url: str
    salary: str
    area: str
    published_at: str  # ISO datetime
    experience_id: str
    schedule_id: str
    snippet: str


def _http_get_json(url: str, headers: Optional[dict[str, str]] = None) -> Any:
    req = Request(url, headers=headers or {})
    with urlopen(req, timeout=30) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8"))


def _format_salary(s: Optional[dict[str, Any]]) -> str:
    if not s:
        return ""
    cur = s.get("currency") or ""
    frm = s.get("from")
    to = s.get("to")
    gross = s.get("gross")
    gross_txt = ""
    if gross is True:
        gross_txt = " (до вычета)"
    elif gross is False:
        gross_txt = " (на руки)"

    if frm and to:
        return f"{frm}-{to} {cur}{gross_txt}".strip()
    if frm:
        return f"от {frm} {cur}{gross_txt}".strip()
    if to:
        return f"до {to} {cur}{gross_txt}".strip()
    return cur.strip()


def search_hh(
    *,
    text: str,
    area: int = 1,
    per_page: int = 20,
    page: int = 0,
    only_with_salary: bool = False,
) -> list[HHVacancy]:
    """
    HH API: https://api.hh.ru/openapi/
    Поиск вакансий: GET https://api.hh.ru/vacancies
    """
    params = {
        "text": text,
        "area": area,
        "per_page": per_page,
        "page": page,
        "only_with_salary": "true" if only_with_salary else "false",
        "order_by": "publication_time",
    }
    url = "https://api.hh.ru/vacancies?" + urlencode(params)
    data = _http_get_json(url, headers={"User-Agent": "career-obsidian-bot/0.1"})

    items = data.get("items", []) or []
    out: list[HHVacancy] = []
    for it in items:
        snippet = it.get("snippet") or {}
        snippet_text = " ".join(
            [str(snippet.get("requirement") or ""), str(snippet.get("responsibility") or "")]
        ).strip()
        experience = it.get("experience") or {}
        schedule = it.get("schedule") or {}
        out.append(
            HHVacancy(
                external_id=str(it.get("id", "")),
                name=str(it.get("name", "")).strip(),
                employer=str((it.get("employer") or {}).get("name", "")).strip(),
                url=str(it.get("alternate_url", "")).strip(),
                salary=_format_salary(it.get("salary")),
                area=str((it.get("area") or {}).get("name", "")).strip(),
                published_at=str(it.get("published_at", "")).strip(),
                experience_id=str(experience.get("id", "")).strip(),
                schedule_id=str(schedule.get("id", "")).strip(),
                snippet=snippet_text,
            )
        )
    return out


def suggest_deadline(days: int = 3) -> str:
    # пока просто "сегодня", чтобы не тащить timezone-логику; позже сделаем +N дней
    # (в Obsidian дедлайн — организационный, а не "дата публикации")
    return date.today().isoformat()


