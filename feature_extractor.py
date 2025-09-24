import numpy as np
from sklearn.preprocessing import LabelEncoder

# Encoder statique pour deviceType
device_encoder = LabelEncoder()
device_encoder.fit(["desktop", "mobile", "tablet", "unknown"])

def compute_field_order_deviation(expected_order, field_data):
    # Filtrer les champs effectivement visités
    actual_order = [field for field in expected_order if field_data.get(field, {}).get("focusCount", 0) > 0]
    deviation = sum(1 for i, field in enumerate(expected_order[:len(actual_order)]) if actual_order[i] != field)
    return deviation

def extract_features(data):
    fields = data.get("fields", {})
    field_order = data.get("field_order", [])
    duration_ms = data.get("duration_ms", 0)
    device_type = data.get("deviceType", "unknown")

    # Initialisations
    fieldCount = len(fields)
    totalTimeSpent = sum(f.get("timeSpentMs", 0) for f in fields.values())
    avgTimePerField = totalTimeSpent / fieldCount if fieldCount else 0
    totalFocusCount = sum(f.get("focusCount", 0) for f in fields.values())
    avgChangesPerField = np.mean([f.get("changes", 0) for f in fields.values()]) if fields else 0
    avgPastePerField = np.mean([f.get("paste", 0) for f in fields.values()]) if fields else 0
    avgDeletePerField = np.mean([f.get("delete", 0) for f in fields.values()]) if fields else 0

    # Variabilité du temps par champ
    stdTimePerField = np.std([f.get("timeSpentMs", 0) for f in fields.values()]) if fields else 0

    # Collage maximal sur un champ
    maxPasteCount = max([f.get("paste", 0) for f in fields.values()]) if fields else 0

    # Ratio de champs collés
    pasteRatio = sum(1 for f in fields.values() if f.get("paste", 0) > 0) / fieldCount if fieldCount else 0

    # Ratio de champs modifiés (delete)
    deleteRatio = sum(1 for f in fields.values() if f.get("delete", 0) > 0) / fieldCount if fieldCount else 0

    # ✅ Correction de fieldOrderDeviation
    fieldOrderDeviation = compute_field_order_deviation(field_order, fields)

    # 📜 Ajout de scrollDensity
    scrollCount = data.get("scrollCount", 0)
    scrollDensity = scrollCount / (duration_ms / 1000) if duration_ms > 0 else 0

    # Encodage du device
    try:
        deviceType_encoded = int(device_encoder.transform([device_type])[0])
    except Exception:
        deviceType_encoded = int(device_encoder.transform(["unknown"])[0])

    # Autres features transmis directement
    mouseClickCount = data.get("mouseClickCount", 0)
    viewportChanges = data.get("viewportChanges", 0)
    tabCount = data.get("tabKeyCount", 0)
    enterPressed = int(bool(data.get("enterPressed", False)))

    return {
        "duration_ms": duration_ms,
        "mouseClickCount": mouseClickCount,
        "scrollCount": scrollCount,
        "scrollDensity": scrollDensity,
        "viewportChanges": viewportChanges,
        "tabCount": tabCount,
        "enterPressed": enterPressed,
        "deviceType_encoded": deviceType_encoded,
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
