"""Repeatable end-to-end checks for Fusion Core Lift (no external test package)."""
import os
import re
import sqlite3
import tempfile

import app as app_module
from app import app, db_connection, init_db


def run_tests():
    """Exercise all required routes using a new temporary SQLite database."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        app_module.DATABASE = os.path.join(temporary_directory, "database.db")
        init_db()
        assert os.path.exists(app_module.DATABASE), "Database was not created"
        with db_connection() as connection:
            tables = {row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            assert {"users", "plans"}.issubset(tables), "Tables were not created"
            try:
                connection.execute("INSERT INTO users (name, age, height, weight, gender, goal, fitness_level, diet) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                   ("", 20, 170, 65, "Male", "Muscle Gain", "Beginner", "Vegetarian"))
            except sqlite3.IntegrityError:
                pass
            else:
                raise AssertionError("Database accepted an invalid profile")

        client = app.test_client()
        assert client.get("/").status_code == 200
        assert client.get("/register").status_code == 200
        profile = {"name": "Test User", "age": "20", "height": "170", "weight": "65",
                   "gender": "Male", "goal": "Muscle Gain", "fitness_level": "Beginner",
                   "diet": "Vegetarian", "injury": "None"}
        registration = client.post("/register", data=profile, follow_redirects=False)
        assert registration.status_code == 302
        dashboard_url = registration.headers["Location"]
        user_id = int(dashboard_url.rsplit("/", 1)[1])

        with db_connection() as connection:
            assert connection.execute("SELECT COUNT(*) FROM users WHERE id = ?", (user_id,)).fetchone()[0] == 1
            assert connection.execute("SELECT COUNT(*) FROM plans WHERE user_id = ?", (user_id,)).fetchone()[0] == 1
            indexes = {row["name"] for row in connection.execute("PRAGMA index_list('plans')")}
            assert "idx_plans_user_id" in indexes, "Plan lookup index was not created"

        dashboard = client.get(dashboard_url)
        assert dashboard.status_code == 200
        for expected in (b"22.5", b"2241", b"104g", b"2.3L"):
            assert expected in dashboard.data, f"Missing metric {expected!r}"
        assert client.get(f"/workout/{user_id}").status_code == 200
        assert client.get(f"/diet/{user_id}").status_code == 200
        for link in re.findall(rb'href="([^"]+)"', dashboard.data):
            target = link.decode()
            if target.startswith("/"):
                assert client.get(target).status_code == 200, target

        for change in ({"age": "12"}, {"height": "300"}, {"height": "nan"}, {"weight": "10"}, {"weight": "inf"}, {"name": ""}):
            assert client.post("/register", data={**profile, **change}).status_code == 200
        for unknown_path in ("/dashboard/999999", "/workout/999999", "/diet/999999"):
            assert client.get(unknown_path).status_code == 302

        count_before_refresh = len(client.get("/users").get_json())
        client.get(dashboard_url)
        assert len(client.get("/users").get_json()) == count_before_refresh
        init_db()  # Represents an application restart; user data must remain.
        assert len(client.get("/users").get_json()) == count_before_refresh

        injured = client.post("/register", data={**profile, "name": "Knee Test", "injury": "knee pain"}, follow_redirects=False)
        injury_page = client.get(injured.headers["Location"])
        assert b"Low-impact plan" in injury_page.data and b"Chair squat" not in injury_page.data
        assert client.get("/health").get_json() == {"status": "healthy"}


if __name__ == "__main__":
    run_tests()
    print("All Fusion Core Lift checks passed.")
