import requests
import csv
from datetime import datetime
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomAuthenticationForm, SoilImageForm, SoilCharacteristicsForm, SignUpForm
from django.conf import settings
import os
import json
from collections import Counter
from .models import Prediction, CropPrediction
import numpy as np
import pickle

from .soil_model_loader import predict_soil
from .soil_model_loader import predict_soil

API_URL = "http://127.0.0.1:8000/api/predict/"

@login_required
def home(request):
    return render(request, "home.html")

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = CustomAuthenticationForm()
    
    form.fields['username'].widget.attrs.update({'placeholder': 'Nom d\'utilisateur'})
    form.fields['password'].widget.attrs.update({'placeholder': 'Mot de passe'})

    return render(request, 'connexion.html', {'login_form': form})

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'connexion.html', {'signup_form': form})

def logout_view(request):
    logout(request)
    return redirect('connexion')

@login_required
def result(request):
    soil_type = request.session.get("soil_type")
    confidence = request.session.get("confidence")
    uploaded_image = request.session.get("uploaded_image")
    if not soil_type:
        return redirect("home")
    context = {
        'predicted_class': soil_type,
        'probability_percentage': confidence,
        'image_url': uploaded_image
    }
    return render(request, "result.html", context)

@user_passes_test(lambda u: u.is_staff)
def prediction_history(request):
    history = Prediction.objects.all()
    return render(request, 'historique.html', {'history': history})

@login_required
def my_history(request):
    history = Prediction.objects.filter(user=request.user)
    return render(request, 'historique.html', {'history': history})

@login_required
def export_history_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="prediction_history.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date et Heure', 'Nom de l\'image', 'Type de sol prédit', 'Confiance', 'Latitude', 'Longitude', 'Nom de la Localisation'])

    predictions = Prediction.objects.filter(user=request.user).order_by('timestamp')
    for prediction in predictions:
        writer.writerow([
            prediction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            prediction.image_name,
            prediction.soil_type,
            f'{prediction.confidence:.2f}%',
            prediction.latitude if prediction.latitude is not None else '',
            prediction.longitude if prediction.longitude is not None else '',
            prediction.location_name if prediction.location_name is not None else ''
        ])
    return response

@login_required
def export_history_pdf(request):
    predictions = Prediction.objects.filter(user=request.user).order_by('timestamp')
    
    context = {
        'predictions': predictions,
    }
    
    template_path = 'history_pdf_template.html'
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="prediction_history.pdf"'
    
    pisa_status = pisa.CreatePDF(
        html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


@user_passes_test(lambda u: u.is_staff)
def dashboard(request):
    # Données pour les types de sol
    soil_history_data = Prediction.objects.all()
    soil_types = [item.soil_type for item in soil_history_data]
    soil_type_counts = Counter(soil_types)

    # Données pour les types de culture
    crop_history_data = CropPrediction.objects.all()
    crop_types = [item.predicted_crop for item in crop_history_data]
    crop_type_counts = Counter(crop_types)

    context = {
        'soil_type_labels': list(soil_type_counts.keys()),
        'soil_type_data': list(soil_type_counts.values()),
        'crop_type_labels': list(crop_type_counts.keys()),
        'crop_type_data': list(crop_type_counts.values()),
    }
    return render(request, 'dashboard.html', context)

@user_passes_test(lambda u: u.is_staff)
def dashboard_data(request):
    history_data = Prediction.objects.all()
    soil_types = [item.soil_type for item in history_data]
    soil_type_counts = Counter(soil_types)

    data = {
        'labels': list(soil_type_counts.keys()),
        'data': list(soil_type_counts.values()),
    }
    return JsonResponse(data)

@user_passes_test(lambda u: u.is_staff)
def crop_dashboard_data(request):
    history_data = CropPrediction.objects.all()
    crop_types = [item.predicted_crop for item in history_data]
    crop_type_counts = Counter(crop_types)

    data = {
        'labels': list(crop_type_counts.keys()),
        'data': list(crop_type_counts.values()),
    }
    return JsonResponse(data)

@login_required
def upload_image_view(request):
    if request.method == "POST":
        form = SoilImageForm(request.POST, request.FILES)
        if form.is_valid():
            img_file = request.FILES["image"]
            
            img_path = os.path.join(settings.MEDIA_ROOT, img_file.name)
            with open(img_path, "wb+") as f:
                for chunk in img_file.chunks():
                    f.write(chunk)
            
            try:
                soil_type, confidence = predict_soil(img_path)

                # Gérer le cas où l'image n'est pas un sol
                if soil_type == 'image non sol':
                    form = SoilImageForm()
                    error_message = "L'image fournie ne semble pas être une image de sol. Veuillez essayer avec une autre image."
                    return render(request, "upload_image.html", {"form": form, "error_message": error_message})

                # Si c'est un sol, sauvegarder la prédiction
                Prediction.objects.create(
                    user=request.user,
                    image_name=img_file.name,
                    soil_type=soil_type,
                    confidence=confidence
                )
                
                # Préparer la page de résultat
                img_url = settings.MEDIA_URL + img_file.name
                request.session["soil_type"] = soil_type
                request.session["confidence"] = confidence
                request.session["uploaded_image"] = img_url
                return redirect("result")

            except Exception as e:
                print(f"Erreur lors de la prédiction locale du sol: {e}")
                form = SoilImageForm()
                error_message = "Une erreur est survenue lors de l'analyse de l'image."
                return render(request, "upload_image.html", {"form": form, "error_message": error_message})
    else:
        form = SoilImageForm()
    return render(request, "upload_image.html", {"form": form})

@login_required
def delete_prediction(request, prediction_id):
    prediction = get_object_or_404(Prediction, id=prediction_id)
    # Allow staff to delete any prediction, otherwise check ownership
    if not request.user.is_staff and prediction.user != request.user:
        return HttpResponseForbidden("You are not allowed to delete this prediction.")
    if request.method == 'POST':
        prediction.delete()
        # Redirect to the appropriate history page based on user type
        if request.user.is_staff:
            return redirect('historique') # Redirect to admin history page
        else:
            return redirect('my_history') # Redirect to user's history page
    # If it's a GET request, just redirect to the appropriate history page
    if request.user.is_staff:
        return redirect('historique')
    else:
        return redirect('my_history')

def landing_page_view(request):
    return render(request, "landing.html")

@login_required
def analyze_characteristics_view(request):
    if request.method == 'POST':
        form = SoilCharacteristicsForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # Créer le payload JSON pour l'API
            api_payload = {
                'temperature': data['temperature'],
                'ph': data['ph'],
                'humidity': data['humidity'],
                'nitrogen': data['nitrogen'],
                'potassium': data['potassium'],
                'phosphorus': data['phosphorus'],
                'rainfall': data['rainfall']
            }

            # Appeler l'API de prédiction de culture
            try:
                response = requests.post("http://127.0.0.1:8000/api/crop-predict/", json=api_payload)
                response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP (4xx ou 5xx)
                
                result_data = response.json()
                predicted_crop = result_data.get('predicted_crop', 'Erreur')

                # Sauvegarder la prédiction de culture dans la base de données
                CropPrediction.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    temperature=data['temperature'],
                    ph=data['ph'],
                    humidity=data['humidity'],
                    nitrogen=data['nitrogen'],
                    potassium=data['potassium'],
                    phosphorus=data['phosphorus'],
                    rainfall=data['rainfall'],
                    predicted_crop=predicted_crop
                )

                # Stocker le résultat dans la session et rediriger
                request.session['predicted_crop'] = predicted_crop
                return redirect('crop_result')

            except requests.exceptions.RequestException as e:
                # Gérer les erreurs réseau ou HTTP
                print(f"--- Erreur lors de l'appel à l'API de culture : {e} ---")
                # On pourrait rediriger vers une page d'erreur ou ré-afficher le formulaire avec un message
                pass

    else:
        form = SoilCharacteristicsForm()

    return render(request, 'analyze_characteristics.html', {'form': form})

@login_required
def crop_result_view(request):
    predicted_crop_en = request.session.get('predicted_crop', 'N/A')

    translation_dict = {
        'apple': 'Pomme', 'banana': 'Banane', 'blackgram': 'Haricot Urd', 'chickpea': 'Pois Chiche',
        'coconut': 'Noix de Coco', 'coffee': 'Café', 'cotton': 'Coton', 'grapes': 'Raisin',
        'jute': 'Jute', 'kidneybeans': 'Haricot Rouge', 'lentil': 'Lentille', 'maize': 'Maïs',
        'mango': 'Mangue', 'mothbeans': 'Haricot Mat', 'mungbean': 'Haricot Mungo',
        'muskmelon': 'Melon Cantaloup', 'orange': 'Orange', 'papaya': 'Papaye',
        'pigeonpeas': 'Pois d\'Angole', 'pomegranate': 'Grenade', 'rice': 'Riz',
        'watermelon': 'Pastèque'
    }

    # Traduire le nom de la culture, avec une valeur par défaut si non trouvé
    predicted_crop_fr = translation_dict.get(predicted_crop_en, predicted_crop_en)

    context = {
        'predicted_crop': predicted_crop_fr
    }
    return render(request, 'crop_result.html', context)