import sqlite3
import random
import uuid
from datetime import datetime, timedelta
import pandas as pd

# ==== CONFIGURATION ====
DB_PATH = "tracking.db"

SAMPLES_PER_CASE = {
    "normal": 200,
    "fast": 100,
    "paste_abuse": 100,
    "hesitant": 100,
    "no_mouse": 100,
    "strategic_fraud": 100,
    "copy_safe": 100,
    "mouse_but_fast": 100,
    "hesitant_legit": 100,
    "hybrid_confusing": 50
}

FIELD_NAMES = ["nom", "prenom", "cin", "adresse", "profession", "revenu", "montant", "duree"]

# ==== DONNÉES FAKE TUNISIENNES ====
tunisian_first_names = ["Ahmed", "Sana", "Khalil", "Fatma", "Nour", "Anis", "Rania", "Yassine"]
tunisian_last_names = ["Ben Ali", "Trabelsi", "Gharbi", "Mzoughi", "Jemni", "Kefi", "Chaabane", "Ayari"]
tunisian_professions = ["Enseignant", "Médecin", "Ingénieur", "Comptable", "Coiffeur", "Chauffeur", "Ouvrier"]
tunisian_cities = ["Tunis", "Sfax", "Sousse", "Gabès", "Nabeul", "Kairouan", "Bizerte", "Mahdia"]

def fake_name():
    return random.choice(tunisian_last_names)

def fake_first_name():
    return random.choice(tunisian_first_names)

def fake_profession():
    return random.choice(tunisian_professions)

def fake_city():
    rue = f"Rue {random.randint(1, 200)}"
    ville = random.choice(tunisian_cities)
    return f"{rue}, {ville}"

def fake_cin():
    return f"{random.randint(10000000, 99999999)}"

# ==== BASE DE DONNÉES ====
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.executescript("""
    DROP TABLE IF EXISTS fields;
    DROP TABLE IF EXISTS sessions;

    CREATE TABLE sessions (
        session_id TEXT PRIMARY KEY,
        start_time INTEGER NOT NULL,
        end_time INTEGER NOT NULL CHECK(end_time > start_time),
        duration_ms INTEGER GENERATED ALWAYS AS (end_time - start_time) STORED,
        mouseMoved INTEGER NOT NULL CHECK(mouseMoved IN (0,1)),
        mouseClickCount INTEGER NOT NULL,
        scrollCount INTEGER NOT NULL,
        viewportChanges INTEGER DEFAULT 0,
        tabCount INTEGER DEFAULT 0,
        enterPressed INTEGER DEFAULT 0,
        deviceType TEXT CHECK(deviceType IN ('desktop','mobile')),
        fieldFocusOrder TEXT,
        label INTEGER NOT NULL CHECK(label IN (0,1)),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE fields (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        field_name TEXT,
        value TEXT,
        timeSpentMs INTEGER NOT NULL,
        hoverDurationMs INTEGER DEFAULT 0,
        copy INTEGER DEFAULT 0,
        paste INTEGER DEFAULT 0,
        delete_count INTEGER DEFAULT 0,
        changes INTEGER DEFAULT 1,
        focusCount INTEGER DEFAULT 1,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    );
    """)
    return conn

# ==== UTILS ====
def permute_order_for_case(case_type):
    order = FIELD_NAMES[:]
    if case_type == "hesitant":
        swaps = random.randint(1, 3)
        for _ in range(swaps):
            i, j = random.sample(range(len(order)), 2)
            order[i], order[j] = order[j], order[i]
    elif case_type in ("fast", "paste_abuse"):
        if random.random() < 0.4:
            i, j = random.sample(range(len(order)), 2)
            order[i], order[j] = order[j], order[i]
    elif case_type == "hybrid_confusing":
        random.shuffle(order)
    return ",".join(order)

def scroll_by_case(case_type):
    if case_type == "fast":
        return random.randint(0, 5)
    if case_type == "no_mouse":
        return random.randint(0, 2)
    if case_type == "normal":
        return random.randint(5, 20)
    if case_type == "paste_abuse":
        return random.randint(5, 25)
    if case_type == "hesitant":
        return random.randint(15, 60)
    return 0

def viewport_by_case(case_type):
    if case_type in ("normal", "hesitant"):
        return random.randint(0, 2)
    if case_type in ("fast", "no_mouse", "paste_abuse"):
        return random.randint(0, 1)
    return 0

def mouse_clicks_by_case(case_type):
    if case_type == "no_mouse":
        return random.randint(0, 1)
    if case_type == "fast":
        return random.randint(1, 4)
    if case_type == "paste_abuse":
        return random.randint(3, 10)
    if case_type == "hesitant":
        return random.randint(5, 15)
    return random.randint(3, 12)

def field_time_by_case(case_type):
    if case_type == "fast":
        return random.randint(200, 900)
    if case_type == "no_mouse":
        return random.randint(800, 2000)
    if case_type == "paste_abuse":
        return random.randint(800, 2500)
    if case_type == "hesitant":
        return random.randint(2000, 6000)
    return random.randint(1500, 4000)

def deletes_by_case(case_type):
    if case_type == "hesitant":
        return random.randint(10, 25)
    if case_type == "fast":
        return random.randint(0, 1)
    return random.randint(1, 5)

# ==== GÉNÉRATION DES CAS ====
def generate_case(conn, case_type):
    params = {
        "normal": {"duration": (30000, 90000), "mouse": 1, "tabs": 0, "label": 0},
        "fast": {"duration": (3000, 7000), "mouse": 1, "tabs": 0, "label": 1},
        "paste_abuse": {"duration": (10000, 20000), "mouse": 1, "tabs": 0, "label": 1},
        "hesitant": {"duration": (60000, 120000), "mouse": 1, "tabs": 0, "label": 1},
        "no_mouse": {"duration": (8000, 15000), "mouse": 0, "tabs": 3, "label": 1},
        "strategic_fraud": {"duration": (40000, 70000), "mouse": 1, "tabs": 0, "label": 1},
        "copy_safe": {"duration": (40000, 80000), "mouse": 1, "tabs": 0, "label": 0},
        "mouse_but_fast": {"duration": (3000, 6000), "mouse": 1, "tabs": 0, "label": 1},
        "hesitant_legit": {"duration": (60000, 120000), "mouse": 1, "tabs": 0, "label": 0},
        "hybrid_confusing": {"duration": (45000, 90000), "mouse": 1, "tabs": 1, "label": 1}
    }[case_type]

    session_id = f"sess_{case_type}_{uuid.uuid4()}"
    start = int((datetime.now() - timedelta(days=random.randint(1, 30))).timestamp() * 1000)
    duration = random.randint(*params["duration"])
    end = start + duration
    scroll_count = scroll_by_case(case_type)
    viewport_changes = viewport_by_case(case_type)
    mouse_clicks = mouse_clicks_by_case(case_type)
    enter_pressed = 1 if case_type == "no_mouse" else 0
    device = random.choice(["desktop", "mobile"])
    field_order = permute_order_for_case(case_type)

    conn.execute("""
    INSERT INTO sessions (
        session_id, start_time, end_time, mouseMoved, mouseClickCount, scrollCount,
        viewportChanges, tabCount, enterPressed, deviceType, fieldFocusOrder, label
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id, start, end, params["mouse"], mouse_clicks, scroll_count,
        viewport_changes, params["tabs"], enter_pressed, device, field_order, params["label"]
    ))

    paste_targets = set()
    hesitant_fields = set()

    if case_type == "hybrid_confusing":
        paste_targets = set(random.sample(FIELD_NAMES, 3))
        hesitant_fields = set(random.sample(FIELD_NAMES, 2))

    if case_type == "strategic_fraud":
        k = random.randint(3, 5)
        paste_targets = set(random.sample(FIELD_NAMES, k))

    if case_type == "paste_abuse":
        k = random.randint(3, 6)
        paste_targets = set(random.sample(FIELD_NAMES, k))

    for field in FIELD_NAMES:
        val = {
            "nom": fake_name(),
            "prenom": fake_first_name(),
            "cin": fake_cin(),
            "adresse": fake_city(),
            "profession": fake_profession(),
            "revenu": str(random.randint(1200, 5000)),
            "montant": str(random.randint(1000, 15000)),
            "duree": str(random.randint(6, 60))
        }[field]

        time_spent = field_time_by_case(case_type)
        deletes = deletes_by_case(case_type)
        paste = 0
        copy = 0
        changes = random.randint(1, 5)

        if case_type == "hybrid_confusing":
            if field in paste_targets:
                paste = random.randint(5, 8)
                copy = random.randint(0, 2)
            if field in hesitant_fields:
                time_spent = random.randint(3000, 6000)
                deletes = random.randint(3, 8)
                changes = random.randint(3, 6)

        if case_type == "strategic_fraud":
            if field in paste_targets:
                paste = random.randint(6, 10)
                copy = random.randint(0, 2)

        elif case_type == "copy_safe":
            # Collage modéré sur certains champs seulement
            if field in ["cin", "adresse", "profession"]:
                paste = random.randint(2, 4)
                copy = random.randint(1, 3)
            else:
                paste = 0
                copy = random.randint(0, 1)
            # Temps de saisie réaliste pour montrer prudence
            time_spent = random.randint(3000, 6000)
            deletes = random.randint(0, 2)
            changes = random.randint(1, 3)

        elif case_type == "mouse_but_fast":
            paste = random.randint(0, 1)
            copy = random.randint(0, 1)

        elif case_type == "hesitant_legit":
            paste = 0
            copy = 0

        elif case_type == "paste_abuse" and field in paste_targets:
            paste = random.randint(6, 10)
            copy = random.randint(0, 2)

        elif case_type == "no_mouse":
            paste = random.randint(3, 5) if random.random() < 0.4 else 0

        elif case_type == "normal":
            paste = random.randint(0, 1)
            if copy == 0 and random.random() < 0.05:
                copy = 1

        if case_type == "hesitant":
            changes = random.randint(3, 10)

        conn.execute("""
        INSERT INTO fields (
            session_id, field_name, value, timeSpentMs, hoverDurationMs, copy, paste, delete_count, changes, focusCount
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, field, val, time_spent, 0, copy, paste, deletes, changes, 1))

# ==== EXPORT FINAL POUR ENTRAÎNEMENT ====
def export_csv(conn):
    print("\n📦 Construction du dataset enrichi...")
    sessions_df = pd.read_sql_query("SELECT * FROM sessions", conn)
    fields_df = pd.read_sql_query("SELECT * FROM fields", conn)

    # Agrégations de base
    agg_fields = fields_df.groupby("session_id").agg(
        fieldCount=("field_name", "count"),
        totalTimeSpent=("timeSpentMs", "sum"),
        avgTimePerField=("timeSpentMs", "mean"),
        totalFocusCount=("focusCount", "sum"),
        avgChangesPerField=("changes", "mean"),
        avgPastePerField=("paste", "mean"),
        avgDeletePerField=("delete_count", "mean")
    ).reset_index()

    # 🔍 Ajout des nouvelles features comportementales
    std_time = fields_df.groupby("session_id")["timeSpentMs"].std().fillna(0)
    max_paste = fields_df.groupby("session_id")["paste"].max().fillna(0)
    paste_ratio = fields_df.groupby("session_id").apply(lambda g: (g["paste"] > 0).sum() / len(g)).fillna(0)
    delete_ratio = fields_df.groupby("session_id").apply(lambda g: (g["delete_count"] > 0).sum() / len(g)).fillna(0)

    # Fusion avec agg_fields
    agg_fields["stdTimePerField"] = agg_fields["session_id"].map(std_time)
    agg_fields["maxPasteCount"] = agg_fields["session_id"].map(max_paste)
    agg_fields["pasteRatio"] = agg_fields["session_id"].map(paste_ratio)
    agg_fields["deleteRatio"] = agg_fields["session_id"].map(delete_ratio)

    # Merge avec sessions
    df = sessions_df.merge(agg_fields, on="session_id")
    df["deviceType_encoded"] = df["deviceType"].map({"desktop": 0, "mobile": 1}).fillna(0).astype(int)

    def calc_deviation(order_str):
        ref_order = FIELD_NAMES
        try:
            actual_order = order_str.split(",")
            if len(actual_order) != len(ref_order):
                return len(ref_order)
            return sum(1 for i, j in zip(ref_order, actual_order) if i != j)
        except Exception:
            return len(FIELD_NAMES)

    df["fieldOrderDeviation"] = df["fieldFocusOrder"].apply(calc_deviation)
    df["label_target"] = df["label"]
    df["scrollDensity"] = df["scrollCount"] / (df["duration_ms"] / 1000 + 1e-5)

    final_features = [
        "duration_ms", "mouseClickCount", "scrollCount", "scrollDensity", "viewportChanges",
        "tabCount", "enterPressed", "deviceType_encoded", "fieldCount", "totalTimeSpent",
        "avgTimePerField", "totalFocusCount", "avgChangesPerField", "avgPastePerField",
        "avgDeletePerField", "fieldOrderDeviation", "stdTimePerField", "maxPasteCount",
        "pasteRatio", "deleteRatio", "label_target"
    ]

    df[final_features].to_csv("kyc_dataset_ready.csv", index=False)
    print("✅ Export CSV prêt pour entraînement : kyc_dataset_ready.csv")

# ==== MAIN ====
if __name__ == "__main__":
    print("\n=== Génération de données 100% tunisiennes ===")
    conn = init_db()
    for case, count in SAMPLES_PER_CASE.items():
        print(f"🔄 Génération du cas : {case} ({count} sessions)")
        for _ in range(count):
            generate_case(conn, case)
    conn.commit()
    export_csv(conn)
    conn.close()
