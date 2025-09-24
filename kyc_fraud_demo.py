import streamlit as st
import pandas as pd
import joblib
from datetime import datetime
import os

# ==== CONFIGURATION ====
FEATURES = [
    "duration_ms", "mouseClickCount", "scrollCount", "scrollDensity",
    "viewportChanges", "tabCount", "enterPressed", "deviceType_encoded",
    "fieldCount", "totalTimeSpent", "avgTimePerField", "totalFocusCount",
    "avgChangesPerField", "avgPastePerField", "avgDeletePerField",
    "fieldOrderDeviation", "stdTimePerField", "maxPasteCount", "pasteRatio",
    "deleteRatio"
]
HISTORY_PATH = "prediction_history.csv"

# ==== CHARGEMENT DU MODÈLE ====
xgb_model = joblib.load("kyc_xgb_model.pkl")

# ==== PAGE ====
st.set_page_config(page_title="Détection KYC", page_icon="🔎")
st.title("🔎 Détection de fraude KYC (comportement)")
st.markdown("Remplis les données observées ou choisis un profil simulé. Le modèle XGBoost évaluera le risque.")

# ==== SIMULATION DE PROFIL ====
st.sidebar.header("🎭 Simulation de profil")
preset = st.sidebar.selectbox("Choisir un profil simulé", [
    "manuel", "hybrid_confusing", "copy_safe", "hesitant_legit"
])

# Slider de seuil
threshold = st.sidebar.slider("⚖️ Seuil de décision", 0.0, 1.0, 0.5, 0.01)

def get_preset_values(profile):
    if profile == "hybrid_confusing":
        return {
            "duration_ms": 60000,
            "mouseClickCount": 10,
            "scrollCount": 30,
            "viewportChanges": 1,
            "tabCount": 1,
            "enterPressed": "Oui",
            "deviceType": "desktop",
            "fieldCount": 8,
            "totalTimeSpent": 55000,
            "avgTimePerField": 6875,
            "totalFocusCount": 8,
            "avgChangesPerField": 3,
            "avgPastePerField": 2.5,
            "avgDeletePerField": 2.2,
            "fieldOrderDeviation": 4,
            "stdTimePerField": 1800,
            "maxPasteCount": 7,
            "pasteRatio": 0.375,
            "deleteRatio": 0.25
        }
    elif profile == "copy_safe":
        return {
            "duration_ms": 80000,
            "mouseClickCount": 15,
            "scrollCount": 40,
            "viewportChanges": 1,
            "tabCount": 0,
            "enterPressed": "Non",
            "deviceType": "desktop",
            "fieldCount": 8,
            "totalTimeSpent": 70000,
            "avgTimePerField": 8750,
            "totalFocusCount": 8,
            "avgChangesPerField": 2,
            "avgPastePerField": 1.5,
            "avgDeletePerField": 1,
            "fieldOrderDeviation": 0,
            "stdTimePerField": 1200,
            "maxPasteCount": 3,
            "pasteRatio": 0.25,
            "deleteRatio": 0.125
        }
    elif profile == "hesitant_legit":
        return {
            "duration_ms": 90000,
            "mouseClickCount": 20,
            "scrollCount": 60,
            "viewportChanges": 2,
            "tabCount": 0,
            "enterPressed": "Oui",
            "deviceType": "desktop",
            "fieldCount": 8,
            "totalTimeSpent": 85000,
            "avgTimePerField": 10625,
            "totalFocusCount": 10,
            "avgChangesPerField": 4,
            "avgPastePerField": 0.5,
            "avgDeletePerField": 3,
            "fieldOrderDeviation": 1,
            "stdTimePerField": 2200,
            "maxPasteCount": 2,
            "pasteRatio": 0.125,
            "deleteRatio": 0.375
        }
    else:
        return {}

preset_values = get_preset_values(preset)

# ==== FORMULAIRE ====
with st.form("kyc_form"):
    st.subheader("📝 Comportement utilisateur à évaluer")
    duration_ms = st.number_input("Durée totale de saisie (ms)", value=preset_values.get("duration_ms", 45000))
    mouseClickCount = st.number_input("Nombre de clics souris", value=preset_values.get("mouseClickCount", 10))
    scrollCount = st.number_input("Nombre de scrolls", value=preset_values.get("scrollCount", 30))
    viewportChanges = st.number_input("Changements de viewport", value=preset_values.get("viewportChanges", 1))
    tabCount = st.number_input("Changements d'onglet", value=preset_values.get("tabCount", 1))
    enterPressed = st.selectbox(
        "Touche Entrée pressée ?", ["Oui", "Non"],
        index=0 if preset_values.get("enterPressed", "Oui") == "Oui" else 1
    )
    deviceType = st.selectbox(
        "Type d'appareil", ["desktop", "mobile"],
        index=0 if preset_values.get("deviceType", "desktop") == "desktop" else 1
    )
    fieldCount = st.number_input("Nombre de champs remplis", value=preset_values.get("fieldCount", 8))
    totalTimeSpent = st.number_input("Temps total sur les champs (ms)", value=preset_values.get("totalTimeSpent", 60000))
    avgTimePerField = st.number_input("Temps moyen par champ (ms)", value=preset_values.get("avgTimePerField", 7500))
    totalFocusCount = st.number_input("Nombre total de focus", value=preset_values.get("totalFocusCount", 8))
    avgChangesPerField = st.number_input("Modifications moyennes par champ", value=preset_values.get("avgChangesPerField", 3))
    avgPastePerField = st.number_input("Collages moyens par champ", value=preset_values.get("avgPastePerField", 2))
    avgDeletePerField = st.number_input("Suppressions moyennes par champ", value=preset_values.get("avgDeletePerField", 2))
    fieldOrderDeviation = st.number_input("Ordre des champs modifié (écart)", value=preset_values.get("fieldOrderDeviation", 3))
    stdTimePerField = st.number_input("Écart-type du temps par champ", value=preset_values.get("stdTimePerField", 2000))
    maxPasteCount = st.number_input("Collage max sur un champ", value=preset_values.get("maxPasteCount", 6))
    pasteRatio = st.number_input("Ratio de champs collés", value=preset_values.get("pasteRatio", 0.4))
    deleteRatio = st.number_input("Ratio de champs supprimés", value=preset_values.get("deleteRatio", 0.3))
    submitted = st.form_submit_button("📤 Prédire")

# ==== UTILS ====
def badge_label(pred):
    return f":green[✅ Normal (0)]" if pred == 0 else f":red[⚠️ Suspect (1)]"

def save_prediction(data, pred, proba):
    row = data.copy()
    row.update({
        "prediction": pred,
        "confidence": round(proba, 4),
        "threshold": threshold,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profil": preset
    })
    if os.path.exists(HISTORY_PATH):
        df = pd.read_csv(HISTORY_PATH)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.to_csv(HISTORY_PATH, index=False)

# ==== PRÉDICTION ====
if submitted:
    input_data = {
        "duration_ms": duration_ms,
        "mouseClickCount": mouseClickCount,
        "scrollCount": scrollCount,
        "scrollDensity": scrollCount / (duration_ms / 1000 + 1e-5),
        "viewportChanges": viewportChanges,
        "tabCount": tabCount,
        "enterPressed": 1 if enterPressed == "Oui" else 0,
        "deviceType_encoded": 0 if deviceType == "desktop" else 1,
        "fieldCount": fieldCount,
        "totalTimeSpent": totalTimeSpent,
        "avgTimePerField": avgTimePerField,
        "totalFocusCount": totalFocusCount,
        "avgChangesPerField": avgChangesPerField,
        "avgPastePerField": avgPastePerField,
        "avgDeletePerField": avgDeletePerField,
        "fieldOrderDeviation": fieldOrderDeviation,
        "stdTimePerField": stdTimePerField,
        "maxPasteCount": maxPasteCount,
        "pasteRatio": pasteRatio,
        "deleteRatio": deleteRatio
    }
    X_input = pd.DataFrame([input_data])
    proba_xgb = xgb_model.predict_proba(X_input)[0][1]  # probabilité que ce soit suspect
    pred_xgb = int(proba_xgb > threshold)

    st.success("✅ Prédiction effectuée avec succès !")
    st.subheader("📊 Résultat de la prédiction XGBoost")
    st.write("Résultat :", badge_label(pred_xgb))
    st.write(f"📊 Score brut : {round(proba_xgb, 4)}")
    st.write(f"⚖️ Seuil appliqué : {threshold}")
    st.progress(int(proba_xgb * 100))

    # Sauvegarde
    save_prediction(input_data, pred_xgb, proba_xgb)

# ==== HISTORIQUE ====
st.markdown("---")
st.subheader("📁 Historique des prédictions")
if os.path.exists(HISTORY_PATH):
    df_log = pd.read_csv(HISTORY_PATH)
    st.dataframe(df_log.tail(10), use_container_width=True)
    st.download_button(
        "📥 Télécharger l'historique CSV",
        data=df_log.to_csv(index=False),
        file_name="historique_predictions.csv",
        mime="text/csv"
    )
    if st.button("🧹 Réinitialiser l'historique"):
        os.remove(HISTORY_PATH)
        st.success("Historique supprimé.")
        st.experimental_rerun()
else:
    st.info("Aucune prédiction enregistrée pour l’instant.")
