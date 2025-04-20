
# AI-Powered Image Search Engine (Web + Desktop)

A multimodal image search system that lets users search through their local image collections using **natural language** queries. Supports both **web-based** and **desktop** interfaces built with Electron. Powered by **CLIP embeddings**
---

##  Features

- **Text-to-Image Search**: Search for images using plain text descriptions.
- **CLIP-Based Retrieval**: Leverages OpenAI's CLIP model for powerful multimodal understanding.
- **Next.js Web Frontend**: Modern responsive UI for browser access.
- **Electron Desktop App**: Cross-platform image search from your desktop.
- **Folder Indexing**: Select and index entire folders of images.
- **FastAPI Backend**: High-performance API for embedding and search.

---

##  Tech Stack

| Layer        | Tech                          |
|--------------|-------------------------------|
| Frontend     | [Next.js](https://nextjs.org/), [ShadCN UI](https://ui.shadcn.com/), [Electron](https://www.electronjs.org/) |
| Backend      | [FastAPI](https://fastapi.tiangolo.com/), [Python](https://www.python.org/) |
| ML Models    | [CLIP](https://openai.com/research/clip) |
| Search       | BM25, Cosine Similarity       |
| Storage      | Local folder index

## Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/Spandan7724/img_srch.git
```

### 2. Backend (FastAPI)

Run the backend

First install all required python libraried either with
```bash
uv sync
```
or 
```bash
pip install -r requirements.txt
```

then run the uvicorn server with 

```bash
 uvicorn server.main:app --reload
```

make sure you are in the main direcotory when doing this outside the backend directory 

### 3. Web Frontend (Next.js)

to run the frontend simply 

```bash
cd frontend_img_srch
```

then 

```bash
npm install
```

```bash
npm run dev 
```

### 3. Electron App (searchbar)

Also I have added a Electron based desktop app which is in the form of just a search bar 

```bash
cd img_launcher
```

```bash
npm install
```

```bash
npm start
```
And then do 

```bash
alt+s
```

to start/close it 


## How It Works

- User selects a folder (via web or desktop).

- Images are indexed by extracting CLIP embeddings.

- Search queries are converted into text embeddings.

- Results are ranked by cosine similarity


## Future Enhancements

- Real-time captioning & OCR pipeline.

- GPU-accelerated caption generation.

- User feedback loop for improving search relevance.

- Dockerized deployment for easier setup.

- Cloud sync for remote image browsing.
