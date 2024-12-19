import logging
import requests
from bs4 import BeautifulSoup
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Define your keys and tokens
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Conversation states
INDUSTRY, OBJECTIVE, WEBSITE, SOCIAL_MEDIA, PPC, AUDIENCE, LOCATION = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Start command received")
    await update.message.reply_text("Welcome! What industry is your business in?")
    return INDUSTRY

async def industry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['industry'] = update.message.text.capitalize()  # Capitalize the industry name
    logging.info(f"Industry set to: {update.message.text}")
    await update.message.reply_text("What is your business objective? (e.g., lead generation, sales, etc.)")
    return OBJECTIVE

async def objective(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['objective'] = update.message.text
    logging.info(f"Objective set to: {update.message.text}")
    await update.message.reply_text("Do you have a website? If yes, please enter the URL.")
    return WEBSITE

async def website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['website'] = update.message.text.strip() or None  # Store None if empty
    logging.info(f"Website set to: {context.user_data['website']}")
    await update.message.reply_text("Do you have any social media platforms? If yes, please provide the URL.")
    return SOCIAL_MEDIA

async def social_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['social_media'] = update.message.text.strip() or None  # Store None if empty
    logging.info(f"Social media set to: {context.user_data['social_media']}")
    await update.message.reply_text("Do you use PPC campaigns? (yes/no)")
    return PPC

async def ppc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ppc'] = update.message.text.lower().strip()
    logging.info(f"PPC set to: {context.user_data['ppc']}")
    if context.user_data['ppc'] == "yes":
        await update.message.reply_text("Great! What PPC platform are you using? (e.g., Google Ads, Facebook Ads, etc.)")
    else:
        await update.message.reply_text("No worries! We can focus on other strategies. Who are you trying to reach? (e.g., young adults, professionals, etc.)")
    return AUDIENCE

async def audience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['audience'] = update.message.text.strip().capitalize()  # Capitalize the audience name
    logging.info(f"Audience set to: {context.user_data['audience']}")
    await update.message.reply_text("Where is your target location? (e.g., India, USA, etc.)")
    return LOCATION

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['location'] = update.message.text.strip().capitalize()  # Capitalize the location name
    logging.info(f"Location set to: {context.user_data['location']}")

    # Retrieve the collected user data
    industry = context.user_data.get('industry', 'Unknown')
    objective = context.user_data.get('objective', 'Unknown')
    website = context.user_data.get('website', None)  # None if not provided
    social_media = context.user_data.get('social_media', None)  # None if not provided
    ppc = context.user_data.get('ppc', 'No')
    audience = context.user_data.get('audience', 'Unknown')
    location = context.user_data.get('location', 'Unknown')

    # Generate keywords dynamically with proper capitalization
    keywords = []

    if industry and objective:
        keywords.append(f"{industry} strategies for {objective.lower()}")
    if audience and location:
        keywords.append(f"How to target {audience} in {location}")
    if ppc == "yes":
        keywords.append(f"Best PPC campaigns for {industry.lower()}")
    
    # Add website only if it's not empty or invalid
    if website and website.lower() != "no":
        keywords.append(f"Improving website traffic for {industry.lower()}: {website}")
    else:
        keywords.append(f"Improving website traffic for {industry.lower()}")
    
    # Add social media only if it's not empty or invalid
    if social_media and social_media.lower() != "no":
        keywords.append(f"Social media tips for {audience}: {social_media}")

    # Format the response based on the provided data
    if keywords:
        formatted_keywords = "\n".join([f"- {kw}" for kw in keywords if kw])  # Add bullet points and exclude empty values
        await update.message.reply_text(f"Here are some suggested keywords for your business:\n{formatted_keywords}")
    else:
        await update.message.reply_text("It seems we don't have enough data to generate keywords. Please try providing more details.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Goodbye! Have a nice day!")
    return ConversationHandler.END

async def fetch_trends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://databox.com/ppc-industry-benchmarks"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Example: Extracting the first few paragraphs or trend data points
    trends = soup.find_all('p')
    trend_data = "\n".join([trend.text for trend in trends[:5]])  # Get first 5 paragraphs as trend data
    
    await update.message.reply_text(f"Here are the latest industry trends:\n{trend_data}")

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are an expert in digital marketing."},
                  {"role": "user", "content": user_query}]
    )
    answer = response['choices'][0]['message']['content']
    await update.message.reply_text(answer)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Logging the bot startup
    logging.info("Bot is starting...")

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            INDUSTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, industry)],
            OBJECTIVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, objective)],
            WEBSITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, website)],
            SOCIAL_MEDIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, social_media)],
            PPC: [MessageHandler(filters.TEXT & ~filters.COMMAND, ppc)],
            AUDIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, audience)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('trends', fetch_trends))
    application.add_handler(CommandHandler('faq', faq))

    # Start polling the bot for new updates
    logging.info("Bot is now polling for updates...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
