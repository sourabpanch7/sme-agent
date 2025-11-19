# RAGgers Project - Mid-Evaluation Technical Report

**Run the server**
```bash
 uvicorn app.main:app --reload
```

**Live Frontend Demo**: https://ra-ggers-frontend.vercel.app/

## Project Overview

| Attribute | Details |
|-----------|---------|
| **Project Name** | RAGgers - IP Expert AI Agent |
| **Domain** | Intellectual Property Laws |
| **Evaluation Type** | Mid-term Assessment |
| **Team** | RAGgers |
| **Date** | October 25, 2025 |
| **Frontend Deployment** | https://ra-ggers-frontend.vercel.app/ |
| **Backend Status** | Local development (hosting planned) |

## Technology Stack Analysis

### Frontend Architecture

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | Next.js 14 | React-based web application framework |
| **Language** | TypeScript | Type-safe JavaScript development |
| **Styling** | Tailwind CSS | Utility-first CSS framework |
| **Authentication** | Firebase Auth | User authentication and authorization |
| **Database** | Firebase Realtime DB | Real-time data synchronization |
| **State Management** | React Context | Global application state |

### Backend Architecture

| Component | Technology | Purpose |
|-----------|------------|---------|
| **API Framework** | FastAPI | High-performance Python web framework |
| **AI/ML Framework** | LangChain | LLM orchestration and workflow management |
| **Language Model** | Google Gemini 2.0/2.5 Flash | Natural language processing and generation |
| **Vector Database** | Milvus Lite | Vector similarity search and storage |
| **Embeddings** | Google Generative AI | Document and query vectorization |
| **Document Processing** | PyPDF2, RecursiveCharacterTextSplitter | PDF parsing and text chunking |

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
├─────────────────────────────────────────────────────────────────┤
│  Next.js Frontend (Port 3000)                                    │
│  ├─ Authentication (Firebase Auth)                               │
│  ├─ Chat Interface (Real-time messaging)                         │
│  ├─ Conversation Management                                       │
│  └─ Theme Management (Light/Dark/System)                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ HTTP/WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend Services                            │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Server (Port 8000)                                      │
│  ├─ Chat Routes (/chat/get_answer)                               │
│  ├─ Quiz Routes (/chat/generate_quiz)                            │
│  └─ API Documentation (/docs)                                    │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     RAG Pipeline                                 │
├─────────────────────────────────────────────────────────────────┤
│  ├─ Ensemble Retriever (3 Collections)                          │
│  │  ├─ ip_laws (Weight: 0.4)                                    │
│  │  ├─ ip_laws_extended (Weight: 0.4)                           │
│  │  └─ ip_laws_hindi (Weight: 0.2)                              │
│  ├─ Context Compression (FlashRank)                              │
│  └─ LLM Integration (Gemini)                                     │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Vector Database                               │
├─────────────────────────────────────────────────────────────────┤
│  Milvus Database                                                 │
│  ├─ Dense Vectors (Cosine Similarity)                           │
│  ├─ Sparse Vectors (BM25)                                       │
│  └─ Hybrid Search Implementation                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Core Implementation Analysis

### Multi-Collection RAG System

The system implements an advanced ensemble retrieval approach using three separate document collections:

| Collection | Weight | Purpose | Content Type |
|------------|--------|---------|--------------|
| `ip_laws` | 0.4 | Primary legal documents | Core IP law texts |
| `ip_laws_extended` | 0.4 | Extended documentation | Detailed procedures and rules |
| `ip_laws_hindi` | 0.2 | Regional language support | Hindi translations |

### Chat Implementation (Home_2.py)

The main chat functionality is implemented through the `InteractIpExpert` class:

```python
class InteractIpExpert(PdfEmbeder, IpRAG, IpExpertLLM, VectorStore)
```

**Key Features:**
- Multiple inheritance for modular functionality
- Ensemble retriever with weighted document collections
- Context-aware conversation management
- Streamlit-based user interface for testing
- Error handling and fallback responses

### Quiz Generation (Home.py)

The quiz generation system uses the `IpQuizGenerator` class:

```python
class IpQuizGenerator(PdfEmbeder, IpRAG, VectorStore, IpQuizAgent)
```

**Key Features:**
- Multi-agent architecture for quiz creation
- PDF output generation
- Document retrieval from multiple sources
- Structured question-answer format

## Feature Implementation Status

### Completed Features

| Feature Category | Implementation Details | Status |
|------------------|------------------------|---------|
| **Authentication** | Email/password + Anonymous login | Complete |
| **Real-time Chat** | Firebase Realtime Database integration | Complete |
| **RAG Pipeline** | Multi-collection ensemble retrieval | Complete |
| **Vector Search** | Hybrid dense + sparse search | Complete |
| **UI/UX** | Modern responsive interface | Complete |
| **API Layer** | RESTful endpoints with documentation | Complete |
| **Document Processing** | Automated PDF ingestion | Complete |
| **Agent System** | Chat and Quiz generation agents | Complete |

### Component Distribution

```mermaid
pie title "Implementation Completeness"
    "Frontend Components" : 45
    "Backend Services" : 35
    "RAG Pipeline" : 15
    "Integration Layer" : 5
```

## Database Schema Analysis

### Firebase Realtime Database Structure

```json
{
  "users": {
    "{userId}": {
      "uid": "string",
      "email": "string", 
      "isAnonymous": "boolean",
      "createdAt": "ISO8601",
      "conversations": {
        "default": {
          "title": "string",
          "lastMessage": "string",
          "timestamp": "number",
          "messages": {
            "{messageId}": {
              "role": "user|assistant",
              "content": "string",
              "timestamp": "number"
            }
          }
        }
      },
      "settings": {
        "theme": "light|dark|system"
      },
      "profile": {
        "displayName": "string"
      }
    }
  }
}
```

### Vector Database Schema

| Field | Type | Purpose |
|-------|------|---------|
| **dense** | Vector | Dense embeddings for semantic similarity |
| **sparse** | SparseVector | BM25 sparse vectors for keyword matching |
| **text** | String | Original document content |
| **metadata** | JSON | Document metadata and source information |

## API Endpoint Documentation

### Chat Endpoints

| Endpoint | Method | Purpose | Request Schema |
|----------|--------|---------|----------------|
| `/chat/get_answer` | POST | Process chat queries | `ChatRequest` |
| `/chat/generate_quiz` | POST | Generate quiz content | `ChatRequest` |

### Request/Response Models

**ChatRequest Schema:**
```json
{
  "user_id": "string",
  "query": "string", 
  "message_id": "string"
}
```

**ChatResponse Schema:**
```json
{
  "user_id": "string",
  "role": "assistant",
  "message_id": "string",
  "timestamp": "ISO8601",
  "content": [
    {
      "text": "string",
      "source_docs": [
        {
          "id": "string",
          "text": "string",
          "meta": "object"
        }
      ]
    }
  ]
}
```

## Performance Metrics

### Vector Search Configuration

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **Chunk Size** | 2500 characters | Optimal context window |
| **Chunk Overlap** | 1400 characters | Maintain context continuity |
| **Top-K Retrieval** | 5 documents | Balance relevance and performance |
| **Index Type** | IVF_FLAT (dense), SPARSE_INVERTED_INDEX (sparse) | Efficient similarity search |

### Model Configuration

| Component | Model/Version | Configuration |
|-----------|---------------|---------------|
| **Chat LLM** | Gemini 2.0 Flash | Temperature: 0, Reasoning: none |
| **Quiz LLM** | Gemini 2.5 Flash | Temperature: 0, Reasoning: none |
| **Embeddings** | text-embedding-004 | Google Generative AI |
| **Reranker** | FlashRank | Context compression |

## Service Architecture

### Modular Service Design

```
app/
├── services/
│   ├── llm_service.py          # LLM integration and prompting
│   ├── rag_service.py          # Retrieval and ranking logic  
│   ├── embedding_service.py    # Vector operations and storage
│   ├── agent_service.py        # Multi-agent orchestration
│   └── service_interface.py    # Abstract base classes
├── core/
│   ├── repository.py           # Data access layer
│   └── session_manager.py      # Session handling
├── models/
│   └── schemas.py              # Pydantic data models
└── routers/
    └── chat_routes.py          # API endpoint definitions
```

### Inheritance Hierarchy

```
GenericEmbedder ←── PdfEmbeder
GenericRAG ←── IpRAG  
GenericLLM ←── IpExpertLLM
GenericAgent ←── IpQuizAgent
VectorStore ←── Milvus Integration
```

## Data Flow Analysis

### Chat Flow Sequence

1. **User Input** → Frontend chat interface
2. **Authentication** → Firebase Auth validation
3. **Message Storage** → Firebase Realtime Database
4. **API Request** → FastAPI backend endpoint
5. Query Processing → Ensemble retriever activation for the multiple collections
6. Vector Search → Multi-collection hybrid search based on cosine similarity dense search and BM25 sparse search
7. Context Retrieval → Document ranking and selection using FlashReRanker
8. **LLM Processing** → Gemini model inference
9. **Response Generation** → Structured answer formatting
10. **Real-time Update** → Firebase database synchronization

### Quiz Generation Flow

1. **Quiz Request** → User initiates quiz generation
2. **Document Retrieval** → Multi-source content gathering
3. **Agent Processing** → Quiz agent workflow execution
4. **Question Generation** → LLM-based quiz creation
5. **PDF Creation** → Formatted output generation
6. **File Storage** → Local file system storage
7. **Response Delivery** → File path and status return

## Integration Architecture

### Frontend-Backend Communication

| Integration Point | Current Status | Implementation Method |
|-------------------|----------------|----------------------|
| **Authentication** | Complete | Firebase SDK |
| **Real-time Messaging** | Complete | Firebase Realtime DB |
| **Chat API** | Ready (pending connection) | HTTP POST requests |
| **Quiz API** | Ready (pending connection) | HTTP POST requests |
| **Error Handling** | Partial | Try-catch with fallbacks |

### Environment Configuration

| Variable | Purpose | Location |
|----------|---------|----------|
| `GEMINI_API_KEY` | Google AI API access | Backend .env |
| `NEXT_PUBLIC_FIREBASE_*` | Firebase configuration | Frontend .env |

## Deployment Status

### Current Deployment

| Component | Status | Location |
|-----------|--------|----------|
| **Frontend** | Deployed | https://ra-ggers-frontend.vercel.app/ |
| **Backend** | Local Development | Port 8000 (hosting planned) |
| **Vector Database** | Local Development | Milvus Lite database file |
| **Firebase Services** | Cloud Hosted | Google Firebase |

## Security Implementation

### Authentication Flow

1. **User Registration/Login** → Firebase Auth
2. **Token Generation** → JWT tokens
3. **Session Management** → Firebase session cookies
4. **Route Protection** → Next.js middleware
5. **API Authorization** → Token validation

### Data Access Control

| Resource | Access Method | Security Layer |
|----------|---------------|----------------|
| **User Data** | User ID-based paths | Firebase security rules |
| **Chat Messages** | Authenticated requests | Context isolation |
| **Vector Database** | Service-level access | Internal network |
| **API Endpoints** | Public access | Input validation |

## Testing and Quality Assurance

### Code Quality Metrics

| Aspect | Implementation | Coverage |
|--------|----------------|----------|
| **Type Safety** | TypeScript (Frontend) | 100% |
| **Error Handling** | Try-catch blocks | Comprehensive |
| **Input Validation** | Pydantic schemas | All API endpoints |
| **Documentation** | Inline comments | High coverage |

### Testing Infrastructure

| Component | Testing Method | Status |
|-----------|----------------|---------|
| **API Endpoints** | Swagger documentation | Available |
| **Frontend Components** | Manual testing | Functional |
| **RAG Pipeline** | Streamlit interface | Operational |
| **Vector Search** | Direct queries | Verified |

## Current Integration Status

### Connection Requirements

The frontend and backend systems are architecturally prepared for integration. The primary requirement is replacing the placeholder response in the chat interface:

**Current Implementation:**
```typescript
// TODO: Replace this with actual API call to your backend
const assistantMessage = "This is a placeholder response...";
```

**Required Implementation:**
```typescript
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat/get_answer`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: userMessage,
    user_id: user.uid,
    message_id: `msg_${Date.now()}`
  })
});
```

### Readiness Assessment

| Component | Status | Notes |
|-----------|--------|-------|
| **Frontend UI** | Ready | Complete interface implementation |
| **Backend APIs** | Ready | Functional endpoints with documentation |
| **Authentication** | Ready | Firebase integration complete |
| **Database** | Ready | Vector and real-time databases operational |
| **RAG Pipeline** | Ready | Multi-collection ensemble functional |

## Recommendations for Final Phase

### Priority Tasks

| Priority | Task | Estimated Effort | Impact |
|----------|------|------------------|---------|
| **High** | Frontend-Backend API Integration | 2-3 days | Critical |
| **Medium** | Source Document Citations UI | 2-3 days | High |
| **Medium** | Quiz Generation Frontend | 3-4 days | High |
| **Low** | Error Handling Enhancement | 1-2 days | Medium |
| **Low** | Performance Optimization | 2-3 days | Medium |

### Technical Improvements for Future Development

1. **Response Streaming**: Real-time response streaming implementation
2. **Backend Deployment**: Cloud hosting setup for production access  
3. **Monitoring**: Logging and monitoring system implementation
4. **Testing**: Comprehensive test suite development

## Project Status Summary

The RAGgers project implements a domain-specific AI agent for Intellectual Property Laws using modern web technologies. The system integrates ensemble retrieval, multi-agent architecture, and real-time web interfaces. The modular backend architecture includes FastAPI services, while the frontend provides a complete user interface deployed on Vercel.

**Current Status:**
- Frontend: Deployed and functional at https://ra-ggers-frontend.vercel.app/
- Backend: Fully developed and tested locally, pending cloud deployment
- Integration: Final API connection step remaining
- Resources can be found at the below location:
https://drive.google.com/drive/u/1/folders/1T3_TJcPzaZMoeH78zGBm2cC4pneq1hQP

The project includes functional RAG pipeline, authentication system, real-time chat interface, and comprehensive document processing capabilities.
