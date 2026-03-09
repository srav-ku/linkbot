import re
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

pattern = re.compile(r"const finalUrl = '([^']+)'")

def extract_stream(url):
    try:
        html = requests.get(url, timeout=15).text
        match = pattern.search(html)
        if match:
            return match.group(1)
    except:
        pass
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send player links.")


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    urls = re.findall(r"https?://[^\s]+", text)

    results = []

    for url in urls:
        stream = extract_stream(url)
        if stream:
            results.append(stream)

    if results:

        links_text = "\n\n".join(results)

        message = (
            f"Links Extracted: {len(results)}\n\n"
            f"{links_text}"
        )

        await update.message.reply_text(
            message,
            reply_to_message_id=update.message.message_id
        )

    else:
        await update.message.reply_text(
            "No stream links found.",
            reply_to_message_id=update.message.message_id
        )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()


if __name__ == "__main__":
    main()