# AI_QUIZ - Intelligent MCQ Generation and Assessment Chatbot

## Problem Statement

**Intelligent MCQ Generation and Assessment Chatbot**

To streamline and enhance the interview process by leveraging artificial intelligence to automatically generate and administer skill-based multiple-choice questions (MCQs) through a chatbot interface.

## Description

This project implements an AI-powered assessment platform that includes:

- **Candidate Selection Interaction**: Engages shortlisted candidates via an AI-powered chatbot
- **Automated Profile Testing**: Conducts skill assessments through interactive chatbot sessions
- **Custom MCQ Generation**: Creates tailored multiple-choice questions for relevant skills during the interview process
- **Skill-Based Reporting**: Produces detailed reports ranking candidates based on their skill performance
- **Optional Face Capture**: Ensures identity verification by capturing candidates' faces during mock tests

## Architecture

This application consists of:

- **Backend**: FastAPI-based REST API with PostgreSQL database
- **Frontend**: React.js with TypeScript and Vite
- **AI Integration**: OpenAI integration for intelligent question generation
- **Real-time Communication**: WebSocket support for live interactions

## Prerequisites

Before running this application, ensure you have the following installed:

- **Python**: 3.8 or higher
- **Node.js**: 16.x or higher
- **PostgreSQL**: 12 or higher
- **Redis**: 6.0 or higher (for caching and session management)
- **Celery**: For background task processing

> **Note**: Detailed package dependencies are listed in `backend/requirements.txt` and `frontend/package.json`

## Installation & Setup

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

## Running the Application

> **⚠️ CRITICAL**: Follow this exact order and ensure each service starts successfully before proceeding to the next step. Each service must be running in a separate terminal window.

### Prerequisites Check

Before starting, verify these are running:

- ✅ PostgreSQL server is running and databases (`ai_quiz_db`, `test_persist_langgraph`) exist
- ✅ Redis server is running
- ✅ All environment variables are properly configured in `.env` files

### Step-by-Step Startup Process

#### Terminal 1: Start Redis Server

```bash
# Verify Redis is running first
redis-cli ping
# Expected output: PONG

# If Redis is not running, start it:
# Windows: redis-server
# macOS: brew services start redis
# Linux: sudo systemctl start redis-server
```

#### Terminal 2: Activate Python Environment & Start Celery Worker

```bash
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Start Celery worker (MUST see "ready" message)
celery -A celery_app worker --loglevel=info

# ✅ Wait for: "[INFO/MainProcess] Connected to redis://localhost:6379//"
# ✅ Wait for: "[INFO/MainProcess] mingle: searching for available nodes..."
# ✅ Wait for: "[INFO/MainProcess] mingle: all alone"
# ✅ Wait for: "[INFO/MainProcess] celery@<hostname> ready."
```

#### Terminal 3: Start Scheduler (Background Tasks)

```bash
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Start scheduler
python scheduler.py

# ✅ Wait for: "Scheduler started successfully"
```

#### Terminal 4: Start FastAPI Backend

```bash
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Start main application
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# ✅ Wait for: "Application startup complete."
# ✅ Wait for: "Uvicorn running on http://0.0.0.0:8000"
```

#### Terminal 5: Start Frontend

```bash
cd frontend

# Start React development server
npm run dev

# ✅ Wait for: "Local:   http://localhost:5173/"
# ✅ Wait for: "ready in [time]ms"
```

### Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **API Health Check**: http://localhost:8000/health (should return 200 OK)

### Verification Steps

1. **Backend Health Check**: Visit http://localhost:8000/health
2. **API Documentation**: Visit http://localhost:8000/docs - you should see Swagger UI
3. **Frontend**: Visit http://localhost:5173 - application should load
4. **Database Connection**: Check terminal outputs for database connection confirmations
5. **Celery Worker**: Verify Celery worker shows "ready" status in terminal

### ⚠️ Common Issues & Solutions

#### Issue: "Connection refused" errors

- **Solution**: Ensure PostgreSQL and Redis are running before starting backend services

#### Issue: "Database does not exist"

- **Solution**: Run database creation commands and initialization scripts:

```bash
cd backend
python setup_database.py
python validate_database.py
```

#### Issue: "Module not found" errors

- **Solution**: Ensure virtual environment is activated and dependencies are installed:

```bash
cd backend
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

#### Issue: Celery worker not connecting

- **Solution**: Verify Redis is running and accessible:

```bash
redis-cli ping  # Should return PONG
```

#### Issue: Frontend not loading

- **Solution**: Ensure Node.js dependencies are installed:

```bash
cd frontend
npm install
npm run dev
```

> **🚨 IMPORTANT**: Do NOT proceed to the next step until you see the success messages mentioned above. Each service must be fully operational before starting the next one.

## Key Features

### AI-Powered Assessment System

- **LangGraph Integration**: Advanced AI workflow management with the following service components:
  - `ai_screening_service.py` - Automated candidate screening
  - `mcq_generation/` - Dynamic MCQ creation based on job requirements
  - `resume_parsing/` - Intelligent resume analysis
  - `resume_screening/` - AI-driven candidate evaluation
  - `skill_graph_generation/` - Dynamic skill assessment graphs
  - `report_generation/` - Automated assessment reports

### Background Processing

- **Bulk Candidate Upload**: Asynchronous processing of multiple candidate applications using Celery
- **Real-time Assessment**: WebSocket-based live assessment sessions
- **Scheduled Tasks**: Automated report generation and candidate notifications

### Workflow Management

- **Assessment Pipeline**: End-to-end candidate evaluation workflow

> **Note**: Screenshots and detailed functionality demos will be provided separately for evaluation purposes.

## API Documentation

The application provides comprehensive API documentation through **Swagger UI**:

- **Interactive API Docs**: http://localhost:8000/docs
- Test endpoints directly from the browser
- View request/response schemas and authentication requirements

## Screenshots

### Demo Video

Watch the complete application walkthrough:

[![AI_QUIZ Demo Video](https://img.youtube.com/vi/EHdonrPPtoI/maxresdefault.jpg)](https://www.youtube.com/watch?v=EHdonrPPtoI)

_Click the image above to watch the full demo video_

### Dashboard & Management

#### Recruiter Dashboard

![Recruiter Dashboard](assets/recruiter_dashboard.png)

#### Test Dashboard

![Test Dashboard](assets/test_dashboard.png)

#### Tests Overview Page

![Tests Page](assets/Tests_Page.png)

### Test Management

#### Test Creation Interface

![Test Creation Page](assets/test_creation_page.png)

#### Test Candidates Management

![Test Candidates](assets/test_candidates.png)

### Reports & Analytics

#### Assessment Report Overview

![Assessment Report](assets/assessment_report.png)

#### Detailed Candidate Report

![Candidate Report](assets/candidate_report.png)

#### Candidate Performance Analysis

![Candidate Report 2](assets/candidate_report_2.png)

#### Advanced Candidate Metrics

![Candidate Report 3](assets/candidate_report_3.png)

#### AI-Generated Skill Graph

![Skill Graph](assets/skill_graph.png)
