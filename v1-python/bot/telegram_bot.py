import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from run_hh_to_obsidian import load_config, run_with_config


def _env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise SystemExit(f"Не задана переменная окружения {name}")
    return v


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Я бот мониторинга вакансий.\n"
        "Команды:\n"
        "- /run — загрузить вакансии с HH, создать заметки в Obsidian и прислать топ-5\n"
        "- /status — показать текущие настройки (кратко)"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    here = Path(__file__).resolve().parent
    cfg = load_config(here / "config.json")
    hh = cfg.get("hh", {})
    msg = (
        f"Папка вакансий: `{cfg.get('vacancies_folder')}`\n"
        f"HH.area: `{hh.get('area')}`\n"
        f"min_score_to_create: `{hh.get('min_score_to_create')}`\n"
        f"pages x per_page: `{hh.get('pages')} x {hh.get('per_page')}`"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


def _format_digest(created_notes: list[dict]) -> str:
    if not created_notes:
        return "Новых заметок не создано."

    # top-5 by score
    top = sorted(created_notes, key=lambda x: int(x.get("score", 0)), reverse=True)[:5]
    lines = ["**Топ-5 (HH → Obsidian):**"]
    for i, it in enumerate(top, start=1):
        company = it.get("company") or "—"
        role = it.get("role") or "—"
        score = it.get("score", 0)
        url = it.get("url") or ""
        why = it.get("why") or "-"
        lines.append(f"{i}. **{role}** — {company}  (score: `{score}`)")
        if url:
            lines.append(f"   {url}")
        lines.append(f"   _{why}_")
    return "\n".join(lines)


async def cmd_run(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Запускаю HH → Obsidian… (это может занять 5–20 секунд)")

    here = Path(__file__).resolve().parent
    cfg = load_config(here / "config.json")
    res = run_with_config(cfg, workdir=here)

    digest = _format_digest(res.created_notes)
    summary = (
        f"{digest}\n\n"
        f"Итого: рассмотрено `{res.considered}`, создано `{res.created}`, отклонено `{res.rejected}`, пропущено `{res.skipped}`."
    )
    await update.message.reply_text(summary, parse_mode=ParseMode.MARKDOWN)


def main() -> None:
    here = Path(__file__).resolve().parent
    load_dotenv(dotenv_path=here / ".env", override=False)
    token = _env("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("run", cmd_run))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    main()



