from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from database import create_tables, insert_session_data, insert_field_data
from feature_extractor import extract_features
import joblib
import sqlite3
import csv
import numpy as np
from datetime import datetime
import os
import requests
import json

# Initialisation
app = Flask(__name__)
CORS(app)

if os.path.exists("tracking.db"):
    os.remove("tracking.db")

create_tables()
model = joblib.load("kyc_xgb_model.pkl")

# Ordre des features attendu par le modèle
FEATURE_ORDER = [
    "duration_ms",
    "mouseClickCount",
    "scrollCount",
    "scrollDensity",
    "viewportChanges",
    "tabCount",
    "enterPressed",
    "deviceType_encoded",
    "fieldCount",
    "totalTimeSpent",
    "avgTimePerField",
    "totalFocusCount",
    "avgChangesPerField",
    "avgPastePerField",
    "avgDeletePerField",
    "fieldOrderDeviation",
    "stdTimePerField",
    "maxPasteCount",
    "pasteRatio",
    "deleteRatio"
]

# Enregistrement des données
@app.route('/api/save', methods=['POST'])
def save_data():
    try:
        data = request.get_json(force=True)
        print("📥 Données reçues :", data)

        if not data:
            print("⚠️ Aucune donnée reçue")
            return jsonify({"error": "Aucune donnée reçue"}), 400

        required_fields = ["session_id", "start_time", "end_time", "submit_delay_ms", "field_order", "fields"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            print("⚠️ Champs manquants :", missing)
            return jsonify({"error": f"Champs manquants : {', '.join(missing)}"}), 400

        duration_ms = data.get("end_time", 0) - data.get("start_time", 0)
        data["duration_ms"] = duration_ms  # 👈 Ajout obligatoire

        session_data = {
            "session_id": data.get("session_id", "unknown"),
            "start_time": data.get("start_time", 0),
            "end_time": data.get("end_time", 0),
            "submit_delay_ms": data.get("submit_delay_ms", 0),
            "fast_fill": int(bool(data.get("fast_fill", False))),
            "mouseMoved": int(bool(data.get("mouseMoved", False))),
            "mouseClickCount": data.get("mouseClickCount", 0),
            "scrollCount": data.get("scrollCount", 0),
            "viewportChanges": data.get("viewportChanges", 0),
            "tabKeyCount": data.get("tabKeyCount", 0),
            "enterPressed": int(bool(data.get("enterPressed", False))),
            "deviceType": data.get("deviceType", "unknown"),
            "fieldFocusOrder": ",".join(data.get("field_order", []))
        }

        print("🔍 Clés dans data avant insert:", list(data.keys()))
        print("🔍 duration_ms dans data:", data.get("duration_ms", "❌ absent"))

        insert_session_data(session_data)
        print("✅ Session enregistrée :", session_data["session_id"])

        fields = data.get("fields", {})
        if not isinstance(fields, dict):
            print("⚠️ Format invalide pour 'fields'")
            return jsonify({"error": "Format invalide pour 'fields'"}), 400

        for field_name, infos in fields.items():
            insert_field_data({
                "session_id": session_data["session_id"],
                "field_name": field_name,
                "value": infos.get("value", ""),
                "timeSpentMs": infos.get("timeSpentMs", 0),
                "hoverDurationMs": infos.get("hoverDurationMs", 0),
                "copy": infos.get("copy", 0),
                "paste": infos.get("paste", 0),
                "delete_count": infos.get("delete", 0),
                "changes": infos.get("changes", 0),
                "focusCount": infos.get("focusCount", 0)
            })

        print("✅ Champs enregistrés pour session :", session_data["session_id"])
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("❌ Erreur dans /api/save :", str(e))
        return jsonify({"error": f"Erreur interne du serveur : {str(e)}"}), 500


# Prédiction avec log CSV
@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json(force=True)
        print("📤 Données reçues pour prédiction :", data)

        if not data:
            return jsonify({"error": "Données manquantes"}), 400

        session_id = data.get("session_id", "unknown")
        features = extract_features(data)
        print("📊 Features extraites :", features)

        # Construction du vecteur dans l’ordre attendu
        try:
            features_array = np.array([[features[f] for f in FEATURE_ORDER]])
        except KeyError as e:
            print("❌ Feature manquante :", str(e))
            return jsonify({"error": f"Feature manquante : {str(e)}"}), 400

        print("📐 Shape du vecteur :", features_array.shape)
        print("✅ Vecteur final :", features_array)

        expected_features = model.n_features_in_
        actual_features = features_array.shape[1]
        if actual_features != expected_features:
            raise ValueError(f"Feature shape mismatch, expected: {expected_features}, got: {actual_features}")

        prediction = model.predict(features_array)[0]
        probability = model.predict_proba(features_array)[0].tolist()
        score = round(probability[1], 4)
        label = "Suspicious" if prediction == 1 else "Clean"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"🔍 Session: {session_id} | Score: {score} | Label: {label} | Timestamp: {timestamp}")

        # Log dans le fichier CSV
        with open("prediction_log.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["timestamp", "session_id", "label", "score"])
            writer.writerow([timestamp, session_id, label, score])

        # Envoi webhook si suspicion
        if label == "Suspicious":
            # ➜ VRAIES valeurs depuis le formulaire (data["fields"])
            form_fields = data.get("fields", {})
            payload = {
                "session_id": session_id,
                "client": f'{form_fields.get("nom", {}).get("value", "")} {form_fields.get("prenom", {}).get("value", "")}'.strip(),
                "montant": form_fields.get("montant", {}).get("value", ""),
                "revenu": form_fields.get("revenu", {}).get("value", ""),
                "cin": form_fields.get("cin", {}).get("value", ""),
                "adresse": form_fields.get("adresse", {}).get("value", ""),
                "profession": form_fields.get("profession", {}).get("value", ""),
                "duree": form_fields.get("duree", {}).get("value", ""),
                # techniques/pratiques
                "ip": request.remote_addr,
                "score": float(score),
                "label": label,
                "timestamp": timestamp,
                "lien_dossier": f"https://ton-system.local/sessions/{session_id}"
            }

            # Debug clair
            print("\n📤 Payload envoyé à n8n :")
            print(json.dumps(payload, indent=2, ensure_ascii=False))

            try:
                # ⚠️ Mets l’URL ngrok du moment ici
                n8n_url = "https://b6a10d83a527.ngrok-free.app/webhook/fraud_alert"
                response = requests.post(n8n_url, json=payload, timeout=5)
                print("📤 Alerte envoyée à n8n :", response.status_code, response.text)
            except Exception as e:
                print("⚠️ Erreur envoi n8n :", e)

        return jsonify({
            "message": "Votre session a été transmise pour vérification.",
            "score": score,
            "label": label
        }), 200

    except Exception as e:
        print("❌ Erreur dans /api/predict :", str(e))
        return jsonify({"error": "Erreur interne du serveur"}), 500


# Export CSV - Sessions
@app.route('/export/sessions')
def export_sessions_csv():
    try:
        conn = sqlite3.connect("tracking.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM sessions")
        rows = cur.fetchall()
        headers = [d[0] for d in cur.description]
        conn.close()

        with open("export_sessions.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        return jsonify({"status": "sessions exported"}), 200
    except Exception as e:
        print("❌ Erreur export sessions :", str(e))
        return jsonify({"error": "Erreur export sessions"}), 500


# Export CSV - Fields
@app.route('/export/fields')
def export_fields_csv():
    try:
        conn = sqlite3.connect("tracking.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM fields")
        rows = cur.fetchall()
        headers = [d[0] for d in cur.description]
        conn.close()

        with open("export_fields.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        return jsonify({"status": "fields exported"}), 200
    except Exception as e:
        print("❌ Erreur export fields :", str(e))
        return jsonify({"error": "Erreur export fields"}), 500


# Page principale
@app.route("/")
def index():
    return render_template("formulaire.html")


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
