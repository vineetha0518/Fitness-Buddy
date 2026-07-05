# Fitness Buddy 🏋️‍♂️

**AI-Powered Fitness Coach** built with Python Flask & IBM Watsonx.ai Granite Models.

> Personalized workouts · Indian nutrition plans · BMI & calorie tracking · 24/7 AI coaching

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 IBM Granite AI | Powered by `ibm/granite-3-8b-instruct` via Watsonx.ai |
| 💬 AI Chat | Conversational fitness coach with multi-turn memory |
| 🏋️ Workout Planner | Beginner → Advanced home workouts with sets/reps/rest |
| 🥗 Indian Nutrition | Regional meal suggestions with calories & macros |
| ⚖️ BMI Calculator | WHO-standard BMI with health risk assessment |
| 🔥 TDEE Calculator | Mifflin-St Jeor BMR + activity-adjusted calorie target |
| 📅 Weekly Planner | 7-day structured workout schedule |
| 📊 Progress Dashboard | Streak tracking, achievements, charts |
| 🌙 Dark Mode | System-aware + manual toggle |
| 📱 Responsive | Mobile-first Bootstrap 5 design |

---

## 🗂️ Project Structure

```
FitnessBuddy/
├── app.py                    # Flask app, all routes
├── requirements.txt
├── .env.example              # Template — copy to .env
├── README.md
├── services/
│   ├── granite_client.py     # IBM Watsonx.ai API client
│   └── fitness_agent.py      # Prompt engineering + AGENT_INSTRUCTIONS
├── templates/
│   └── index.html            # SPA template (all sections)
├── static/
│   ├── css/style.css         # Custom styles
│   └── js/script.js          # Frontend logic
├── utils/
│   ├── bmi.py                # BMI calculator
│   ├── calorie.py            # TDEE / BMR calculator
│   └── workout.py            # Workout plan builder
└── data/
    ├── workouts.json         # Exercise database
    └── indian_meals.json     # Indian meal database
```

---

## 🚀 Quick Start (Local)

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/fitness-buddy.git
cd fitness-buddy/FitnessBuddy
```

### 2. Create a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and fill in your IBM Cloud credentials:
```env
IBM_API_KEY=your_ibm_cloud_api_key_here
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
IBM_PROJECT_ID=your_watsonx_project_id_here
IBM_MODEL_ID=ibm/granite-3-8b-instruct
FLASK_SECRET_KEY=a-random-secret-key-here
```

### 5. Run the application
```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 🔑 Getting IBM Watsonx.ai Credentials

### Step 1 — IBM Cloud Account
1. Sign up at [cloud.ibm.com](https://cloud.ibm.com) (Lite tier is free)
2. Create an **API Key**: Profile → Manage → API keys → Create

### Step 2 — IBM Watsonx.ai Project
1. Go to [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
2. Create a new project → copy the **Project ID** from Project Settings

### Step 3 — Enable Watsonx.ai
1. In your IBM Cloud dashboard, search for **Watson Machine Learning**
2. Create a Lite instance and associate it with your project

---

## 🎨 Customising the AI Personality

All AI behaviour is controlled by the **`AGENT_INSTRUCTIONS`** dict in [`services/fitness_agent.py`](services/fitness_agent.py):

```python
AGENT_INSTRUCTIONS = {
    "name":               "FitBot",          # AI's name
    "personality":        "...",             # Core personality description
    "motivation_style":   "...",             # How it motivates users
    "specialization":     "...",             # Fitness expertise focus
    "nutrition_focus":    "...",             # Food/nutrition preferences
    "intensity_guidance": "...",             # Workout intensity rules
    "language_tone":      "...",             # Communication style
    "response_format":    "...",             # How to structure responses
    "safety_guidelines":  "...",             # Non-negotiable safety rules
    "regional_awareness": "...",             # Indian regional context
    "scope":              "...",             # Topic boundaries
}
```

Simply edit any value — no other code changes needed.

---

## 🌐 Deployment

### Option A — Render (Free tier)

1. Push your project to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `gunicorn app:app`
6. Add environment variables in Render dashboard
7. Deploy!

### Option B — IBM Cloud (Code Engine)

```bash
# Install IBM Cloud CLI
# Login
ibmcloud login --apikey YOUR_API_KEY

# Build container
ibmcloud ce application create \
  --name fitness-buddy \
  --image us.icr.io/your-namespace/fitness-buddy \
  --port 5000 \
  --env IBM_API_KEY=xxx \
  --env IBM_PROJECT_ID=xxx \
  --env IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

### Option C — Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
```

```bash
docker build -t fitness-buddy .
docker run -p 5000:5000 --env-file .env fitness-buddy
```

---

## 🔒 Security Notes

- **Never commit `.env`** — it's in `.gitignore`
- Use `FLASK_SECRET_KEY` with a long random string in production
- Set `FLASK_DEBUG=False` in production
- Consider adding Flask-Session or Redis for persistent user data in production

---

## ⚕️ Medical Disclaimer

> This application is for **informational and educational purposes only**. It is **not a substitute for professional medical advice**, diagnosis, or treatment. Always consult a qualified healthcare professional before beginning any new exercise or diet program, especially if you have existing medical conditions, are pregnant, or are over 60 years of age.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Flask 3.0 |
| AI | IBM Watsonx.ai, IBM Granite 3 8B Instruct |
| Frontend | Bootstrap 5.3, Chart.js 4 |
| Icons | Bootstrap Icons 1.11 |
| Auth | IAM Token (IBM Cloud) |
| Deployment | Gunicorn, Render / IBM Code Engine |

---

## 📝 License

MIT — free for personal and educational use.

---

*Built for IBM SkillsBuild Hackathon 2024–25*
