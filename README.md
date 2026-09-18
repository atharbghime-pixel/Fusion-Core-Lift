# Fusion Core Lift — Smart Fitness Assistant

A beginner-friendly Flask college project that turns a fitness profile into transparent, rule-based fitness metrics, a weekly workout, and daily meal ideas. It stores profiles and generated plans in SQLite, so data remains after restarting the app.

## Features

- Validated registration form (server-side validation is authoritative)
- SQLite storage created automatically at startup
- BMI, calorie, protein, water, and sleep estimates
- Goal and fitness-level based weekly workout plans
- Vegetarian and non-vegetarian meal ideas
- Injury-aware safety messages and low-impact guidance
- Responsive Bootstrap-based interface
- Read-only API endpoints plus a delete endpoint for demo/testing

## Technology stack

- Python 3 and Flask
- SQLite (`sqlite3`, included with Python)
- HTML5, CSS3, JavaScript, Bootstrap 5 CDN, Jinja2

## Folder structure

```
FusionCoreLift/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── database.db              # created automatically; intentionally not committed
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── dashboard.html
│   ├── workout.html
│   └── diet.html
└── static/
    ├── style.css
    └── script.js
```

## Installation and running on Windows

Open a terminal inside `FusionCoreLift`.

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

If `python` is not recognized, use:

```powershell
py -m venv venv
venv\Scripts\activate
py -m pip install -r requirements.txt
py app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Demo input

Use this for a quick demo:

| Field | Value |
|---|---|
| Name | Test User |
| Age | 20 |
| Height | 170 cm |
| Weight | 65 kg |
| Gender | Male |
| Goal | Muscle Gain |
| Fitness level | Beginner |
| Diet | Vegetarian |
| Injury | None |

## Test procedure

1. Start the app: the first run creates `database.db` and both tables automatically.
2. Open the home page and select **Get Started**.
3. Submit the demo input above. You should land on a dashboard with BMI (22.5), calorie, protein, water, and sleep cards.
4. Select **View Workout**; the saved weekly plan should be displayed.
5. Select **View Diet**; four saved meal ideas should be displayed.
6. Try age `12`, height `300`, weight `10`, or blank required fields. The registration page should show friendly validation errors.
7. Visit `/dashboard/999999`; the app should return you to profile creation rather than crash.
8. Restart Flask and visit `/users`; your previously created profiles remain listed.
9. Visit `/health`; expected response: `{"status":"healthy"}`.

## Database and API notes

The database has `users` and `plans` tables, connected with a foreign key and cascade deletion. All SQL uses parameterized queries. No passwords or authentication are used in this first version.

- `GET /health` — health check
- `GET /users` — profile summary list
- `GET /users/<id>` — one profile
- `DELETE /users/<id>` — delete a profile and related plan (testing only)

## Common errors

- **`python` is not recognized:** use the `py` commands above.
- **`ModuleNotFoundError: flask`:** activate `venv`, then run `python -m pip install -r requirements.txt`.
- **Port 5000 is in use:** stop the other Flask process, or change the last line of `app.py` to `app.run(debug=True, port=5001)`.
- **Database reset desired:** stop the app and delete only `database.db`; it is automatically recreated on the next run. This deletes saved profiles.

## Disclaimer

Fusion Core Lift provides general fitness and nutrition estimates for informational purposes only. It is not a substitute for professional medical or nutritional advice. If you have an injury, medical condition, or health concern, consult a qualified healthcare professional.

## Future enhancements

Potential future improvements include authentication, exercise videos, advanced tracking, wearable support, and professionally reviewed programs. They are intentionally out of scope for this reliable local prototype.
