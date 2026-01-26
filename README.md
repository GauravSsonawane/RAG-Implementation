# Industrial RAG Implementation

A professional-grade Retrieval-Augmented Generation (RAG) system for industrial documentation, featuring a clean light-mode UI, automated document ingestion, and persistent session memory.

## 🚀 Quick Start Guide

Follow these steps to get the system up and running on your local machine.

### 1. Prerequisites
Ensure you have the following installed:
- **[Ollama](https://ollama.com/)** (Running locally)
- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**
- **Python 3.10+**
- **Node.js 18+**

### 2. Infrastructure Setup (Databases)
Start the Postgres (with Vector extension) and Redis containers:
```bash
docker-compose up -d
```

### 3. Backend Setup
1. **Model Pulling**: Ensure you have the required models in Ollama:
   ```bash
   ollama pull llama3.2:3b
   ollama pull nomic-embed-text:latest
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Launch FastAPI**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8002 --reload
   ```

### 4. Frontend Setup
1. **Install Packages**:
   ```bash
   cd frontend
   npm install
   ```
2. **Launch Dev Server**:
   ```bash
   npm run dev
   ```

## 🌐 Accessing the System
- **UI Interface**: [http://localhost:5173](http://localhost:5173)
- **API Documentation (Swagger)**: [http://localhost:8002/docs](http://localhost:8002/docs)

## ✨ Key Features
- **Llama 3.2 (3B) Integration**: Optimized for fast local performance.
- **Automated Ingestion**: Simply upload a PDF, and the system handles the background indexing/embedding.
- **Persistent Library**: Chat sessions are saved in Postgres and persist across restarts.
- **Source Citations**: Every AI response includes clickable citations to the exact manual used.
- **Premium Light Theme**: A clean, "Perplexity-style" aesthetic.

## 📂 Project Structure
- `/backend`: FastAPI routers and logic.
- `/frontend`: React + Vite + Tailwind UI.
- `/knowledge_base`: Directory for indexing original PDF manuals.
- `/orchestrator`: LangGraph workflow management.
- `/storage`: Database models and connection management.
