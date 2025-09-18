import os
import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .soil_model_loader import predict_soil
from .models import Prediction
from datetime import datetime
import pickle
import numpy as np

# Variable pour la dernière prédiction de SOL
last_soil_prediction = {}
# Fichier pour la dernière prédiction de CULTURE
CROP_PREDICTION_FILE = os.path.join(settings.BASE_DIR, "last_crop_prediction.json")

class SoilPredictAPI(APIView):
    def post(self, request, *args, **kwargs):
        image = request.FILES.get('image')
        if not image:
            return Response({"error": "Aucune image envoyée"}, status=400)

        img_path = os.path.join(settings.MEDIA_ROOT, image.name)
        with open(img_path, 'wb+') as f:
            for chunk in image.chunks():
                f.write(chunk)

        try:
            label, confidence = predict_soil(img_path)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        result = {
            "soil_type": label,
            "confidence": round(confidence , 2)
        }

        # Sauvegarde en mémoire
        global last_soil_prediction
        last_soil_prediction = result

        # Sauvegarde en base de données
        Prediction.objects.create(
            image_name=image.name,
            soil_type=label,
            confidence=result["confidence"]
        )

        # Sauvegarde dans un fichier JSON
        json_path = os.path.join(settings.BASE_DIR, "prediction_history.json")
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                history = json.load(f)
        else:
            history = []

        history.append({
            "timestamp": datetime.now().isoformat(),
            "image": image.name,
            "soil_type": label,
            "confidence": result["confidence"]
        })

        with open(json_path, "w") as f:
            json.dump(history, f, indent=2)

        return Response(result)

    def get(self, request, *args, **kwargs):
        if not last_soil_prediction:
            return Response({"message": "Aucune prédiction de sol disponible."}, status=404)
        return Response(last_soil_prediction)


class CropPredictAPI(APIView):
    def post(self, request, *args, **kwargs):
        # 1. Valider les données d'entrée
        required_fields = ['temperature', 'ph', 'humidity', 'nitrogen', 'potassium', 'phosphorus', 'rainfall']
        if not all(field in request.data for field in required_fields):
            return Response({"error": "Données d'entrée manquantes"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 2. Formater les données pour le modèle
            data = request.data
            input_data = np.array([[
                data['temperature'],
                data['ph'],
                data['humidity'],
                data['nitrogen'],
                data['potassium'],
                data['phosphorus'],
                data['rainfall']
            ]])
        except (TypeError, ValueError):
            return Response({"error": "Données d'entrée invalides"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Charger le modèle et prédire
        model_path = os.path.join(settings.BASE_DIR, 'model.pkl')
        try:
            with open(model_path, 'rb') as file:
                model = pickle.load(file)
            
            prediction = model.predict(input_data)
            predicted_crop = prediction[0]

            # 4. Retourner le résultat
            result = {
                "predicted_crop": predicted_crop
            }

            # Sauvegarde dans un fichier JSON
            with open(CROP_PREDICTION_FILE, "w") as f:
                json.dump(result, f)

            return Response(result, status=status.HTTP_200_OK)

        except FileNotFoundError:
            return Response({"error": "Modèle de prédiction introuvable"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"Erreur de prédiction : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):
        try:
            with open(CROP_PREDICTION_FILE, "r") as f:
                last_prediction = json.load(f)
            return Response(last_prediction)
        except FileNotFoundError:
            return Response({"message": "Aucune prédiction de culture disponible."}, status=404)

    
