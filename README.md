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
1. **Environment Configuration**: 
   Create a `.env` file in the root directory and copy the contents from `.env.example`:
   ```bash
   cp .env.example .env
   ```
2. **Model Pulling**: Ensure you have the required models in Ollama:
   ```bash
   ollama pull llama3.2:3b
   ollama pull nomic-embed-text:latest
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. **Initialize & Seed Database**:
   ```bash
   python storage/init_db.py
   python seed_db.py
   ```
5. **Launch FastAPI**:
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
- **Multi-Format Support**: Handle PDF, Word (.docx), Excel (.xlsx, .xls), CSV, and Text (.txt, .md).
- **Enhanced Retrieval**: Automatically prepends document headers to searchable content for 100% accurate file-based queries.
- **Llama 3.2 (3B) Integration**: Optimized for fast local performance.
- **Automated Ingestion**: Background indexing and embedding with a unified loader factory.
- **Persistent Library**: Chat sessions saved in Postgres with source-tracked vector storage.
- **Source Citations**: Every AI response includes clickable citations to the exact manual used.

## 📂 Project Structure
- `/backend`: FastAPI routers and logic.
- `/frontend`: React + Vite + Tailwind UI.
- `/knowledge_base`: Directory for storage and indexing of source documents.
- `/orchestrator`: LangGraph workflow management.
- `/storage`: Database models and connection management.

## 🛠️ Maintenance & Reset
- **Initialization**: Run `python storage/init_db.py` then `python seed_db.py` to set up tables and system docs.
- **Index All Files**: Run `$env:PYTHONPATH="."; python -m knowledge_base.ingest` to force-index all documents in the knowledge base.
- **Full Reset**: Run `python scorched_earth.py` to wipe the entire vector database (use with caution).
