# 🌍 Umuhuza Platform

### Empowering Rwandan Agriculture through Data, Collaboration, and Digital Innovation

---

## 🧩 Overview

**Umuhuza Platform** is an integrated agricultural information and collaboration system that connects **Farmers**, **Agro-Dealers**, **Processors & Customers**, and **Researchers**.  
It bridges the gap between data and decision-making in Rwanda’s agricultural value chain by providing real-time insights, digital transactions, and knowledge sharing.

---

## 💡 Purpose

The platform helps to:

- 🌦 Provide **accurate weather forecasts** and **market price trends** to farmers.  
- 📦 Facilitate **digital ordering** between farmers and agro-dealers.  
- 🏭 Allow **processors** to access available crops directly from farmers.  
- 🧪 Enable **researchers** to analyze agricultural and economic data (e.g., NISR datasets).  
- 🌱 Strengthen the connection between **data, production, and market decisions**.

---

## ⚙️ Technology Stack

| Component | Technology |
|------------|-------------|
| **Backend** | Flask (Python) |
| **Frontend** | HTML, CSS, JavaScript (Chart.js) |
| **Database** | SQLite / MySQL |
| **Data Sources** | NISR Datasets, Open-Meteo API, Manual Market Inputs |

---

## 📊 Data & Dashboards

### 🧑‍🌾 Farmer Dashboard

**Purpose:** Empower farmers with actionable information and tools.

**Features:**

- 🌦 **Weather Forecast**  
  Displays daily temperature and rainfall using **Open-Meteo API**.

- 📈 **Market Prices**  
  Shows recent market prices for common commodities.

- 📦 **Agro-Dealer Inventory**  
  Farmers can view and order inputs like fertilizers and seeds.

- 🧾 **My Orders**  
  Farmers track their orders and delivery status.

- 🌾 **Publish Crops for Processors**  
  Farmers can publish available harvests for sale to processors.

- 💡 **Farming Tips**  
  Contextual advice generated from weather, market, and sustainability data.

**Interaction:**

- Farmers **register & log in** to access personalized insights.  
- They can **create orders**, **publish crop offers**, and **view charts interactively**.  
- When clicked, each dashboard section **appears centered** for clear focus.

---

### 🧪 Researcher Dashboard

**Purpose:** Help researchers analyze market and agricultural data.

**Features:**

- 📈 **Price Trend Graphs**  
  Charts showing commodity price variations.

- 📉 **Histograms**  
  Price frequency distribution visualizations.

- 📂 **NISR Dataset Integration**  
  Researchers can **download official CSV data** directly from the platform.  
  (The dataset is read from local CSV files, not stored in the database.)

**Interaction:**

- Researchers can **visualize trends**, **download data**, and **compare variables** for analysis.

---

### 🧑‍🌾 Agro-Dealer Dashboard

**Purpose:** Manage input supply and farmer orders.

**Features:**

- 📦 **Inventory Management**  
  View and update stock of fertilizers, seeds, and pesticides.

- 🛒 **Order Requests**  
  Receive and approve orders placed by farmers.

- 📢 **Policy & Subsidy Updates**  
  View government policies or subsidies affecting agricultural trade.

**Interaction:**

- Dealers **log in** to manage stock, process farmer orders, and update availability.  
- Updated inventory appears on the **Farmer Dashboard** automatically.

---

### 🏭 Processor & Customer Dashboard

**Purpose:** Connect processors directly to farmers for crop acquisition.

**Features:**

- 🌾 **Available Crops**  
  Lists all published crop offers from farmers.

- 📜 **Quality Certifications**  
  Displays certified crop products and standards compliance.

- 🚚 **Logistics & Delivery**  
  Manages order deliveries and transportation schedules.

**Interaction:**

- Processors can **view, request, and purchase** crops directly.  
- They can track **order logistics** and manage quality data.

---

## 👥 User Roles & Permissions

| Role | Description | Key Abilities |
|------|--------------|----------------|
| 👨‍🌾 **Farmer** | Produces and sells crops | View forecasts, order inputs, publish crops, approve processor orders |
| 🧑‍🌾 **Agro-Dealer** | Supplies inputs to farmers | Manage stock, approve farmer orders, view policy updates |
| 🏭 **Processor & Customer** | Purchases crops from farmers | Browse and order crops, track logistics |
| 🧑‍🔬 **Researcher** | Analyzes agricultural and market data | View graphs, download datasets, study market trends |

---

## 🔐 User Authentication

### 📝 Create Account
1. Navigate to `/register`.
2. Choose your **role** (Farmer, Agro-Dealer, Processor, Researcher).
3. Fill in your details (Full Name, Email, Password, etc.).
4. Submit the form to create an account.

### 🔑 Login
1. Visit `/login`.
2. Enter your email and password.
3. You’ll be redirected to your **role-specific dashboard**.

> Each user only sees data relevant to their role.

---

## 🧠 How Users Interact

| Action | From | To | Description |
|--------|------|----|-------------|
| Place order | Farmer | Agro-Dealer | Farmer orders seeds, fertilizers, etc. |
| Publish crop | Farmer | Processor | Farmer lists available crops for sale |
| Approve order | Dealer or Farmer | System | Approve or reject pending orders |
| Analyze data | Researcher | NISR Dataset | Researcher downloads & visualizes CSV |
| Update stock | Agro-Dealer | Database | Dealer updates current inventory |
| Manage logistics | Processor | Farmer | Track delivery and payment status |

---

## 📈 Information Communicated

The platform communicates:
- 🌾 **Agricultural intelligence**: Market demand, price fluctuations, crop availability  
- 🌦 **Environmental insights**: Weather trends and rainfall forecasts  
- 📦 **Supply chain data**: Input availability and order flow  
- 📊 **Research insights**: Data-driven evidence for policy and productivity improvement  

---

## 🧩 Example Data Sources

| Data Type | Source | Example |
|------------|---------|----------|
| Weather Forecast | Open-Meteo API | Daily temp & rainfall by province |
| Market Prices | CSV or manual input | Maize = 500 RWF/kg |
| NISR Dataset | Official CSV | Crop yield and production |
| Inventory | Agro-Dealer input | 100 bags Urea Fertilizer |
| Orders | Platform DB | Farmer A → 10 bags Maize Seeds |

---

## 🤖 UMUHUZA - Assistant

The landing page now includes **UMUHUZA - Assistant**, an AI chatbot tailored to this platform. It answers onboarding questions, explains dashboards, and guides farmers, agro-dealers, processors, and policymakers.

1. Click the green chat bubble to open the assistant.
2. Ask about services, weather data, market prices, or account steps.
3. Close the panel or press `Esc` to hide it.

### Backend configuration

1. Copy `env.example` to `.env` (never commit `.env`):
   ```
   cp env.example .env
   ```
   Update the values (`GROQ_API_KEY`, DB credentials, mail settings, etc.).
2. Install dependencies: `pip install -r requirements.txt`
3. Restart the Flask server. The new `/chat` endpoint now uses Groq’s free Llama models plus UMUHUZA’s knowledge base.

> ⚠️ Never paste the API key into HTML, JavaScript, GitHub, or public docs.

### Retrieval-Augmented Generation (RAG)

1. **Create the table** (done):
   ```sql
   CREATE TABLE knowledge_base (
       id INT AUTO_INCREMENT PRIMARY KEY,
       content TEXT NOT NULL,
       embedding JSON NOT NULL
   );
   ```
2. **Seed embeddings** from `chatbot_knowledge_base.json` (uses a hashing vectorizer, no API cost):
   ```bash
   python scripts/seed_knowledge_base.py
   ```
   The script reads every UMUHUZA snippet, skips any text mentioning other brands, converts them into deterministic TF-style hash embeddings (default 4096 dimensions), and stores them in MySQL.
3. **Chat flow**:
   - `/chat` embeds the user question
   - Fetches the top matching snippets via cosine similarity
   - Sends the context + question to OpenAI for a grounded answer
4. **Updating knowledge**:
   - Edit `chatbot_knowledge_base.json`
   - Re-run the seed script to refresh embeddings
   - No code changes required

Keep `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` in `.env` so both Flask and the seeding script use the same credentials. Set `GROQ_API_KEY` (for chat) and `KNOWLEDGE_EMBED_DIM` if you want a different hashing dimension.

---
Interact Here: https://ikiraro1.vercel.app/
## 🧭 Navigation Map

