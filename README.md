<div align="center">

# 🌱 PALASH

### **AI-Powered Vernacular Pedagogy & Real-Time Translation**

**Empowering every child to learn in the language they understand best.**

<br/>

[![React Native](https://img.shields.io/badge/React%20Native-Expo-61DAFB?style=for-the-badge\&logo=react\&logoColor=white)](https://reactnative.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge\&logo=fastapi\&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge\&logo=python\&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-Frontend-3178C6?style=for-the-badge\&logo=typescript\&logoColor=white)](https://www.typescriptlang.org/)
[![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?style=for-the-badge\&logo=supabase\&logoColor=white)](https://supabase.com/)

<br/>

**🌐 Multilingual • 🎙️ Speech-Enabled • 📚 Curriculum-Aware • 📡 Offline-First**

</div>

---

## 🧭 What is PALASH?

**PALASH** is an AI-powered educational platform designed to support **mother-tongue-based primary education**.

It brings together:

> 🗣️ **Speech**
> 🌐 **Translation**
> 🤖 **Artificial Intelligence**
> 📚 **Curriculum**
> 📱 **Mobile Learning**
> 📡 **Offline Accessibility**

into a single ecosystem for teachers and students.

The goal is simple:

### **Language should never be a barrier to learning.**

PALASH is particularly designed for multilingual and low-resource language environments where conventional digital education tools often fall short.

---

# 🎯 The Problem

In many multilingual classrooms, students may understand concepts better in their **mother tongue**, while available educational resources are predominantly available in other languages.

This creates challenges such as:

| Challenge                    | Impact                                    |
| ---------------------------- | ----------------------------------------- |
| 🌐 Language barriers         | Students struggle to understand concepts  |
| 📖 Limited localized content | Fewer learning resources                  |
| 🗣️ Low-resource languages   | Limited NLP and speech technologies       |
| 📡 Poor connectivity         | Cloud-only tools become unreliable        |
| 👩‍🏫 Teacher workload       | Manual translation and worksheet creation |
| 🧩 Fragmented tools          | Teachers need multiple applications       |

PALASH addresses these challenges through a **single AI-assisted learning ecosystem**.

---

# 💡 Our Solution

PALASH creates a bridge between:

```text
┌─────────────────────┐
│      TEACHER        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   PALASH MOBILE     │
│                     │
│ Translation         │
│ Speech               │
│ Lessons              │
│ Worksheets           │
│ Classroom Tools      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    AI SERVICES      │
│                     │
│ Translation          │
│ Speech / ASR         │
│ Text-to-Speech       │
│ Content Generation   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     BACKEND         │
│      FastAPI        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ DATABASE + CACHE    │
│                     │
│ Supabase PostgreSQL │
│ Local Storage       │
└─────────────────────┘
```

---

# ✨ Key Features

<table>
<tr>
<td width="50%">

### 🌐 Multilingual Translation

Translate educational content between supported languages while maintaining a **cache-first workflow** for faster repeated translations.

</td>

<td width="50%">

### 🎙️ Speech & Audio

Enable speech-oriented interaction and audio learning through speech processing and **Text-to-Speech** services.

</td>
</tr>

<tr>
<td>

### 📚 Curriculum Support

Organize learning around structured curriculum, lessons, topics and educational resources.

</td>

<td>

### 📝 AI Worksheets

Generate educational worksheets including:

* MCQs
* Fill in the blanks
* Matching questions
* Picture-based activities

</td>
</tr>

<tr>
<td>

### 📡 Offline-First

Store frequently used resources locally so learning can continue even when internet connectivity is limited.

</td>

<td>

### 🧑‍🏫 Classroom Context

Maintain learning context around teachers, classrooms, lessons and educational sessions.

</td>
</tr>
</table>

---

# 🧠 AI Pipeline

PALASH is designed around multiple AI-assisted workflows.

### Translation Pipeline

```text
                    USER INPUT
                        │
                        ▼
                Language Selection
                        │
                        ▼
                 Local Cache
                    /     \
                 FOUND    NOT FOUND
                  │          │
                  │          ▼
                  │     Backend API
                  │          │
                  │          ▼
                  │   Translation Model
                  │          │
                  │          ▼
                  └────► Translated Text
                              │
                              ▼
                         Save Cache
```

### Speech Pipeline

```text
Voice Input
     │
     ▼
Audio Processing
     │
     ▼
Speech Recognition
     │
     ▼
Text Processing
     │
     ▼
Translation / Learning
     │
     ▼
Text-to-Speech
     │
     ▼
Audio Output
```

---

# 📡 Offline-First Architecture

Connectivity shouldn't decide whether a child can learn.

PALASH therefore follows an **offline-first approach**.

```text
                  ┌───────────────┐
                  │ PALASH MOBILE │
                  └───────┬───────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  LOCAL STORAGE  │
                 │                 │
                 │ • Lessons       │
                 │ • Translations  │
                 │ • Worksheets    │
                 │ • Preferences   │
                 └────────┬────────┘
                          │
                   Internet Available?
                     /             \
                   YES              NO
                   │                 │
                   ▼                 ▼
             Backend Sync       Continue Offline
                   │                 │
                   └────────┬────────┘
                            ▼
                         Learning
```

This architecture is especially valuable for environments where network connectivity may be inconsistent.

---

# 🏗️ System Architecture

PALASH follows a modular architecture:

```text
┌─────────────────────────────────────────────┐
│                 PALASH APP                  │
│                                             │
│          React Native + Expo                │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│               DOMAIN SERVICES               │
│                                             │
│ Translation │ Audio │ Offline │ Classroom   │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│                 API LAYER                   │
│                   FastAPI                   │
│                                             │
│ Auth • Curriculum • Lessons • Translation  │
│ Speech • Worksheets • Sync • Classrooms    │
└───────────────┬─────────────────┬───────────┘
                │                 │
                ▼                 ▼
       ┌────────────────┐   ┌───────────────┐
       │   PostgreSQL   │   │  AI SERVICES  │
       │    Supabase    │   │               │
       │                │   │ Translation   │
       │                │   │ Speech / TTS  │
       └────────────────┘   └───────────────┘
```

The repository itself separates the mobile application, backend, ML components, workers, benchmarks, documentation and seed data.

---

# 🛠️ Technology Stack

<div align="center">

| Layer                 | Technology                     |
| :-------------------- | :----------------------------- |
| 📱 Mobile             | **React Native + Expo**        |
| 🎨 Frontend           | **TypeScript**                 |
| ⚙️ Backend            | **Python + FastAPI**           |
| 🗄️ Database          | **Supabase PostgreSQL**        |
| 💾 Local Storage      | **AsyncStorage**               |
| 🔐 Authentication     | **JWT**                        |
| 🤖 AI                 | **Translation + Speech + TTS** |
| 🚀 API Server         | **Uvicorn**                    |
| 📦 Package Management | **npm / pip**                  |
| 🔧 Version Control    | **Git + GitHub**               |

</div>

---

# 📂 Project Structure

```text
PALASH/
│
├── 📱 PalashMobile/
│   └── React Native + Expo application
│
├── ⚙️ backend/
│   └── FastAPI backend services
│
├── 🤖 ml/
│   └── Machine Learning / AI components
│
├── 🔄 workers/
│   └── Background processing
│
├── 📊 benchmarks/
│   └── Model & system evaluation
│
├── 🌱 data/
│   └── Seed / initialization data
│
├── 📚 docs/
│   └── Project documentation
│
├── 🔧 scripts/
│   └── Development & utility scripts
│
├── 🏛️ ARCHITECTURE.md
├── 🔗 API_MAPPING.md
├── 📡 ENDPOINTS_USED.md
├── 🆕 NEW_ENDPOINTS.md
├── 🚀 SETUP.md
└── 🧪 conftest.py
```

---

# 🚀 Quick Start

## 1️⃣ Clone

```bash
git clone https://github.com/avishrey-beep/PALASH.git

cd PALASH
```

---

## 2️⃣ Start the Mobile App

```bash
cd PalashMobile

npm install

npx expo start
```

You can then run the application using your preferred Expo development environment.

---

## 3️⃣ Start the Backend

```bash
cd backend

python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

# 🔐 Environment Variables

Configure the required environment variables before running the project.

### Mobile

```env
EXPO_PUBLIC_API_BASE_URL=http://YOUR_BACKEND_IP:8000
```

### Development examples

**Android Emulator**

```text
http://10.0.2.2:8000
```

**iOS Simulator / Web**

```text
http://127.0.0.1:8000
```

> ⚠️ Never commit API keys, database credentials, JWT secrets or other sensitive credentials to GitHub.

---

# 🔑 Authentication

PALASH uses **JWT-based authentication** to secure protected API endpoints.

The authentication layer handles:

* 🔐 Access tokens
* 🔄 Refresh tokens
* 🛡️ Authorization headers
* ♻️ Token refresh
* 👤 Authentication state

---

# 📈 Scalability

PALASH is designed to grow beyond a prototype.

### Current modular boundaries allow future expansion into:

```text
             PALASH
                │
     ┌──────────┼──────────┐
     ▼          ▼          ▼
Languages     AI Models   Analytics
     │          │          │
     ▼          ▼          ▼
Language      Speech      Teacher
Packs         Models      Dashboard
     │          │          │
     └──────────┼──────────┘
                ▼
         National Scale
```

Future scalability opportunities include:

* 🌐 Additional Indian languages
* 🧠 Improved low-resource language models
* 🎙️ Better speech recognition
* 🔊 Improved regional-language TTS
* 📦 Downloadable language packs
* 📊 Teacher analytics
* 🎯 Personalized learning
* ☁️ Scalable cloud infrastructure

---

# 🎓 Educational Impact

PALASH aims to make digital education more **inclusive, localized and accessible**.

### 👨‍🏫 For Teachers

* Reduce translation effort
* Generate localized learning material
* Access structured curriculum resources
* Continue working with limited connectivity

### 👧 For Students

* Learn in familiar languages
* Access audio-supported learning
* Understand concepts more naturally
* Benefit from localized educational content

### 🌏 For Education Systems

* Support multilingual education
* Enable digital resources for underserved languages
* Build reusable language resources
* Reduce dependence on one-language-only educational platforms

---

# 🔮 Roadmap

```text
                    PALASH ROADMAP

        ┌──────────────────────────────┐
        │ ✅ Core Mobile Platform      │
        └──────────────┬───────────────┘
                       │
        ┌──────────────▼───────────────┐
        │ ✅ Translation Infrastructure│
        └──────────────┬───────────────┘
                       │
        ┌──────────────▼───────────────┐
        │ 🔄 Speech & Audio            │
        └──────────────┬───────────────┘
                       │
        ┌──────────────▼───────────────┐
        │ 🔄 Offline Language Packs    │
        └──────────────┬───────────────┘
                       │
        ┌──────────────▼───────────────┐
        │ 🚀 Advanced AI Models        │
        └──────────────┬───────────────┘
                       │
        ┌──────────────▼───────────────┐
        │ 🚀 National Language Scale   │
        └──────────────────────────────┘
```

---

# 🤝 Contributing

Contributions are welcome!

### Step 1 — Fork

```bash
git fork https://github.com/avishrey-beep/PALASH.git
```

### Step 2 — Create a branch

```bash
git checkout -b feature/your-feature
```

### Step 3 — Commit

```bash
git add .

git commit -m "feat: add your feature"
```

### Step 4 — Push

```bash
git push origin feature/your-feature
```

### Step 5 — Open a Pull Request

Please include:

* Clear description
* Testing details
* Screenshots where relevant
* API/database changes
* Documentation updates

---

# 📚 Documentation

| Document                                   | Purpose               |
| :----------------------------------------- | :-------------------- |
| [`ARCHITECTURE.md`](./ARCHITECTURE.md)     | System architecture   |
| [`SETUP.md`](./SETUP.md)                   | Development setup     |
| [`API_MAPPING.md`](./API_MAPPING.md)       | API mapping           |
| [`ENDPOINTS_USED.md`](./ENDPOINTS_USED.md) | Existing endpoints    |
| [`NEW_ENDPOINTS.md`](./NEW_ENDPOINTS.md)   | Planned/new endpoints |

---

# 🌟 Vision

<div align="center">

### **"Every child deserves to learn in a language they understand."**

PALASH combines **AI, language technology and education**
to build a more inclusive digital learning ecosystem.

<br/>

🌱 **Learn in your language.**
🤖 **Powered by AI.**
📚 **Built for education.**
🇮🇳 **Designed for multilingual India.**

</div>

---

# ⭐ Support PALASH

If you believe technology can make education more inclusive:

**⭐ Star the repository**

**🍴 Fork the project**

**🐛 Report issues**

**💡 Suggest improvements**

**🤝 Contribute**

---

<div align="center">

### 🌱 PALASH

**AI-Powered Vernacular Education**

Made with ❤️ for multilingual learners and educators.

</div>
