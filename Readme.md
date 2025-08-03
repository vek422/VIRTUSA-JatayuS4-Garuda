# AI_QUIZ - Intelligent MCQ Generation and Assessment Chatbot

## 📋 Problem Statement

**Intelligent MCQ Generation and Assessment Chatbot**

To streamline and enhance the interview process by leveraging artificial intelligence to automatically generate and administer skill-based multiple-choice questions (MCQs) through a chatbot interface.

## 🎯 Description

This project implements an AI-powered assessment platform that includes:

- **Candidate Selection Interaction**: Engages shortlisted candidates via an AI-powered chatbot
- **Automated Profile Testing**: Conducts skill assessments through interactive chatbot sessions
- **Custom MCQ Generation**: Creates tailored multiple-choice questions for relevant skills during the interview process
- **Skill-Based Reporting**: Produces detailed reports ranking candidates based on their skill performance
- **Optional Face Capture**: Ensures identity verification by capturing candidates' faces during mock tests

## 🏗️ Architecture

This application consists of:

- **Backend**: FastAPI-based REST API with PostgreSQL database
- **Frontend**: React.js with TypeScript and Vite
- **AI Integration**: OpenAI integration for intelligent question generation
- **Real-time Communication**: WebSocket support for live interactions

## 📋 Prerequisites

Before running this application, ensure you have the following installed:

- **Python**: 3.8 or higher
- **Node.js**: 16.x or higher
- **PostgreSQL**: 12 or higher
- **Redis**: 6.0 or higher (for caching and session management)
- **Celery**: For background task processing

> **Note**: Detailed package dependencies are listed in `backend/requirements.txt` and `frontend/package.json`

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd VIRTUSA-JatayuS4-Garuda
```

### 2. Database Setup

Ensure PostgreSQL is running and create the required databases:

```sql
CREATE DATABASE ai_quiz_db;
CREATE DATABASE test_persist_langgraph;
```

### 3. Backend Setup

#### 3.1 Navigate to Backend Directory

```bash
cd backend
```

#### 3.2 Create Virtual Environment

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

#### 3.3 Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3.4 Environment Configuration

Create a `.env` file in the `backend` directory with the following structure:

```env
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/ai_quiz_db
SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# OpenAI Configuration - Add your actual API key here
OPENAI_API_KEY=your_openai_api_key

# LangSmith Configuration
LANGSMITH_API_KEY=your_langsmith_api_key

# SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key

# Tavily Configuration
TAVILY_API_KEY=your_tavily_api_key

# PostgreSQL Configuration
PSQL_USERNAME=postgres
PSQL_PASSWORD=your_password
PSQL_PORT=5432
PSQL_HOST=localhost
PSQL_DATABASE_LANGGRAPH=test_persist_langgraph
```

#### 3.5 Database Initialization (Run these scripts to ensure database is properly set up)

```bash
# Setup database tables and initial data
python setup_database.py

# Validate database configuration
python validate_database.py

# Fix any database issues if they occur
python fix_database.py
```

### 4. Frontend Setup

#### 4.1 Navigate to Frontend Directory

```bash
cd ../frontend
```

#### 4.2 Install Dependencies

```bash
npm install
```

#### 4.3 Environment Configuration

Create a `.env` file in the `frontend` directory based on `.env.example`:

```env
VITE_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 5. Redis Setup

Ensure Redis server is running:

```bash
# On Windows (if Redis is installed)
redis-server

# On macOS
brew services start redis

# On Ubuntu/Debian
sudo systemctl start redis-server
```

## 🔥 Running the Application

### Backend Services (Start in this order)

#### 1. Start Redis Server

Ensure Redis is running (see Redis Setup section above)

#### 2. Start Celery Worker

```bash
cd backend
celery -A celery_app worker --loglevel=info
```

#### 3. Start Scheduler

```bash
cd backend
python scheduler.py
```

#### 4. Start FastAPI Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

#### Start React Development Server

```bash
cd frontend
npm run dev
```

### 🌐 Access the Application

- **Frontend**: http://localhost:5173 (Vite default port)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)

> **Important**: Start all backend services (Redis, Celery, Scheduler) before starting the main FastAPI application to ensure full functionality.
