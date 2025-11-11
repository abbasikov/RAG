# Quick Start Guide

Get your Stock Market Chatbot running in 5 minutes!

## Step 1: Install Dependencies (2 minutes)

```bash
cd /Users/mac/Desktop/RAG
pip install -r requirements.txt
```

## Step 2: Configure Environment (1 minute)

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```env
OPENAI_API_KEY=your_key_here
SENDGRID_API_KEY=
SENDER_EMAIL=your_verified_email@example.com
RECIPIENT_EMAIL=where_to_receive_data@example.com
```

**Critical:** Verify your sender email in SendGrid first!
👉 https://app.sendgrid.com/settings/sender_auth

## Step 3: Run the Application (2 minutes)

```bash
streamlit run app.py
```

On first run, it will:
- Extract text from your knowledge base
- Build FAISS index (takes 2-5 minutes)
- Open browser automatically

**That's it!** Start chatting with your market wizard! 🚀

## What to Expect

1. **First Message**: Chat about stock market topics
2. **Natural Questions**: Bot will ask for your name, email, income
3. **Data Tracking**: Watch sidebar for collection status
4. **Auto Email**: Receive email when all data is collected

## Quick Troubleshooting

**"Module not found"**
```bash
pip install -r requirements.txt
```

**"Invalid API key"**
- Check your .env file has correct keys
- No spaces around the = sign

**"Sender email not verified"**
- Verify sender in SendGrid dashboard
- Use exact same email in SENDER_EMAIL

**"Cannot build FAISS index"**
- Make sure "RAG Source File.docx" exists
- Check it's a valid DOCX file

## Need Help?

Check the full [README.md](README.md) for detailed documentation.

## Test It Works

After starting, try these questions:
- "What do you think about the current market?"
- "Tell me about day trading strategies"
- "How should I manage risk?"

The bot will naturally ask for your information during the conversation!
