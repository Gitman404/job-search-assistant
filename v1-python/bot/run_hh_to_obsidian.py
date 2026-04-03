import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from hh_fetch import search_hh, suggest_deadline
from state_store import is_seen, load_state, mark_seen, save_state

import json


@dataclass(frozen=True)
class ObsidianVacancy:
    company: str
    role: str
    status: str
    salary: str
    link: str
    external_id: str
    deadline: str
    source: str
    location: str = ""
    employment_type: str = ""
    parsedByBot: bool = True
    matchScore: int = 0
    createdAt: str = ""
    why: str = ""


def _sanitize_filename(name: str) -> str:
    forbidden = '<>:"/\\|?*'
    for ch in forbidden:
        name = name.replace(ch, " ")
    name = " ".join(name.split())
    return name.strip().rstrip(".")


def vacancy_to_markdown(v: ObsidianVacancy) -> str:
    created_at = v.createdAt or date.today().isoformat()
    salary_yaml = json.dumps(v.salary, ensure_ascii=False) if v.salary else ""
    lines = [
        "---",
        f"company: {v.company}",
        f"role: {v.role}",
        f"status: {v.status}",
        f"salary: {salary_yaml}".rstrip(),
        f"link: {v.link}",
        f"external_id: {v.external_id}",
        f"deadline: {v.deadline}",
        f"source: {v.source}",
        f"location: {v.location}",
        f"employment_type: {v.employment_type}",
        f"parsedByBot: {str(v.parsedByBot).lower()}",
        f"matchScore: {int(v.matchScore)}",
        f"createdAt: {created_at}",
        "---",
        "",
        "**Комментарий:**",
        "",
        "**Почему выбрано ботом:**",
        v.why or "-",
        "",
        "**Связанные заметки**",
        "[[Дашборд - Вакансии по статусу]]",
        "",
    ]
    return "\n".join(lines)


def load_config(config_path: Path) -> dict:
    return json.loads(config_path.read_text(encoding="utf-8"))


def write_note(vault_root: Path, vacancies_folder: str, v: ObsidianVacancy) -> Path:
    folder = vault_root / Path(vacancies_folder)
    folder.mkdir(parents=True, exist_ok=True)

    filename = _sanitize_filename(f"Вакансия {v.company} — {v.role} ({v.source} {v.external_id}).md")
    path = folder / filename
    path.write_text(vacancy_to_markdown(v), encoding="utf-8")
    return path


@dataclass(frozen=True)
class RunResult:
    considered: int
    created: int
    skipped: int
    rejected: int
    created_notes: list[dict]  # {path,url,company,role,score,why}
    debug_report_path: str | None


def run_with_config(cfg: dict, *, workdir: Path) -> RunResult:
    vault_root = Path(cfg["vault_root"])
    vacancies_folder = cfg["vacancies_folder"]
    default_status = cfg.get("default_status", "в_анализе")

    hh_cfg = cfg.get("hh", {})
    text = hh_cfg.get("search_text", "")
    area = int(hh_cfg.get("area", 1))
    per_page = int(hh_cfg.get("per_page", 20))
    pages = int(hh_cfg.get("pages", 1))
    only_with_salary = bool(hh_cfg.get("only_with_salary", False))
    experience_allowed = list(hh_cfg.get("experience_allowed", []))
    require_title_contains_any = [
        str(x).strip().lower()
        for x in hh_cfg.get("require_title_contains_any", [])
        if str(x).strip()
    ]
    exclude_title_contains_any = [
        str(x).strip().lower()
        for x in hh_cfg.get("exclude_title_contains_any", [])
        if str(x).strip()
    ]
    exclude_text_contains_any = [
        str(x).strip().lower()
        for x in hh_cfg.get("exclude_text_contains_any", [])
        if str(x).strip()
    ]
    title_keywords_any = [str(x).strip().lower() for x in hh_cfg.get("title_keywords_any", []) if str(x).strip()]
    bonus_keywords_any = [str(x).strip().lower() for x in hh_cfg.get("bonus_keywords_any", []) if str(x).strip()]
    prefer_office_hybrid = bool(hh_cfg.get("prefer_office_hybrid", True))
    remote_penalty = int(hh_cfg.get("remote_penalty", 0))
    min_score_to_create = int(hh_cfg.get("min_score_to_create", 0))
    debug_report = bool(hh_cfg.get("debug_report", False))

    if not text.strip():
        raise SystemExit("В config.json -> hh.search_text пустой. Укажи запрос для поиска.")
    if not vault_root.exists():
        raise SystemExit(f"vault_root не найден: {vault_root}")

    state_path = workdir / "state.json"
    state = load_state(state_path)

    created: list[Path] = []
    created_notes: list[dict] = []
    skipped = 0
    considered = 0
    rejected = 0
    debug_rows: list[dict] = []

    def score_and_explain(name: str, snippet: str, schedule_id: str) -> tuple[int, str]:
        txt_name = (name or "").lower()
        txt = (txt_name + " " + (snippet or "").lower()).strip()

        reasons: list[str] = []
        score = 0

        # Title fit
        if title_keywords_any:
            if any(k in txt_name for k in title_keywords_any):
                score += 50
                reasons.append("совпадение по целевой роли (название)")
            else:
                # не рубим насмерть: просто низкий приоритет
                score -= 10
                reasons.append("не похоже на целевую роль (название) — низкий приоритет")

        # Bonus keywords (ИИ/автоматизация/процессы)
        bonus_hits = [k for k in bonus_keywords_any if k and k in txt]
        if bonus_hits:
            score += min(30, 5 * len(bonus_hits))
            reasons.append(f"ключевые слова: {', '.join(sorted(set(bonus_hits))[:6])}")

        # Work format preference (HH schedule_id: remote / fullDay / flexible / ...)
        if prefer_office_hybrid and schedule_id == "remote":
            score -= remote_penalty
            reasons.append("удалёнка (минус к приоритету)")
        elif schedule_id:
            reasons.append(f"формат (hh.schedule): {schedule_id}")

        return score, "; ".join(reasons) if reasons else "-"

    for page in range(pages):
        items = search_hh(
            text=text,
            area=area,
            per_page=per_page,
            page=page,
            only_with_salary=only_with_salary,
        )
        for it in items:
            considered += 1
            if not it.external_id:
                continue

            # Experience filter
            if experience_allowed and it.experience_id and it.experience_id not in experience_allowed:
                if debug_report:
                    debug_rows.append(
                        {
                            "id": it.external_id,
                            "name": it.name,
                            "experience_id": it.experience_id,
                            "schedule_id": it.schedule_id,
                            "action": "reject",
                            "reason": f"experience_id={it.experience_id} not in allowed",
                            "url": it.url,
                        }
                    )
                rejected += 1
                continue

            # Mandatory "shape" filter: must mention project/проект in title to avoid garbage like "помощник по уходу"
            if require_title_contains_any:
                name_l = (it.name or "").lower()
                if not any(tok in name_l for tok in require_title_contains_any):
                    if debug_report:
                        debug_rows.append(
                            {
                                "id": it.external_id,
                                "name": it.name,
                                "experience_id": it.experience_id,
                                "schedule_id": it.schedule_id,
                                "action": "reject",
                                "reason": f"title_missing_required_tokens={require_title_contains_any}",
                                "url": it.url,
                            }
                        )
                    rejected += 1
                    continue

            # Hard exclude by title (blacklist)
            if exclude_title_contains_any:
                name_l = (it.name or "").lower()
                hit = next((w for w in exclude_title_contains_any if w in name_l), None)
                if hit:
                    if debug_report:
                        debug_rows.append(
                            {
                                "id": it.external_id,
                                "name": it.name,
                                "experience_id": it.experience_id,
                                "schedule_id": it.schedule_id,
                                "action": "reject",
                                "reason": f"title_blacklist_hit={hit}",
                                "url": it.url,
                            }
                        )
                    rejected += 1
                    continue

            # Hard exclude by "domain"/text (title + snippet + employer)
            if exclude_text_contains_any:
                blob = " ".join([(it.name or ""), (it.snippet or ""), (it.employer or "")]).lower()
                hit = next((w for w in exclude_text_contains_any if w in blob), None)
                if hit:
                    if debug_report:
                        debug_rows.append(
                            {
                                "id": it.external_id,
                                "name": it.name,
                                "experience_id": it.experience_id,
                                "schedule_id": it.schedule_id,
                                "action": "reject",
                                "reason": f"text_blacklist_hit={hit}",
                                "url": it.url,
                            }
                        )
                    rejected += 1
                    continue

            if is_seen(state, source="hh", external_id=it.external_id):
                skipped += 1
                continue

            score, why = score_and_explain(it.name, it.snippet, it.schedule_id)
            if score < min_score_to_create:
                if debug_report:
                    debug_rows.append(
                        {
                            "id": it.external_id,
                            "name": it.name,
                            "experience_id": it.experience_id,
                            "schedule_id": it.schedule_id,
                            "action": "reject",
                            "reason": f"score={score} < min_score_to_create={min_score_to_create}; {why}",
                            "url": it.url,
                        }
                    )
                rejected += 1
                continue

            ov = ObsidianVacancy(
                company=it.employer or "—",
                role=it.name or "—",
                status=default_status,
                salary=it.salary,
                link=it.url,
                external_id=it.external_id,
                deadline=suggest_deadline(3),
                source="hh",
                location=it.area,
                employment_type="",
                parsedByBot=True,
                matchScore=score,
                why=why,
            )
            p = write_note(vault_root, vacancies_folder, ov)
            created.append(p)
            created_notes.append(
                {
                    "path": str(p),
                    "url": it.url,
                    "company": ov.company,
                    "role": ov.role,
                    "score": score,
                    "why": why,
                }
            )
            mark_seen(
                state,
                source="hh",
                external_id=it.external_id,
                meta={"path": str(p), "url": it.url},
            )

    save_state(state_path, state)

    debug_path: str | None = None
    if debug_report:
        report_path = workdir / "hh_debug_report.json"
        report_path.write_text(json.dumps(debug_rows, ensure_ascii=False, indent=2), encoding="utf-8")
        debug_path = str(report_path)

    return RunResult(
        considered=considered,
        created=len(created),
        skipped=skipped,
        rejected=rejected,
        created_notes=created_notes,
        debug_report_path=debug_path,
    )


def main() -> None:
    here = Path(__file__).resolve().parent
    load_dotenv(dotenv_path=here / ".env", override=False)
    cfg = load_config(here / "config.json")
    res = run_with_config(cfg, workdir=here)

    print(
        f"Рассмотрено: {res.considered}; создано: {res.created}; пропущено (уже было): {res.skipped}; отклонено: {res.rejected}"
    )
    for item in res.created_notes[:10]:
        print(f"- {item['path']}")
    if res.created > 10:
        print(f"...и ещё {res.created - 10}")
    if res.debug_report_path:
        print(f"Debug-отчёт: {res.debug_report_path}")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    main()


