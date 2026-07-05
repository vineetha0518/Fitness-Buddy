# 🏋️ Fitness Buddy – AI Powered Virtual Fitness Coach

Fitness Buddy is an AI-powered virtual fitness assistant built using **Python Flask** and **IBM Watsonx.ai Granite Models**. It provides personalized workout recommendations, Indian nutrition guidance, BMI and calorie calculations, progress tracking, and an interactive AI chatbot to help users maintain a healthy lifestyle.

---

## 🚀 Features

### 🤖 AI Fitness Coach
- Conversational AI powered by IBM Watsonx.ai Granite
- Personalized workout recommendations
- Daily fitness motivation
- Exercise and wellness guidance

### 💪 Workout Planner
- Beginner, Intermediate, and Advanced workouts
- Home workout recommendations
- Weekly workout planner
- Warm-up and cool-down routines

### 🥗 Nutrition Assistant
- Healthy Indian meal suggestions
- Personalized meal planning
- Calorie and nutrition recommendations
- Diet preference support

### 📊 Health Calculators
- BMI Calculator
- Daily Calorie Requirement (BMR/TDEE)
- Health recommendations based on BMI

### 📈 Progress Dashboard
- Workout history
- Daily streak tracker
- Calories burned tracking
- Achievement badges

### 👤 User Profile
- Store fitness information
- Set fitness goals
- Diet preferences
- Workout preferences

### 🎨 Modern User Interface
- Responsive Bootstrap 5 design
- Dark/Light mode
- Mobile-friendly layout
- Interactive dashboard
- AI Chat Interface

---

# 🛠 Technologies Used

- Python 3.11+
- Flask
- IBM Watsonx.ai
- IBM Granite Models
- Bootstrap 5
- JavaScript
- HTML5
- CSS3
- Chart.js
- Python Dotenv

---

# 📁 Project Structure

```
FitnessBuddy/
│
├── app.py
├── requirements.txt
├── .env
├── README.md
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/
│
├── services/
│   ├── granite_client.py
│   └── fitness_agent.py
│
├── utils/
│   ├── bmi.py
│   ├── calorie.py
│   └── workout.py
│
└── data/
    ├── workouts.json
    └── indian_meals.json
```

---

# ⚙️ Installation

## Clone the Repository

```bash
git clone https://github.com/yourusername/FitnessBuddy.git

cd FitnessBuddy
```

---

## Create Virtual Environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Configure Environment Variables

Create a `.env` file in the project root.

```env
IBM_API_KEY=YOUR_API_KEY

IBM_PROJECT_ID=YOUR_PROJECT_ID

IBM_URL=https://us-south.ml.cloud.ibm.com
```

---

# ▶ Run the Application

```bash
python app.py
```

The application will start at

```
http://127.0.0.1:5000
```

---

# 📌 IBM Watsonx.ai Setup

1. Create an IBM Cloud Account.
2. Create a Watsonx.ai Project.
3. Generate an IBM Cloud API Key.
4. Copy your:
   - IBM_API_KEY
   - IBM_PROJECT_ID
   - IBM_URL
5. Add them to the `.env` file.

---

# 📸 Modules

- Home Page
- Dashboard
- Workout Planner
- Nutrition Planner
- BMI Calculator
- Calorie Calculator
- Weekly Planner
- Progress Tracker
- AI Chatbot
- User Profile

---

# 📱 Responsive Design

The application supports:

- Desktop
- Laptop
- Tablet
- Mobile Devices

---

# 🔒 Safety

Fitness Buddy provides general fitness and nutrition guidance only.

It is **not a substitute for professional medical advice**. Users should consult qualified healthcare professionals before starting any new exercise or diet program.

---

# 👨‍💻 Developed For

**IBM SkillsBuild Internship**

Problem Statement No.13

**Fitness Buddy – AI Powered Virtual Fitness Coach**

---

# Future Enhancements

- Voice Assistant
- Wearable Device Integration
- AI Exercise Detection
- Water Intake Tracker
- Sleep Monitoring
- Step Counter
- Push Notifications
- Multi-language Support

---

# License

This project is developed for educational and Internship purposes.
