import html
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, filters

from config import settings
from db import (
    close_pool,
    get_items_by_category,
    get_source_status,
    get_today_items,
    init_pool,
    search_items,
)

logger = logging.getLogger(__name__)

_CATEGORY_MAP = {
    "tech":   ["tech-ai", "tech-frontend", "tech-infra", "tech-other"],
    "gaming": ["gaming"],
    "music":  ["music"],
    "films":  ["film-tv"],
}


def _fmt_item(record) -> str:
    title = html.escape(record["title"] or "")
    url = record.get("url") or ""
    summary: list[str] = record.get("summary") or []

    lines = [f"<b>{title}</b>"]
    if url:
        lines.append(url)
    for bullet in summary[:3]:
        lines.append(f"• {html.escape(str(bullet))}")
    return "\n".join(lines)


async def cmd_start(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "<b>intel-agent</b>\n\n"
        "/hoy — resumen del día\n"
        "/tech — últimas noticias tech\n"
        "/gaming — videojuegos\n"
        "/music — tendencias musicales\n"
        "/films — películas y series\n"
        "/buscar &lt;texto&gt; — búsqueda\n"
        "/estado — estado de las fuentes",
        parse_mode=ParseMode.HTML,
    )


async def cmd_hoy(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    rows = await get_today_items()
    if not rows:
        await update.message.reply_text("Aún no hay items procesados hoy.")
        return

    grouped: dict[str, list] = {}
    for r in rows:
        grouped.setdefault(r["category"], []).append(r)

    parts = [f"<b>Digest de hoy</b> — {len(rows)} items\n"]
    for cat, items in grouped.items():
        parts.append(f"\n<b>{html.escape(cat)}</b> ({len(items)})")
        for item in items[:3]:
            parts.append(f"• {html.escape(item['title'])}")
            if item.get("url"):
                parts.append(f"  {item['url']}")

    await update.message.reply_text(
        "\n".join(parts), parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


async def _send_category(update: Update, categories: list[str], label: str) -> None:
    all_rows = []
    for cat in categories:
        rows = await get_items_by_category(cat, limit=5)
        all_rows.extend(rows)

    if not all_rows:
        await update.message.reply_text(f"No hay items de {label} todavía.")
        return

    parts = [f"<b>{html.escape(label)}</b>\n"]
    for r in all_rows[:10]:
        parts.append(_fmt_item(r))
        parts.append("")

    await update.message.reply_text(
        "\n".join(parts), parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


async def cmd_tech(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_category(update, _CATEGORY_MAP["tech"], "Tech")


async def cmd_gaming(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_category(update, _CATEGORY_MAP["gaming"], "Gaming")


async def cmd_music(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_category(update, _CATEGORY_MAP["music"], "Música")


async def cmd_films(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_category(update, _CATEGORY_MAP["films"], "Películas y series")


async def cmd_buscar(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(ctx.args) if ctx.args else ""
    if not query:
        await update.message.reply_text("Uso: /buscar &lt;texto&gt;", parse_mode=ParseMode.HTML)
        return

    rows = await search_items(query)
    if not rows:
        await update.message.reply_text(f"Sin resultados para «{html.escape(query)}».", parse_mode=ParseMode.HTML)
        return

    parts = [f"<b>Resultados para «{html.escape(query)}»</b>\n"]
    for r in rows:
        parts.append(_fmt_item(r))
        parts.append("")

    await update.message.reply_text(
        "\n".join(parts), parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


async def cmd_estado(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    rows = await get_source_status()
    lines = ["<b>Estado de fuentes</b>\n"]
    for r in rows:
        icon = "✅" if r["enabled"] else "⏸"
        last = r["last_run"].strftime("%d/%m %H:%M") if r["last_run"] else "nunca"
        lines.append(f"{icon} <code>{html.escape(r['name'])}</code> — {last}")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def _post_init(app: Application) -> None:
    await init_pool()
    logger.info("DB pool ready")


async def _post_shutdown(app: Application) -> None:
    await close_pool()


def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    app = (
        Application.builder()
        .token(settings.telegram_token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )

    user_filter = (
        filters.User(user_id=settings.telegram_allowed_user_id)
        if settings.telegram_allowed_user_id
        else filters.ALL
    )

    app.add_handler(CommandHandler(["start", "help"], cmd_start, filters=user_filter))
    app.add_handler(CommandHandler("hoy",    cmd_hoy,    filters=user_filter))
    app.add_handler(CommandHandler("tech",   cmd_tech,   filters=user_filter))
    app.add_handler(CommandHandler("gaming", cmd_gaming, filters=user_filter))
    app.add_handler(CommandHandler("music",  cmd_music,  filters=user_filter))
    app.add_handler(CommandHandler("films",  cmd_films,  filters=user_filter))
    app.add_handler(CommandHandler("buscar", cmd_buscar, filters=user_filter))
    app.add_handler(CommandHandler("estado", cmd_estado, filters=user_filter))

    logger.info("Bot polling…")
    app.run_polling()


if __name__ == "__main__":
    main()
