import os
from typing import Optional

import streamlit as st
from groq import Groq

st.set_page_config(page_title="AI Meal & Fitness Planner", page_icon="🥗", layout="centered")

DEFAULT_MODEL = "llama-3.3-70b-versatile"
MODEL_OPTIONS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
]

ACTIVITY = {
    "Sedentary (little or no exercise)": 1.2,
    "Light (1-3 days/week)": 1.375,
    "Moderate (3-5 days/week)": 1.55,
    "Very active (6-7 days/week)": 1.725,
}
GOALS = ["Lose weight", "Maintain weight", "Gain muscle / weight"]
DIETS = ["No restriction", "Vegetarian", "High protein", "Low carb"]
CUISINES = ["Pakistani / Desi", "Mixed (Desi + International)", "International"]
EQUIPMENT = ["No equipment (home)", "Basic dumbbells / bands", "Full gym"]
LEVELS = ["Beginner", "Intermediate", "Advanced"]


# ---------- Helpers ----------
def get_api_key() -> Optional[str]:
    try:
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY")


def calc_bmi(weight_kg: float, height_cm: float) -> float:
    h = height_cm / 100
    return weight_kg / (h * h)


def bmi_label(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def calc_calories(gender: str, age: int, weight_kg: float, height_cm: float, activity: float, goal: str):
    """Mifflin-St Jeor BMR -> TDEE -> goal-adjusted target."""
    if gender == "Male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    tdee = bmr * activity

    if goal == "Lose weight":
        target = tdee - 500
    elif goal == "Gain muscle / weight":
        target = tdee + 300
    else:
        target = tdee

    floor = 1500 if gender == "Male" else 1200  # safety floor
    target = max(target, floor)
    return round(bmr), round(tdee), round(target)


def build_prompt(d: dict) -> str:
    return f"""Create a personalized 7-day meal plan and workout plan.

USER PROFILE
- Age: {d['age']}, Gender: {d['gender']}
- Height: {d['height']} cm, Weight: {d['weight']} kg
- BMI: {d['bmi']:.1f} ({d['bmi_label']})
- Goal: {d['goal']}
- Daily calorie target: {d['target']} kcal (maintenance is about {d['tdee']} kcal)
- Diet preference: {d['diet']}
- Cuisine: {d['cuisine']}
- Allergies / foods to avoid: {d['allergies'] or 'None'}
- Meals per day: {d['meals']}
- Daily food budget: about {d['budget']} PKR
- Fitness level: {d['level']}
- Workout days per week: {d['workout_days']}
- Equipment: {d['equipment']}

FORMAT (Markdown):

## 📊 Your Numbers
Calories, and daily protein / carbs / fat targets in grams that match the calorie target.

## 🍽️ 7-Day Meal Plan
For each day, list every meal with portion sizes (use household measures like 1 roti, 1 cup rice, 2 eggs) and approximate calories. Show the daily total. Keep meals affordable within the budget and use easily available local ingredients. Repeat meals where sensible to keep shopping simple.

## 🏋️ Weekly Workout Plan
Exactly {d['workout_days']} workout days plus rest/active-recovery days. For each workout day: exercises, sets x reps, rest time, and approximate duration. Match the level and equipment. Include a short warm-up and cool-down.

## 🛒 Weekly Grocery List
Grouped by category (grains, protein, vegetables, fruit, dairy, other).

## 💧 Daily Habits
Water, sleep, steps, and 4-5 practical tips for this goal.

## ⚠️ Safety Notes
Short reminder that this is general guidance, not medical advice, and to see a doctor or dietitian for medical conditions, pregnancy, or if under 18.

Keep numbers realistic and consistent with the calorie target. Do not promise specific results."""


def stream_plan(api_key: str, model: str, prompt: str, temperature: float):
    client = Groq(api_key=api_key)
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a certified nutrition and fitness coach. You give safe, realistic, "
                    "budget-aware meal and workout plans and never give extreme or unsafe advice."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=6000,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = get_api_key()
    if not api_key:
        api_key = st.text_input("Groq API Key", type="password", help="Free key at console.groq.com")
    else:
        st.success("API key loaded")
    model = st.selectbox("Model", MODEL_OPTIONS, index=MODEL_OPTIONS.index(DEFAULT_MODEL))
    temperature = st.slider("Creativity", 0.0, 1.0, 0.5, 0.1)
    st.caption("Powered by Groq + Streamlit")

# ---------- Main UI ----------
st.title("🥗 AI Meal & Fitness Planner")
st.write("Fill in your details and get a personalized 7-day meal plan, workout plan, and grocery list.")

with st.form("planner_form"):
    st.subheader("About you")
    c1, c2, c3 = st.columns(3)
    age = c1.number_input("Age", min_value=14, max_value=90, value=22)
    gender = c2.selectbox("Gender", ["Male", "Female"])
    level = c3.selectbox("Fitness level", LEVELS)

    c4, c5 = st.columns(2)
    height = c4.number_input("Height (cm)", min_value=120, max_value=220, value=170)
    weight = c5.number_input("Weight (kg)", min_value=30.0, max_value=250.0, value=70.0, step=0.5)

    st.subheader("Goal & lifestyle")
    goal = st.selectbox("Goal", GOALS)
    activity_label = st.selectbox("Activity level", list(ACTIVITY.keys()), index=1)

    c6, c7 = st.columns(2)
    workout_days = c6.slider("Workout days per week", 2, 6, 4)
    equipment = c7.selectbox("Equipment", EQUIPMENT)

    st.subheader("Food preferences")
    c8, c9 = st.columns(2)
    diet = c8.selectbox("Diet type", DIETS)
    cuisine = c9.selectbox("Cuisine", CUISINES)

    c10, c11 = st.columns(2)
    meals = c10.slider("Meals per day", 3, 6, 4)
    budget = c11.number_input("Daily food budget (PKR)", min_value=200, max_value=10000, value=800, step=100)

    allergies = st.text_input("Allergies / foods to avoid (optional)", placeholder="e.g. peanuts, lactose, no beef")

    submitted = st.form_submit_button("🚀 Generate My Plan", type="primary", use_container_width=True)

if submitted:
    if not api_key:
        st.error("Please add your Groq API key in the sidebar or in Streamlit secrets.")
    else:
        bmi = calc_bmi(weight, height)
        bmr, tdee, target = calc_calories(gender, int(age), weight, height, ACTIVITY[activity_label], goal)

        m1, m2, m3 = st.columns(3)
        m1.metric("BMI", f"{bmi:.1f}", bmi_label(bmi))
        m2.metric("Maintenance", f"{tdee} kcal")
        m3.metric("Daily target", f"{target} kcal")

        if age < 18:
            st.info("You are under 18. Please check with a doctor or parent before changing your diet.")

        data = {
            "age": int(age), "gender": gender, "height": height, "weight": weight,
            "bmi": bmi, "bmi_label": bmi_label(bmi), "goal": goal, "target": target,
            "tdee": tdee, "diet": diet, "cuisine": cuisine, "allergies": allergies.strip(),
            "meals": meals, "budget": int(budget), "level": level,
            "workout_days": workout_days, "equipment": equipment,
        }

        try:
            with st.spinner("Building your plan..."):
                placeholder = st.empty()
                text = ""
                for piece in stream_plan(api_key, model, build_prompt(data), temperature):
                    text += piece
                    placeholder.markdown(text)
            st.session_state["plan"] = text
        except Exception as e:
            st.error(f"Something went wrong: {e}")

if st.session_state.get("plan"):
    st.download_button(
        "⬇️ Download plan (.md)",
        data=st.session_state["plan"],
        file_name="my_meal_and_fitness_plan.md",
        mime="text/markdown",
    )

st.caption("General guidance only, not medical advice. Consult a doctor or dietitian for health conditions.")
