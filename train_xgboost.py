import pandas as pd
from xgboost import XGBClassifier, plot_importance
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import joblib

print("🚀 Démarrage du script d'entraînement XGBoost...")

# === Je charge le dataset ===
print("📥 Chargement du fichier CSV...")
df = pd.read_csv("kyc_dataset_ready.csv")

# === Je vérifie que toutes les colonnes requises sont présentes ===
print("🔍 Vérification des colonnes requises...")
required_cols = [
    "duration_ms", "mouseClickCount", "scrollCount", "scrollDensity",
    "viewportChanges", "tabCount", "enterPressed", "deviceType_encoded",
    "fieldCount", "totalTimeSpent", "avgTimePerField", "totalFocusCount",
    "avgChangesPerField", "avgPastePerField", "avgDeletePerField",
    "fieldOrderDeviation", "stdTimePerField", "maxPasteCount", "pasteRatio",
    "deleteRatio", "label_target"
]
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    print("❌ Colonnes manquantes :", missing_cols)
    raise ValueError(f"Colonnes manquantes dans le CSV : {missing_cols}")
else:
    print("✅ Toutes les colonnes sont présentes.")

# === Je sépare les features et le label ===
print("📊 Séparation des features et du label...")
X = df[required_cols[:-1]]
y = df["label_target"]

# === Je fais le split train/test ===
print("✂️ Découpage train/test...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === J'entraîne le modèle XGBoost ===
print("🧠 Entraînement du modèle XGBoost...")
clf = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric='mlogloss'
)
clf.fit(X_train, y_train)
print("✅ Modèle entraîné avec succès.")

# === Je prédis sur le test set ===
print("🔮 Prédiction sur le test set...")
y_pred = clf.predict(X_test)

# === J'évalue le modèle ===
print("📈 Évaluation du modèle sur test set")
cm = confusion_matrix(y_test, y_pred)
print(cm)
print(classification_report(y_test, y_pred))

# === Je trace la matrice de confusion ===
print("🧩 Affichage de la matrice de confusion...")
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Normal", "Fraude"])
disp.plot(cmap="Blues")
plt.show()

# === Validation croisée manuelle avec analyse détaillée ===
print("\n🔍 Validation croisée manuelle (5 folds) avec analyse détaillée...")
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for i, (train_idx, test_idx) in enumerate(skf.split(X, y)):
    print(f"\n📂 Fold {i+1}")
    X_train_fold, X_test_fold = X.iloc[train_idx], X.iloc[test_idx]
    y_train_fold, y_test_fold = y.iloc[train_idx], y.iloc[test_idx]

    clf_fold = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='mlogloss'
    )
    clf_fold.fit(X_train_fold, y_train_fold)
    y_pred_fold = clf_fold.predict(X_test_fold)

    # === J'affiche les métriques ===
    print("Matrice de confusion :")
    print(confusion_matrix(y_test_fold, y_pred_fold))
    print("\nRapport de classification :")
    print(classification_report(y_test_fold, y_pred_fold))

    # === Je regarde la répartition des profils dans le fold ===
    print("Répartition réelle des classes dans ce fold :", y_test_fold.value_counts())

    # === Je crée un tableau des sessions mal classées par profil ===
    errors = X_test_fold[y_test_fold != y_pred_fold]
    print(f"Nombre de sessions mal classées : {len(errors)}")
    if len(errors) > 0:
        print("Labels réels :", y_test_fold[y_test_fold != y_pred_fold].values)
        print("Prédictions :", y_pred_fold[y_test_fold != y_pred_fold])

    # === Je peux utiliser ces informations pour préparer ma fiche d'audit métier ===
    # Justifier la robustesse de mon modèle
    # Expliquer comment je détecte les fraudes stratégiques

# === Je trace l'importance des features ===
print("📊 Affichage de l'importance des features...")
plot_importance(clf)
plt.show()

# === Je sauvegarde le modèle ===
print("💾 Sauvegarde du modèle dans kyc_xgb_model.pkl...")
joblib.dump(clf, "kyc_xgb_model.pkl")
print("✅ Modèle sauvegardé avec succès.")

print("🏁 Script terminé.")
