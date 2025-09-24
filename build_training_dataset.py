import pandas as pd
import sqlite3
from sklearn.preprocessing import LabelEncoder

# 1. Charger les features depuis le CSV
df_features = pd.read_csv("kyc_dataset_tn.csv")

# 2. Connexion à la base de données SQLite
conn = sqlite3.connect("tracking.db")

# 3. Lire les labels depuis la table sessions
df_labels = pd.read_sql_query("SELECT session_id, label AS label_target FROM sessions", conn)
conn.close()

# 4. Fusionner sur session_id
df = df_features.merge(df_labels, on="session_id", how="left")

# 5. Supprimer les lignes sans label
df = df.dropna(subset=["label_target"])

# 6. Encoder deviceType
le_device = LabelEncoder()
df["deviceType_encoded"] = le_device.fit_transform(df["deviceType"])

# 7. Supprimer les colonnes inutiles (optionnel)
df = df.drop(columns=["fieldFocusOrder", "created_at"], errors="ignore")

# 8. Exporter
df.to_csv("kyc_dataset_ready.csv", index=False)
print("✅ Fichier exporté : kyc_dataset_ready.csv")
