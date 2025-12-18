import io
import google.generativeai as genai
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8536206064:AAGvKSdcuMX8if1k9xQdVd6MoWjdOtTyvMo"
GEMINI_API_KEY = "AIzaSyCgSkXdStpyIh3MSNuHPiIc4xVBm5SaqDg"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# --- TELEGRAM FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = "សួស្តី! ខ្ញុំគឺជាជំនួយការ AI សម្រាប់សិស្ស។ តើអ្នកមានលំហាត់អ្វីចង់សួរខ្ញុំទេ? អ្នកអាចផ្ញើរូបភាពលំហាត់មកខ្ញុំបានផងដែរ! 📸"
    await update.message.reply_text(welcome_msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Show "typing..." status
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    user_input = []  # Gemini expects a list of inputs (Text + Image)
    
    # 1. Check if there is a specific text caption or just general instruction
    if update.message.caption:
        user_input.append(update.message.caption)
    elif update.message.photo:
        # If they send a photo with no text, we assume they want it solved/explained
        user_input.append("Please solve this problem or explain this image in Khmer.")

    # 2. Check if there is a Photo
    if update.message.photo:
        # Get the largest version of the photo
        photo_file = await update.message.photo[-1].get_file()
        
        # Download photo to memory (RAM) - no need to save to hard drive
        photo_bytes = await photo_file.download_as_bytearray()
        image = Image.open(io.BytesIO(photo_bytes))
        
        user_input.append(image)
        
    # 3. If it's just text (no photo)
    elif update.message.text:
        user_input.append(update.message.text)

    # --- SEND TO GEMINI ---
    system_instruction = """You are a Khmer teacher. Answer in Khmer. If an image is provided, solve the problem in the image step-by-step.

IMPORTANT FORMATTING RULES FOR TELEGRAM:
1. Do NOT use markdown tables (| --- |). Telegram doesn't support them.
2. For variation tables (តារាងអថេរភាព), use this format with Unicode box characters:

```
┌───────┬───────┬───────┬───────┐
│   x   │  -∞   │   0   │  +∞   │
├───────┼───────┼───────┼───────┤
│ f'(x) │   -   │   0   │   -   │
├───────┼───────┼───────┼───────┤
│ f(x)  │  ↘    │  max  │  ↘    │
└───────┴───────┴───────┴───────┘
```

3. Use arrows: ↗ (increasing), ↘ (decreasing), → (tends to)
4. Use symbols: ∞, ±, ², ³, √, ≤, ≥, ≠, ∈, ∉
5. Keep tables inside code blocks (```) so they display with monospace font.
6. For fractions, write as: ១/២ or use ½ ⅓ ¼ etc.
"""
    
    try:
        # Pass the list (Text + Image) to Gemini
        full_prompt = [system_instruction] + user_input
        
        response = model.generate_content(full_prompt)
        await update.message.reply_text(response.text)
        
    except Exception as e:
        print(f"ERROR: {e}")
        await update.message.reply_text("សូមអភ័យទោស មានបញ្ហាក្នុងការមើលរូបភាព។ (Error reading image)")

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    # Updated to handle both TEXT and PHOTO
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    
    print("Bot is running...")
    app.run_polling(drop_pending_updates=True)
