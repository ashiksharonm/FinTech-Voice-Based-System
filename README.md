# FinTech Voice-Based System (B2B Debt Discovery)

This is an end-to-end conversational AI project built for a "Conversational Analyst" portfolio. It acts as a B2B Debt Discovery Assistant, helping enterprise clients find the right debt product (e.g., Structured Debt, Term Loans, Supply Chain Finance) based on their financial metrics like annual revenue and required loan amount.

## 🚀 Features
- **Conversational AI Agent**: Powered by LangChain, using structured output to extract financial intents and guide users through a debt discovery flow.
- **Voice Integration**: 
  - **ASR (Speech-to-Text)**: Lightning-fast voice transcription using **Groq** (`whisper-large-v3`).
  - **TTS (Text-to-Speech)**: High-quality, completely free voice synthesis using **Edge-TTS**.
- **Real-time Analytics Dashboard**: Built-in telemetry tracking user drop-off rates, intent distribution, sentiment scores, and recommended products using Plotly.
- **Microservices Architecture**: Separate backend (FastAPI) and frontend (Streamlit) services communicating over a Docker network.
- **Containerized**: Fully deployable via `docker-compose`.

## 🛠️ Technology Stack
- **Backend**: FastAPI, SQLAlchemy, LangChain, SQLite
- **Frontend**: Streamlit, Plotly, Audio-Recorder-Streamlit
- **AI Models**: OpenRouter (Text Generation), Groq API (Speech-to-Text)
- **Infrastructure**: Docker, Docker Compose

## 📦 Local Setup & Deployment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ashiksharonm/FinTech-Voice-Based-System.git
   cd FinTech-Voice-Based-System
   ```

2. **Set up Environment Variables:**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   OPENAI_API_KEY=your_openrouter_or_openai_key
   GROQ_API_KEY=your_groq_api_key
   ```

3. **Run with Docker Compose:**
   ```bash
   docker compose up --build
   ```

4. **Access the Application:**
   - **Chat Interface**: `http://localhost:8502`
   - **Backend API**: `http://localhost:8000`

## 📊 Analytics Tracking
The system automatically logs every conversation to a SQLite database. Navigate to the "Analytics Dashboard" tab in the Streamlit UI to monitor live system performance, user sentiment, and business metrics.
