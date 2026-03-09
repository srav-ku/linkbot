import re
import os
import requests
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# ────────────────────────────────────────────────
# Logging (very important on hosting platforms)
# ────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    logger.error("BOT_TOKEN environment variable is not set!")
    raise ValueError("BOT_TOKEN is required")

# More resilient pattern (allows " or ' quotes)
pattern = re.compile(r"const finalUrl\s*=\s*['\"]([^'\"]+)['\"]")

def extract_stream(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0 LinkBot"})
        r.raise_for_status()
        match = pattern.search(r.text)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        logger.warning(f"Failed to extract from {url}: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! Send me one or more player/stream links and I'll try to extract the final stream URL(s) for you."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text
    urls = re.findall(r"https?://\S+", text)

    if not urls:
        # Optional: reply only when there are URLs → reduces noise
        return

    results = []
    for url in urls:
        stream = extract_stream(url)
        if stream:
            results.append(stream)

    if results:
        links_text = "\n".join(f"• {link}" for link in results)
        msg = f"Found **{len(results)}** stream link(s):\n\n{links_text}"
        await update.message.reply_text(msg, disable_web_page_preview=True)
    else:
        await update.message.reply_text("No valid stream links found in your message.")


def main():
    if not TOKEN:
        logger.critical("Cannot start: BOT_TOKEN missing")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    # Only text messages, ignore commands
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Starting bot (polling mode)...")

    # Use allowed_updates to reduce unnecessary traffic
    app.run_polling(
        drop_pending_updates=True,   # ← very useful on restart / redeploy
        allowed_updates=Update.ALL_TYPES,  # or limit to what you need
    )


if __name__ == "__main__":
    main()
