import sqlite3

DB_FILE = "tracking.db"

def create_tables():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Table sessions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        start_time INTEGER,
        end_time INTEGER,
        submit_delay_ms INTEGER,
        fast_fill INTEGER,
        mouseMoved INTEGER,
        mouseClickCount INTEGER,
        scrollCount INTEGER,
        scrollDensity REAL,
        viewportChanges INTEGER,
        tabKeyCount INTEGER,
        enterPressed INTEGER,
        deviceType TEXT,
        fieldFocusOrder TEXT
    )
    """)

    # Table fields
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fields (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        field_name TEXT,
        value TEXT,
        timeSpentMs INTEGER,
        hoverDurationMs INTEGER,
        copy INTEGER,
        paste INTEGER,
        delete_count INTEGER,
        changes INTEGER,
        focusCount INTEGER,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Tables créées avec succès.")

def insert_session_data(session_data):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO sessions (
        session_id, start_time, end_time, submit_delay_ms, fast_fill,
        mouseMoved, mouseClickCount, scrollCount, viewportChanges,
        tabKeyCount, enterPressed, deviceType, fieldFocusOrder
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_data.get("session_id"),
        session_data.get("start_time"),
        session_data.get("end_time"),
        session_data.get("submit_delay_ms"),
        session_data.get("fast_fill"),
        session_data.get("mouseMoved"),
        session_data.get("mouseClickCount"),
        session_data.get("scrollCount"),
        session_data.get("viewportChanges"),
        session_data.get("tabKeyCount"),
        session_data.get("enterPressed"),
        session_data.get("deviceType"),
        session_data.get("fieldFocusOrder")
    ))

    conn.commit()
    conn.close()
    print(f"✅ Session {session_data.get('session_id')} insérée.")

def insert_field_data(field_data):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO fields (
        session_id, field_name, value, timeSpentMs, hoverDurationMs,
        copy, paste, delete_count, changes, focusCount
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        field_data.get("session_id"),
        field_data.get("field_name"),
        field_data.get("value"),
        field_data.get("timeSpentMs"),
        field_data.get("hoverDurationMs"),
        field_data.get("copy"),
        field_data.get("paste"),
        field_data.get("delete_count"),
        field_data.get("changes"),
        field_data.get("focusCount")
    ))

    conn.commit()
    conn.close()
    print(f"✅ Champ {field_data.get('field_name')} inséré pour la session {field_data.get('session_id')}.")
