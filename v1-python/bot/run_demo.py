import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

@dataclass(frozen=True)
class Vacancy:
    company: str
    role: str
    status: str
    salary: str
    link: str
    external_id: str
    deadline: str  # YYYY-MM-DD
    source: str
    location: str = ""
    employment_type: str = ""
    parsedByBot: bool = True
    matchScore: int = 0
    createdAt: str = ""


def _sanitize_filename(name: str) -> str:
    # Windows-safe filename
    forbidden = '<>:"/\\|?*'
    for ch in forbidden:
        name = name.replace(ch, " ")
    name = " ".join(name.split())
    return name.strip().rstrip(".")


def vacancy_to_markdown(v: Vacancy) -> str:
    created_at = v.createdAt or date.today().isoformat()
    lines = [
        "---",
        f"company: {v.company}",
        f"role: {v.role}",
        f"status: {v.status}",
        f"salary: {json.dumps(v.salary, ensure_ascii=False) if v.salary else ''}".rstrip(),
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
        "**Связанные заметки**",
        "[[Дашборд - Вакансии по статусу]]",
        "",
    ]
    return "\n".join(lines)


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_vacancy_note(vault_root: Path, vacancies_folder: str, v: Vacancy) -> Path:
    folder = vault_root / Path(vacancies_folder)
    folder.mkdir(parents=True, exist_ok=True)

    filename = _sanitize_filename(f"Вакансия {v.company} — {v.role}.md")
    path = folder / filename

    # Never overwrite existing notes in demo mode.
    if path.exists():
        base = path.stem
        i = 2
        while True:
            candidate = folder / f"{base} ({i}).md"
            if not candidate.exists():
                path = candidate
                break
            i += 1

    path.write_text(vacancy_to_markdown(v), encoding="utf-8")
    return path


def main() -> None:
    here = Path(__file__).resolve().parent
    load_dotenv(dotenv_path=here / ".env", override=False)
    cfg = load_config(here / "config.json")

    vault_root = Path(cfg["vault_root"])
    vacancies_folder = cfg["vacancies_folder"]
    default_status = cfg.get("default_status", "в_анализе")

    demo = [
        Vacancy(
            company="Демо Компания",
            role="Junior Project Manager / Assistant",
            status=default_status,
            salary="",
            link="https://example.com/vacancy/demo-1",
            external_id="demo-1",
            deadline=(date.today()).isoformat(),
            source="demo",
            location="удаленно",
            employment_type="intern",
            matchScore=78,
        ),
        Vacancy(
            company="Ещё Демо",
            role="Стажёр в клиентский сервис",
            status=default_status,
            salary="",
            link="https://example.com/vacancy/demo-2",
            external_id="demo-2",
            deadline=(date.today()).isoformat(),
            source="demo",
            location="Москва",
            employment_type="стажировка",
            matchScore=62,
        ),
    ]

    if not vault_root.exists():
        raise SystemExit(
            f"vault_root не найден: {vault_root}\n"
            "Открой config.json и укажи правильный путь (можно в формате D:/... )."
        )

    created = []
    for v in demo:
        created.append(write_vacancy_note(vault_root, vacancies_folder, v))

    print("Созданы заметки:")
    for p in created:
        print(f"- {p}")


if __name__ == "__main__":
    # Avoid PowerShell encoding weirdness in some setups
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    main()


