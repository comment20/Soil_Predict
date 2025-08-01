import os
import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .soil_model_loader import predict_soil
from .models import Prediction
from datetime import datetime

last_prediction = {}

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

        # 1️⃣ Sauvegarde en mémoire
        global last_prediction
        last_prediction = result

        # 2️⃣ Sauvegarde en base de données
        Prediction.objects.create(
            image_name=image.name,
            soil_type=label,
            confidence=result["confidence"]
        )

        # 3️⃣ Sauvegarde dans un fichier JSON
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
        if not last_prediction:
            return Response({"message": "Aucune prédiction disponible."}, status=404)
        return Response(last_prediction)
