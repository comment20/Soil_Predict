import pandas as pd
import pickle
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# 1. Load Data
print("--- Chargement des données depuis Crop_recommendation.csv ---")
try:
    df = pd.read_csv('SoilClassifier/Crop_recommendation.csv')
except FileNotFoundError:
    print("--- ERREUR: Fichier Crop_recommendation.csv introuvable. Assurez-vous qu'il est dans le dossier SoilClassifier. ---")
    exit()

# 2. Séparer les features (X) et la cible (y)
print("--- Séparation des features et de la cible ---")
X = df[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
y = df['label']

# 3. Diviser les données en ensembles d'entraînement et de test
print("--- Division des données (train/test split) ---")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 4. Définir le Pipeline
print("--- Définition du Pipeline (StandardScaler + RandomForest) ---")
# Ce pipeline va d'abord standardiser les données, puis entraîner le classifieur
model_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
])

# 5. Entraîner le Pipeline
print("--- Entraînement du modèle... ---")
model_pipeline.fit(X_train, y_train)
print("--- Entraînement terminé. ---")

# Évaluation (optionnelle, mais bonne pratique)
accuracy = model_pipeline.score(X_test, y_test)
print(f"--- Précision du modèle sur l'ensemble de test : {accuracy:.2f} ---")

# 6. Sauvegarder le Pipeline entraîné
output_path = 'SoilClassifier/model.pkl'
print(f"--- Sauvegarde du modèle entraîné dans {output_path} ---")
with open(output_path, "wb") as file:
    pickle.dump(model_pipeline, file)

print("--- Le nouveau modèle a été créé et sauvegardé avec succès ! ---")
