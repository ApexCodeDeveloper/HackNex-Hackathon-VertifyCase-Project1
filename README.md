# 🚀 Hackathon Project — AI-Powered Legal Assistant

An AI-powered legal assistance platform designed to help users analyze legal documents, understand cases, perform grounded legal research, and generate legal drafts with verifiable sources.

> Built during **Karunya Hacknex — 24-Hour Hackathon 2026**

---

## 🎯 Problem

Legal documents are often lengthy, complex, and difficult to understand. Finding important facts, contradictions, evidence, and relevant legal information manually can take significant time.

Our project aims to make legal document analysis faster, more accessible, and more reliable using **AI + RAG + Agentic Workflows**.

---

## 💡 Our Solution

We built an **Agentic Legal Assistant** that can reason over uploaded legal documents and provide grounded responses with references to the original sources.

### Core Workflows

* 📄 **Contract / Case Review**

  * Extract important facts
  * Identify contradictions
  * Detect missing information
  * Find relevant evidence
  * Provide source references

* ✍️ **Legal Drafting**

  * Generate structured legal drafts
  * Use information from uploaded documents
  * Keep generated content grounded in available evidence

* 🔎 **Legal Research**

  * Search and analyze relevant legal information
  * Connect research findings with the user's case

* 💬 **Grounded RAG Chat**

  * Ask questions about uploaded documents
  * Retrieve relevant sections
  * Generate answers based on the retrieved evidence

---

## 🧠 Key Idea

Instead of treating an LLM as a simple chatbot, our system uses an **agentic workflow**:

```text
User
  ↓
Upload Legal Documents
  ↓
Document Processing
  ↓
Chunking & Embeddings
  ↓
Vector Database
  ↓
RAG Retrieval
  ↓
AI Agent
  ↓
Reasoning + Analysis
  ↓
Verified Response + Sources
```

---

## ✨ Key Features

* 📑 Legal document upload and processing
* 🤖 AI-powered document analysis
* 🔍 Retrieval-Augmented Generation (RAG)
* 🧠 Agent-based reasoning
* 📌 Source-grounded responses
* ⚠️ Contradiction and missing-information detection
* ✍️ AI-assisted legal drafting
* 💬 Interactive legal document chat
* 🎨 Minimal and user-friendly interface

---

## 🛠️ Tech Stack

**Frontend**

* HTML / CSS / JavaScript
* React *(if applicable)*

**Backend**

* Python
* FastAPI

**AI**

* Large Language Model (LLM)
* Retrieval-Augmented Generation (RAG)
* Agentic AI workflows

**Database / Storage**

* Vector Database
* Document Storage

**Deployment**

* Cloud deployment

---

## 🏗️ Architecture

```text
                  ┌─────────────────┐
                  │      User       │
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │   Web Interface │
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │     FastAPI     │
                  │     Backend     │
                  └────────┬────────┘
                           ↓
              ┌─────────────────────────┐
              │   Document Processing   │
              └────────────┬────────────┘
                           ↓
                  ┌─────────────────┐
                  │ Embedding Model │
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │ Vector Database │
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │   AI Agent /    │
                  │      RAG        │
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │ Grounded Answer │
                  │  + References   │
                  └─────────────────┘
```

---

## 🎥 Prototype

The prototype demonstrates the complete user journey:

1. Upload a legal document
2. Process and analyze the document
3. Ask questions about the case
4. Retrieve relevant information
5. Generate an AI-powered response
6. Show supporting sources and evidence

---

## 🌟 Why This Project?

Legal professionals and individuals can spend significant amounts of time reading and analyzing large amounts of information.

Our goal is **not to replace lawyers**, but to build an AI assistant that helps them:

* Save time
* Find information faster
* Analyze documents more efficiently
* Reduce repetitive work
* Access relevant evidence quickly

---

## 🔮 Future Improvements

* Support for more Indian legal languages
* Improved legal-domain models
* Larger legal knowledge base
* Advanced citation verification
* Multi-agent legal workflows
* Voice-based interaction
* Lawyer / organization dashboards
* Case timeline generation
* Integration with trusted legal databases

---

## ⚠️ Disclaimer

This project is a **hackathon prototype** and is intended for research and demonstration purposes.

It does **not provide professional legal advice**. AI-generated results should always be reviewed and verified by a qualified legal professional.

---

## 👥 Team

Built with ❤️ by our team during **Karunya Hacknex 2026**.

### Team Members

* **Pragadeesh** — AI / Backend / Development
* **Vigneshwaran** — Presentation
* **Prakash** — Testing
* **Naveen** — Frontend

---

## 📜 License

This project was created for **Karunya Hacknex 2026**.

---

⭐ If you find this project interesting, consider giving the repository a star!
