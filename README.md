# Stock Market Chatbot with RAG

A sophisticated, personalized stock market chatbot powered by OpenAI's Responses API, featuring Retrieval-Augmented Generation (RAG), user data collection, and automated email delivery.

## Features

### Layer 1: Personalized Chatbot
- **Sharp-tongued market wizard personality** - Bold, witty, and direct communication style
- **Natural conversation flow** - Asks for user information organically during chat
- **Stock market expertise** - Provides insights on stocks, trading strategies, and market trends
- **Educational focus** - Encourages learning and due diligence, not dependency

### Layer 2: RAG (Retrieval-Augmented Generation)
- **FAISS vector database** for efficient similarity search
- **OpenAI embeddings** (text-embedding-3-small) for semantic understanding
- **Knowledge base integration** - Uses external documents to enhance responses
- **Contextual retrieval** - Automatically finds relevant information for each query

### Layer 3: Data Storage
- **SQLite database** for user data storage (name, email, income)
- **Session management** - Tracks user sessions and data collection status
- **Data collection tracking** - Monitors name, email, and income collection status
- **Conversation history** - Managed by OpenAI's Conversations API (not stored locally)

### Layer 4: Structured Output Delivery
- **SendGrid email integration** - Automatically sends collected data
- **Professional HTML emails** - Well-formatted user information delivery
- **Automatic triggers** - Sends email when all data is collected

## Project Structure

```
RAG/
├── app.py                      # Streamlit frontend application
├── chatbot.py                  # Main chatbot logic with OpenAI Responses API
├── rag_system.py               # RAG system with FAISS and embeddings
├── database.py                 # SQLite database management
├── email_sender.py             # SendGrid email delivery
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create from .env.example)
├── .env.example                # Example environment configuration
├── sample_knowledge_base.txt   # Sample knowledge base for testing
├── RAG Source File.docx        # Your actual knowledge base document
├── user_data.db               # SQLite database (created automatically)
├── faiss_index.bin            # FAISS vector index (created automatically)
├── faiss_index.pkl            # FAISS metadata (created automatically)
└── chunks.pkl                 # Text chunks (created automatically)
```

## Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key
- SendGrid API key
- Verified sender email in SendGrid

### Step 1: Clone or Download
```bash
cd /Users/mac/Desktop/RAG
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
OPENAI_API_KEY=your_openai_api_key_here
SENDGRID_API_KEY=
SENDER_EMAIL=your_verified_sender@example.com
RECIPIENT_EMAIL=recipient@example.com
```

**Important Notes:**
- Get OpenAI API key from: https://platform.openai.com/api-keys
- The SendGrid API key is already provided
- **SENDER_EMAIL must be verified in SendGrid** (https://app.sendgrid.com/settings/sender_auth)
- RECIPIENT_EMAIL is where user data will be sent

### Step 4: Prepare Knowledge Base

You already have `RAG Source File.docx`. The system will automatically:
1. Extract text from the DOCX file
2. Split into chunks
3. Generate embeddings
4. Build FAISS vector index

If you want to use the sample knowledge base instead:
```bash
# The system is configured to use RAG Source File.docx
# To use sample_knowledge_base.txt, you would need to convert it to DOCX
# or modify rag_system.py to read .txt files
```

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will:
1. Open in your default browser (usually http://localhost:8501)
2. Build the FAISS index on first run (takes a few minutes)
3. Start the chatbot interface

### First-Time Setup
On first run, the system will:
- Extract text from your knowledge base document
- Create embeddings (this may take several minutes depending on document size)
- Build and save the FAISS index
- Subsequent runs will load the pre-built index (much faster)

### Using the Chatbot

1. **Start Chatting**: Type your stock market questions in the chat input
2. **Natural Data Collection**: The chatbot will naturally ask for:
   - Your name
   - Your email address
   - Your income level
3. **Track Progress**: Watch the sidebar to see data collection status
4. **Automatic Email**: When all data is collected, it's automatically sent via email

### Example Conversation Flow

```
User: Hey, what do you think about the current market?

Bot: Alright, listen up! The market's looking solid but don't get too
comfortable. We're seeing some interesting action in tech stocks...
By the way, what should I call you, market maverick?

User: Call me John

Bot: Nice to meet you, John! Now, about those tech stocks...
[Data saved: Name = John]

...later in conversation...

Bot: If you want me to send you some killer market resources, drop your email.

User: It's john@example.com

Bot: Got it! john@example.com is locked in.
[Data saved: Email = john@example.com]

...and so on...
```

## Testing Individual Components

### Test RAG System
```bash
python rag_system.py
```

### Test Database
```bash
python database.py
```

### Test Email Sender
```bash
python email_sender.py
```

### Test Chatbot
```bash
python chatbot.py
```

## SendGrid Setup

### Verify Your Sender Email
1. Go to https://app.sendgrid.com/settings/sender_auth
2. Click "Verify a Single Sender"
3. Fill in your email details
4. Check your email and click the verification link
5. Use this verified email as SENDER_EMAIL in .env

### Test SendGrid API Key
```bash
curl --request POST \
  --url https://api.sendgrid.com/v3/mail/send \
  --header "Authorization: Bearer YOUR_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{"personalizations":[{"to":[{"email":"recipient@example.com"}]}],"from":{"email":"sender@example.com"},"subject":"Test","content":[{"type":"text/plain","value":"Test"}]}'
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    name TEXT,
    email TEXT,
    income TEXT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_complete BOOLEAN DEFAULT 0
);
```

**Note:** Conversation history is managed by OpenAI's Conversations API and not stored locally. Only user data (name, email, income) is stored in the local database for email delivery purposes.

## Architecture

### Component Flow

```
User Input → Streamlit UI → Chatbot
                              ↓
                        ┌─────┴─────┐
                        ↓           ↓
                    RAG System   Database
                        ↓           ↓
                  OpenAI API   SQLite
                        ↓           ↓
                    Response    Storage
                        ↓           ↓
                    ┌───┴───────────┘
                    ↓
                Email Sender
                    ↓
                SendGrid API
```

### OpenAI Responses API Integration

The chatbot uses OpenAI's **Responses API** (not Chat Completions) which provides:
- **Stateful conversations** via Conversations API
- **Built-in function calling** for tool integration
- **Automatic context management**
- **Structured outputs**

### Function Tool: save_user_data

The chatbot uses a function tool that automatically:
1. Detects when user provides name, email, or income
2. Calls `save_user_data()` function
3. Stores data in SQLite database
4. Checks if all data is collected
5. Triggers email send when complete

## Troubleshooting

### FAISS Index Issues
If you get errors building the index:
```bash
# Delete existing files and rebuild
rm faiss_index.bin faiss_index.pkl chunks.pkl
python rag_system.py
```

### SendGrid Errors
- **403 Forbidden**: Sender email not verified
- **401 Unauthorized**: Invalid API key
- **400 Bad Request**: Check email format

### OpenAI API Errors
- **401 Unauthorized**: Invalid API key
- **429 Too Many Requests**: Rate limit exceeded, wait and retry
- **400 Bad Request**: Check your request format

### Database Locked
If SQLite database is locked:
```bash
# Close all Python processes and restart
pkill python
streamlit run app.py
```

## Customization

### Change Chatbot Personality
Edit `system_instructions` in [chatbot.py](chatbot.py:29)

### Modify Knowledge Base
Replace or update [RAG Source File.docx](RAG Source File.docx) and rebuild index

### Adjust RAG Parameters
In [rag_system.py](rag_system.py):
- `chunk_size`: Default 500 words
- `overlap`: Default 50 words
- `top_k`: Number of relevant chunks (default 3)

### Customize Email Template
Edit `format_user_data_email()` in [email_sender.py](email_sender.py:11)

## API Rate Limits

### OpenAI
- **Embeddings**: 3,000 requests/min (tier 1)
- **Responses API**: Varies by tier

### SendGrid
- **Free Plan**: 100 emails/day
- **Paid Plans**: Higher limits

## Security Notes

- **Never commit .env file** to version control
- **Keep API keys secure**
- **Use environment variables** for sensitive data
- **Validate user inputs** before storing
- **Hash email addresses** if storing long-term

## Cost Estimates

### Per Session
- **OpenAI Embeddings**: ~$0.00002 per chunk (one-time for index)
- **OpenAI Responses**: ~$0.01-0.05 per conversation
- **SendGrid**: Free for first 100 emails/day

### Monthly (100 users)
- **OpenAI**: $5-15
- **SendGrid**: Free

## Support

For issues:
1. Check this README
2. Review error messages in terminal
3. Verify environment variables
4. Test individual components
5. Check OpenAI and SendGrid status pages

## License

This project is for educational and demonstration purposes.

## Credits

- **OpenAI** - Responses API and Embeddings
- **FAISS** - Vector similarity search
- **SendGrid** - Email delivery
- **Streamlit** - Web interface

---

**Built with ❤️ for the stock market maverick community**
