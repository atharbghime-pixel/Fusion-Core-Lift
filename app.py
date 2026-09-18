from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for
import json
import os
import sqlite3

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "fusion-core-lift-local-key")
DATABASE = os.path.join(os.path.dirname(__file__), "database.db")

VALID_GENDERS = {"Male", "Female", "Other"}
VALID_GOALS = {"Weight Loss", "Muscle Gain", "General Fitness"}
VALID_LEVELS = {"Beginner", "Intermediate", "Advanced"}
VALID_DIETS = {"Vegetarian", "Non-Vegetarian"}


def get_db_connection():
    """Return a SQLite connection with safe rows and foreign keys enabled."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with get_db_connection() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                height REAL NOT NULL,
                weight REAL NOT NULL,
                gender TEXT NOT NULL,
                goal TEXT NOT NULL,
                fitness_level TEXT NOT NULL,
                diet TEXT NOT NULL,
                injury TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                workout_plan TEXT NOT NULL,
                diet_plan TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)


def validate_profile(data):
    name = data.get("name", "").strip()
    injury = data.get("injury", "").strip()
    errors = []
    if not name:
        errors.append("Please enter your name.")
    try:
        age = int(data.get("age", ""))
        if not 13 <= age <= 100:
            raise ValueError
    except (TypeError, ValueError):
        errors.append("Please enter a valid age between 13 and 100.")
        age = None
    try:
        height = float(data.get("height", ""))
        if not 50 <= height <= 250:
            raise ValueError
    except (TypeError, ValueError):
        errors.append("Please enter a valid height between 50 and 250 cm.")
        height = None
    try:
        weight = float(data.get("weight", ""))
        if not 20 <= weight <= 400:
            raise ValueError
    except (TypeError, ValueError):
        errors.append("Please enter a valid weight between 20 and 400 kg.")
        weight = None
    for field, allowed, label in [
        ("gender", VALID_GENDERS, "gender"), ("goal", VALID_GOALS, "fitness goal"),
        ("fitness_level", VALID_LEVELS, "fitness level"), ("diet", VALID_DIETS, "diet preference")
    ]:
        if data.get(field) not in allowed:
            errors.append(f"Please select a valid {label}.")
    cleaned = {"name": name, "age": age, "height": height, "weight": weight,
               "gender": data.get("gender"), "goal": data.get("goal"),
               "fitness_level": data.get("fitness_level"), "diet": data.get("diet"),
               "injury": injury}
    return cleaned, errors


def calculate_metrics(user):
    bmi = round(user["weight"] / ((user["height"] / 100) ** 2), 1)
    category = "Underweight" if bmi < 18.5 else "Normal" if bmi < 25 else "Overweight" if bmi < 30 else "Obesity"
    gender_adjustment = 5 if user["gender"] == "Male" else -161 if user["gender"] == "Female" else -78
    bmr = 10 * user["weight"] + 6.25 * user["height"] - 5 * user["age"] + gender_adjustment
    multiplier = {"Beginner": 1.2, "Intermediate": 1.375, "Advanced": 1.55}[user["fitness_level"]]
    goal_adjustment = {"Weight Loss": -300, "Muscle Gain": 300, "General Fitness": 0}[user["goal"]]
    calories = max(1200, round(bmr * multiplier + goal_adjustment))
    protein = round(user["weight"] * {"Weight Loss": 1.4, "Muscle Gain": 1.6, "General Fitness": 1.2}[user["goal"]])
    return {"bmi": bmi, "bmi_category": category, "calories": calories,
            "protein": protein, "water": round(user["weight"] * 0.035, 1), "sleep": "7–9 hours"}


def injury_note(injury):
    text = injury.lower().strip()
    if not text or text == "none":
        return None
    if "knee" in text or "ankle" in text:
        return "Low-impact plan: avoid jumping and deep/high-volume squats; choose comfortable walking, gentle mobility, and upper-body work."
    if "shoulder" in text or "wrist" in text:
        return "Modify or avoid push-ups and overhead movements; prioritize comfortable lower-body and gentle mobility work."
    if "back" in text:
        return "Avoid loaded bending and high-impact work; choose gentle mobility and exercises that feel comfortable."
    return "This plan uses a cautious approach. Avoid movements that cause pain and consult a qualified professional for injury-specific guidance."


def generate_workout(user):
    level = user["fitness_level"]
    cardio = {"Beginner": "20 min brisk walk", "Intermediate": "30 min brisk walk/cycle", "Advanced": "35 min cardio intervals"}[level]
    # Each goal and level gets a distinct, progressively harder exercise selection.
    plans = {
        "Beginner": {
            "Weight Loss": [("Bodyweight squat", "2 sets", "10–15 reps"), ("Wall push-up", "2 sets", "8–12 reps"), ("Glute bridge", "2 sets", "12 reps"), ("Plank", "2 sets", "20 sec")],
            "Muscle Gain": [("Chair squat", "2 sets", "8–12 reps"), ("Incline push-up", "2 sets", "8–12 reps"), ("Reverse lunge", "2 sets", "8 each side"), ("Glute bridge", "2 sets", "12–15 reps")],
            "General Fitness": [("Bodyweight squat", "2 sets", "10 reps"), ("Wall push-up", "2 sets", "10 reps"), ("Bird-dog", "2 sets", "8 each side"), ("Plank", "2 sets", "20 sec")]
        },
        "Intermediate": {
            "Weight Loss": [("Squat", "3 sets", "15 reps"), ("Incline push-up", "3 sets", "10–12 reps"), ("Step-up", "3 sets", "10 each side"), ("Mountain climber", "3 sets", "20 sec")],
            "Muscle Gain": [("Tempo squat", "3 sets", "10–12 reps"), ("Push-up", "3 sets", "8–12 reps"), ("Reverse lunge", "3 sets", "10 each side"), ("Single-leg glute bridge", "3 sets", "10 each side")],
            "General Fitness": [("Goblet squat (light)", "3 sets", "12 reps"), ("Incline push-up", "3 sets", "10 reps"), ("Step-up", "3 sets", "10 each side"), ("Dead bug", "3 sets", "10 each side")]
        },
        "Advanced": {
            "Weight Loss": [("Squat to calf raise", "4 sets", "15 reps"), ("Push-up", "4 sets", "12–15 reps"), ("Alternating reverse lunge", "4 sets", "12 each side"), ("High plank shoulder tap", "4 sets", "20 taps")],
            "Muscle Gain": [("Pause squat", "4 sets", "8–10 reps"), ("Decline or standard push-up", "4 sets", "10–15 reps"), ("Split squat", "4 sets", "10 each side"), ("Single-leg hip thrust", "4 sets", "10 each side")],
            "General Fitness": [("Squat", "4 sets", "15 reps"), ("Push-up", "4 sets", "12 reps"), ("Reverse lunge", "4 sets", "12 each side"), ("Plank", "4 sets", "40 sec")]
        }
    }
    strength = list(plans[level][user["goal"]])
    # Simple keyword handling changes the actual plan as well as showing a safety warning.
    injury_text = user["injury"].lower()
    if "knee" in injury_text or "ankle" in injury_text:
        strength = [exercise for exercise in strength if "squat" not in exercise[0].lower() and "lunge" not in exercise[0].lower()]
        strength.append(("Seated leg extension (gentle)", "2 sets", "8–10 reps if comfortable"))
    if "shoulder" in injury_text or "wrist" in injury_text:
        strength = [exercise for exercise in strength if "push" not in exercise[0].lower()]
        strength.append(("Comfortable walking", "1 session", "15–30 min"))
    if "back" in injury_text:
        strength = [exercise for exercise in strength if "squat" not in exercise[0].lower()]
        strength.append(("Gentle mobility", "1 session", "5–10 min"))
    note = injury_note(user["injury"])
    if not strength:
        strength = [("Comfortable walking", "1 session", "15–30 min"), ("Gentle stretching", "1 session", "5–10 min")]
    return {"days": [
        {"day": "Monday", "focus": "Full-body strength", "exercises": strength},
        {"day": "Tuesday", "focus": "Cardio & mobility", "exercises": [(cardio, "1 session", "Comfortable pace"), ("Light stretching", "1 session", "5–10 min")]},
        {"day": "Wednesday", "focus": "Recovery", "exercises": [("Rest or gentle walk", "Optional", "Listen to your body")]},
        {"day": "Thursday", "focus": "Strength", "exercises": strength},
        {"day": "Friday", "focus": "Cardio", "exercises": [(cardio, "1 session", "Comfortable pace")]},
        {"day": "Saturday", "focus": "Full body & stretching", "exercises": strength + [("Light stretching", "1 session", "5–10 min")]},
        {"day": "Sunday", "focus": "Rest & recovery", "exercises": [("Rest", "—", "Prepare for the next week")]}
    ], "injury_note": note}


def generate_diet(user):
    vegetarian = user["diet"] == "Vegetarian"
    goal = user["goal"]
    meals = {
        "Vegetarian": {
            "Weight Loss": [("Breakfast", "Oats with milk, banana, and seeds"), ("Lunch", "Dal, 2 rotis, vegetables, and curd"), ("Snack", "Fruit with yogurt"), ("Dinner", "Paneer/tofu, vegetables, and 1 roti")],
            "Muscle Gain": [("Breakfast", "Oats with milk, banana, nuts, and paneer"), ("Lunch", "Dal, rice/roti, vegetables, and curd"), ("Snack", "Yogurt, fruit, and nuts"), ("Dinner", "Paneer, roti/rice, and vegetables")],
            "General Fitness": [("Breakfast", "Vegetable poha with milk or yogurt"), ("Lunch", "Dal, roti/rice, vegetables, and curd"), ("Snack", "Fruit and a handful of nuts"), ("Dinner", "Paneer/tofu, roti, and vegetables")]
        },
        "Non-Vegetarian": {
            "Weight Loss": [("Breakfast", "Eggs with oats and fruit"), ("Lunch", "Grilled chicken/fish, roti, and vegetables"), ("Snack", "Yogurt and fruit"), ("Dinner", "Fish/chicken with vegetables and a small serving of rice")],
            "Muscle Gain": [("Breakfast", "Eggs, oats, milk, and fruit"), ("Lunch", "Chicken, rice/roti, vegetables, and curd"), ("Snack", "Yogurt, fruit, and nuts"), ("Dinner", "Fish/chicken, rice/roti, and vegetables")],
            "General Fitness": [("Breakfast", "Eggs, oats, and fruit"), ("Lunch", "Chicken/fish, roti/rice, and vegetables"), ("Snack", "Yogurt, fruit, and nuts"), ("Dinner", "Fish/chicken, vegetables, and roti")]
        }
    }
    return {"meals": [{"name": name, "food": food} for name, food in meals["Vegetarian" if vegetarian else "Non-Vegetarian"][goal]],
            "tip": "Aim for balanced portions, regular meals, and adequate hydration. This is general guidance, not a prescribed diet."}


def get_user_and_plan(user_id):
    with get_db_connection() as connection:
        user = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        plan = connection.execute("SELECT * FROM plans WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
    return user, plan


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        profile, errors = validate_profile(request.form)
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html", form=request.form)
        workout, diet = generate_workout(profile), generate_diet(profile)
        with get_db_connection() as connection:
            cursor = connection.execute("""INSERT INTO users (name, age, height, weight, gender, goal, fitness_level, diet, injury)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", tuple(profile.values()))
            user_id = cursor.lastrowid
            connection.execute("INSERT INTO plans (user_id, workout_plan, diet_plan) VALUES (?, ?, ?)",
                               (user_id, json.dumps(workout), json.dumps(diet)))
        flash("User registered successfully. Your personalized plan is ready!", "success")
        return redirect(url_for("dashboard", user_id=user_id))
    return render_template("register.html", form={})


@app.route("/dashboard/<int:user_id>")
def dashboard(user_id):
    user, plan = get_user_and_plan(user_id)
    if not user or not plan:
        flash("We could not find that profile. Please create a new profile.", "warning")
        return redirect(url_for("register"))
    # Plans remain saved as a snapshot, while displayed guidance is regenerated live.
    return render_template("dashboard.html", user=user, metrics=calculate_metrics(user), workout=generate_workout(user), diet=generate_diet(user))


@app.route("/workout/<int:user_id>")
def workout(user_id):
    user, plan = get_user_and_plan(user_id)
    if not user or not plan:
        flash("We could not find that profile. Please create a new profile.", "warning")
        return redirect(url_for("register"))
    return render_template("workout.html", user=user, workout=generate_workout(user))


@app.route("/diet/<int:user_id>")
def diet(user_id):
    user, plan = get_user_and_plan(user_id)
    if not user or not plan:
        flash("We could not find that profile. Please create a new profile.", "warning")
        return redirect(url_for("register"))
    return render_template("diet.html", user=user, metrics=calculate_metrics(user), diet=generate_diet(user))


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/users")
def users():
    with get_db_connection() as connection:
        rows = connection.execute("SELECT id, name, age, goal, fitness_level, created_at FROM users ORDER BY id DESC").fetchall()
    return jsonify([dict(row) for row in rows])


@app.route("/users/<int:user_id>", methods=["GET", "DELETE"])
def user_api(user_id):
    with get_db_connection() as connection:
        user = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404
        if request.method == "DELETE":
            connection.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return jsonify({"message": "User deleted"})
    return jsonify(dict(user))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
