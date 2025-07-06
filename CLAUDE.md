start responses with smileys 
any code you do do adjust the backend and frontend as well

make sure you use prebuilt libraries no use of raw code find npm libs for doing things and pypi packages best suited for jobs

There a common app that has a response view always use that response to return responses like other apis are returning

we are using pnpm. shadcn and radix ui for frontend

# Project Structure & Goals

## 🎯 OVRA AI - Spanish Tax Law Consultation System

### What We're Building
OVRA AI is a sophisticated AI-powered legal chatbot that provides real-time Spanish tax law consultation, specifically designed for freelancers and professionals in arts/cultural sectors. It democratizes access to Spanish tax law through AI-powered RAG (Retrieval-Augmented Generation) using official BOE documents.

### Core Purpose
- **Democratize Spanish tax law access** for freelancers and cultural professionals
- **Provide instant, accurate tax consultation** using AI-powered RAG
- **Stay current with tax legislation** through automated BOE document processing
- **Offer both authenticated chat and anonymous widget access**

### Tech Stack
**Backend (Django REST API)**
- Django 5.0 + Django REST Framework
- PostgreSQL with pgvector for embeddings
- OpenAI GPT-4 with LangChain
- WebSockets via Django Channels
- Django Q2 for background tasks

**Frontend (Next.js)**
- Next.js 15.2.4 with TypeScript
- Shadcn/UI + Radix UI components
- Tailwind CSS
- PNPM package manager

### Key Features
1. **RAG-Powered Legal Consultation** - Vector search through Spanish tax laws
2. **Real-time BOE Integration** - Daily capture of official Spanish legal documents
3. **Dual Access Models** - Authenticated users + anonymous widget access
4. **Embeddable Widget** - For external websites and lead generation
5. **Multi-language Support** - English/Spanish interface
6. **Cost Tracking** - OpenAI usage monitoring

### Architecture Overview
```
BOE API → PDF Processing → Vector Embeddings → RAG Search → AI Consultation
User Query → Context Retrieval → OpenAI GPT-4 → Cited Legal Response
```

### Target Audience
- Spanish freelancers needing tax guidance
- Arts & cultural professionals with complex tax situations
- Legal/accounting firms wanting AI consultation tools
- Spanish SMEs requiring accessible tax law interpretation
