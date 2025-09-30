# 🧠 Détection comportementale de fraude KYC

Ce projet détecte les comportements suspects lors de la soumission de formulaires KYC (Know Your Customer) en analysant des signaux comportementaux subtils. Il ne se contente pas de ce que l’utilisateur saisit — il s’intéresse à **comment** il le fait.

## 🎯 Objectif

- Capturer des signaux cognitifs et comportementaux pendant la saisie d’un formulaire  
- Simuler des profils réalistes (fraudeurs, hésitants, automatisés…)  
- Extraire des features interprétables  
- Entraîner un modèle XGBoost robuste  
- Déclencher des alertes en temps réel  

## 🧠 Signaux comportementaux capturés

- ⏱️ Temps de focus par champ  
- 🧭 Ordre de navigation  
- 🖱️ Mouvements de souris, clics, scrolls  
- ⌨️ Touches pressées (Tab, Enter, Delete)  
- 📋 Copier/coller  
- 🧠 Vitesse de remplissage et délai avant soumission  

## 🛠️ Architecture technique

| Composant              | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| `formulaire.html`      | Formulaire KYC avec champs classiques et upload de justificatifs           |
| `tracking.js`          | Script de capture comportementale en temps réel                            |
| `app.py`               | Backend Flask avec endpoints `/api/save` et `/api/predict`                 |
| `feature_extractor.py` | Extraction de features interprétables à partir des signaux bruts           |
| `database.py`          | Base SQLite avec tables `sessions`, `fields`, `clicks`, `mouse_movements` |
| `generate_cases.py`    | Générateur de profils cognitifs simulés (10 types de comportements)         |
| `build_training_dataset.py` | Fusion des features extraites avec les labels métier pour créer le dataset d'entraînement |
| `train_xgboost.py`     | Entraînement du modèle XGBoost + validation croisée + interprétabilité     |
| `kyc_fraud_demo.py`    | Interface Streamlit pour tester le modèle et visualiser les prédictions    |

## 🧪 Profils simulés

| Cas simulé             | Interprétation cognitive                  |
|------------------------|-------------------------------------------|
| `fast`                 | Automatisation suspecte                   |
| `hesitant`             | Confusion ou prudence                     |
| `paste_abuse`          | Injection frauduleuse                     |
| `no_mouse`             | Script ou automatisation clavier          |
| `strategic_fraud`      | Simulation de légitimité                  |
| `copy_safe`            | Copier/coller légitime                    |
| `hesitant_legit`       | Prudence authentique                      |
| `mouse_but_fast`       | Vitesse suspecte malgré souris            |
| `hybrid_confusing`     | Brouillage volontaire                     |

## 📊 Features extraites

| Feature               | Interprétation cognitive                  |
|----------------------|-------------------------------------------|
| `scrollDensity`      | Engagement visuel                         |
| `pasteRatio`         | Automatisation ou injection               |
| `fieldOrderDeviation`| Stratégie ou confusion                    |
| `stdTimePerField`    | Hésitation ou prudence                    |
| `maxPasteCount`      | Intensité d’automatisation                |
| `deleteRatio`        | Révision ou doute                         |

## 🚀 Lancement du projet

```bash
# 1. Générer des données simulées
python generate_cases.py

# 2. Construire le dataset d'entraînement
python build_training_dataset.py

# 3. Entraîner le modèle
python train_xgboost.py

# 4. Lancer le serveur Flask
python app.py

# 5. Accéder au formulaire
http://localhost:5000

# 6. Lancer la démo Streamlit
streamlit run kyc_fraud_demo.py
```

## 📁 Historique et audit

- Toutes les prédictions sont loggées dans `prediction_log.csv`  
- L’interface Streamlit permet de visualiser et exporter l’historique  
- Les sessions et champs sont exportables en CSV pour audit métier  
- Les erreurs de classification sont analysées par profil simulé  
- La base SQLite permet une traçabilité complète des interactions  

## 📣 Communication publique

Ce projet est conçu pour être partagé :  
- **GitHub** : README clair, structuré, défendable  
- **LinkedIn** : discussion sur la modélisation cognitive en KYC/fraude  
- **Streamlit** : démonstration interactive pour décideurs et analystes  

## 🧪 Démo interactive avec Streamlit

Le fichier `kyc_fraud_demo.py` permet de tester le modèle en direct via une interface Streamlit :

### 🎭 Simulation de profils cognitifs

- `hybrid_confusing` → brouillage volontaire  
- `copy_safe` → copier/coller légitime  
- `hesitant_legit` → prudence authentique  
- `manuel` → saisie libre  

### 📊 Visualisation des résultats

- Score brut de suspicion  
- Seuil ajustable  
- Badge explicite (`✅ Normal` ou `⚠️ Suspect`)  
- Barre de progression  
- Historique des prédictions exportable  

## 🧠 Entraînement du modèle XGBoost

Le modèle est entraîné sur des features comportementales extraites via `feature_extractor.py`, simulées avec `generate_cases.py`, et consolidées dans `kyc_dataset_ready.csv`.

### ⚙️ Paramètres du modèle

```python
XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric='mlogloss'
)
```

### 📈 Évaluation

- Split train/test (80/20)  
- Validation croisée (5 folds)  
- Matrices de confusion  
- Rapport de classification  
- Analyse des erreurs par profil simulé  

### 📊 Interprétabilité

Le script affiche l’importance des features pour comprendre les signaux les plus discriminants.

### 💾 Sauvegarde

Le modèle est exporté dans `kyc_xgb_model.pkl` pour une utilisation en production via `/api/predict`.

## 🗃️ Structure de la base de données

| Table              | Description                                      |
|--------------------|--------------------------------------------------|
| `sessions`         | Métadonnées globales de la session               |
| `fields`           | Détails par champ (temps, copier/coller, etc.)   |
| `clicks`           | Coordonnées et éléments cliqués                  |
| `mouse_movements`  | Trajectoire de la souris (timestamp, x, y)       |

Cette structure permet d’enrichir le modèle avec des signaux spatiaux, temporels et cognitifs — et d’auditer chaque session avec précision.

## 💡 Pour aller plus loin

- Ajouter des visualisations (heatmaps, timelines, clusters de profils)  
- Intégrer des modèles explicables (SHAP, LIME)  
- Étendre à d’autres formulaires (inscription, paiement, support)
