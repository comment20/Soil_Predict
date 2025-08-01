import requests
from django.shortcuts import render, redirect
from .forms import SoilImageForm
from django.conf import settings
import os

API_URL = "http://127.0.0.1:8000/api/predict/"

def home(request):
    if request.method == "POST":
        form = SoilImageForm(request.POST, request.FILES)
        if form.is_valid():
            img_file = request.FILES["image"]

            # ✅ ENVOI DIRECT À L'API (pas de sauvegarde locale)
            response = requests.post(API_URL, files={"image": img_file})

            if response.status_code == 200:
                data = response.json()
                soil_type = data["soil_type"]
                confidence = data["confidence"]
            else:
                soil_type = "Erreur API"
                confidence = 0

            # ✅ Pour afficher l’image dans result.html
            # On la sauve quand même dans /media/ pour l’affichage
            img_path = os.path.join(settings.MEDIA_ROOT, img_file.name)
            with open(img_path, "wb+") as f:
                for chunk in img_file.chunks():
                    f.write(chunk)
            img_url = settings.MEDIA_URL + img_file.name

            # ✅ Stocker dans la session pour la page /result/
            request.session["soil_type"] = soil_type
            request.session["confidence"] = confidence
            request.session["uploaded_image"] = img_url

            return redirect("result")
    else:
        form = SoilImageForm()

    return render(request, "home.html", {"form": form})


def result(request):
    # Récupérer ce qu'on a mis dans la session
    soil_type = request.session.get("soil_type")
    confidence = request.session.get("confidence")
    uploaded_image = request.session.get("uploaded_image")

    # Si on accède directement sans prédiction, renvoyer à home
    if not soil_type:
        return redirect("home")

    return render(request, "result.html", {
        "soil_type": soil_type,
        "confidence": confidence,
        "uploaded_image": uploaded_image
    })
