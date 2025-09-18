from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from Classifier.models import Prediction, CropPrediction
from .models import ChatMessage
import json

# This is a placeholder for the LLM interaction.
# In a real scenario, this would call an external LLM API (e.g., Gemini API).
# For this exercise, I will simulate the LLM's response based on the prompt.

import re

def get_llm_response(prompt, last_bot_message=None):
    # Extract user message and context from the prompt
    user_message_match = re.search(r'Voici le message de l\'utilisateur: "(.*?)"', prompt)
    user_message = user_message_match.group(1) if user_message_match else ""

    soil_prediction_match = re.search(r'Votre dernière prédiction de sol: (.*?) \(Confiance: (.*?)\\%\)', prompt)
    latest_soil_type = soil_prediction_match.group(1) if soil_prediction_match else None
    latest_soil_confidence = soil_prediction_match.group(2) if soil_prediction_match else None

    crop_prediction_match = re.search(r'Votre dernière prédiction de culture: (.*?)\.', prompt)
    latest_crop_type = crop_prediction_match.group(1) if crop_prediction_match else None

    # --- Comprehensive Knowledge Base ---
    CROP_SOIL_SUITABILITY = {
        "riz": {
            "général": "Le riz est une céréale qui aime l\'eau et les climats chauds. Il est à la base de l\'alimentation de milliards de personnes.",
            "sol sableux": {"suitability": "possible", "recommendation": "Le riz nécessite beaucoup d\'eau. Dans un sol sableux, une irrigation intensive et un apport en matière organique sont cruciaux pour retenir l\'humidité."},
            "sol argileux": {"suitability": "idéal", "recommendation": "Excellent pour la riziculture inondée car il retient bien l\'eau. Un bon drainage est cependant nécessaire pour éviter l\'asphyxie des racines."},
            "sol limoneux": {"suitability": "bon", "recommendation": "Très bon choix. Ce sol fertile retient bien l\'eau tout en offrant un bon drainage, des conditions idéales pour le riz."},
            "sol noir": {"suitability": "bon", "recommendation": "Très fertile et riche, ce sol convient bien au riz, offrant une excellente rétention des nutriments et de l\'eau."},
            "sol alluvial": {"suitability": "idéal", "recommendation": "Idéal pour le riz en raison de sa grande fertilité et de sa bonne capacité de rétention d\'eau."},
            "sol rouge": {"suitability": "possible", "recommendation": "Possible avec des amendements pour améliorer la rétention d\'eau et la fertilité. Une analyse de sol est recommandée."},
            "sol latérite": {"suitability": "non recommandé", "recommendation": "Difficile pour le riz car souvent acide et pauvre. Nécessite des amendements importants (chaux, engrais, matière organique)."}
        },
        "maïs": {
            "général": "Le maïs est une culture polyvalente, utilisée pour l\'alimentation humaine et animale. Il apprécie le soleil et les sols riches.",
            "sol sableux": {"suitability": "possible", "recommendation": "Le maïs peut y pousser, mais demande un arrosage fréquent et un bon apport en nutriments car le sol draine vite."},
            "sol argileux": {"suitability": "bon", "recommendation": "Bonne rétention des nutriments. Assurez un bon drainage pour éviter l\'excès d\'eau qui peut nuire aux racines."},
            "sol limoneux": {"suitability": "idéal", "recommendation": "Excellent pour le maïs. Offre un équilibre parfait entre drainage, rétention d\'eau et richesse en nutriments."},
            "sol noir": {"suitability": "idéal", "recommendation": "Très fertile et bien structuré, c\'est un sol de choix pour une bonne récolte de maïs."},
            "sol alluvial": {"suitability": "bon", "recommendation": "Très fertile et bien drainé, ce qui le rend excellent pour la culture du maïs."},
            "sol rouge": {"suitability": "possible", "recommendation": "La fertilité varie. Le maïs peut y être cultivé, mais une analyse de sol aidera à déterminer les besoins en engrais."},
            "sol latérite": {"suitability": "non recommandé", "recommendation": "Acide et pauvre. Nécessite un amendement avec de la chaux et un apport conséquent en matière organique et engrais."}
        },
        "pois chiche": {
            "général": "Le pois chiche est une légumineuse résistante à la sécheresse, appréciée pour sa richesse en protéines. Il préfère les climats semi-arides.",
            "sol sableux": {"suitability": "idéal", "recommendation": "Très bien adapté. Le pois chiche préfère les sols légers et bien drainés et tolère bien la sécheresse."},
            "sol argileux": {"suitability": "non recommandé", "recommendation": "Moins idéal. Le sol doit être très bien drainé pour éviter les maladies racinaires."},
            "sol limoneux": {"suitability": "bon", "recommendation": "Bonne option. Le sol limoneux bien drainé convient parfaitement à la culture du pois chiche."},
            "sol noir": {"suitability": "bon", "recommendation": "Convient bien, à condition que le drainage soit suffisant pour cette culture qui n\'aime pas l\'excès d\'humidité."},
            "sol alluvial": {"suitability": "possible", "recommendation": "Bonne fertilité, mais le drainage est clé. À éviter si le sol est sujet à l\'engorgement."},
            "sol rouge": {"suitability": "bon", "recommendation": "Bien adapté, car souvent bien drainé. La fertilité peut nécessiter un complément."},
            "sol latérite": {"suitability": "possible", "recommendation": "Peut convenir s\'il est bien drainé, mais un apport en phosphore est souvent nécessaire."}
        },
        "haricot rouge": {
            "général": "Le haricot rouge est une légumineuse populaire riche en fer et en protéines. Il pousse bien dans des conditions tempérées.",
            "sol sableux": {"suitability": "possible", "recommendation": "Acceptable avec une irrigation et une fertilisation régulières pour compenser le drainage rapide."},
            "sol argileux": {"suitability": "non recommandé", "recommendation": "Le drainage est crucial. Un sol argileux lourd peut causer des problèmes de pourriture des racines."},
            "sol limoneux": {"suitability": "idéal", "recommendation": "Idéal. Ce sol offre une bonne structure, un bon drainage et une bonne fertilité pour les haricots."},
            "sol noir": {"suitability": "bon", "recommendation": "Très bon choix en raison de sa fertilité, à condition que le sol ne soit pas trop humide."},
            "sol alluvial": {"suitability": "bon", "recommendation": "Excellent, car fertile et généralement bien drainé."},
            "sol rouge": {"suitability": "bon", "recommendation": "Convient bien. Une analyse de sol peut aider à ajuster les nutriments."},
            "sol latérite": {"suitability": "possible", "recommendation": "Possible avec des amendements pour corriger le pH et améliorer la fertilité."}
        }
    }
    # Ajouter des alias pour les cultures
    CROP_ALIASES = {
        "haricots rouges": "haricot rouge",
        "pois chiches": "pois chiche",
        "mais": "maïs",
        "noix de coco": "noix de coco",
        "pommes": "pomme",
        "oranges": "orange",
        "papayes": "papaye",
        "melons": "melon",
        "pastèques": "pastèque",
        "raisins": "raisin",
        "mangues": "mangue",
        "grenades": "grenade",
        "lentilles": "lentille",
        "haricot": "haricot rouge" # Alias générique
    }

    user_message_lower = user_message.lower()

    # ---
    # New Conversational Logic
    # ---

    # 1. Greeting
    if "bonjour" in user_message_lower or "salut" in user_message_lower:
        return "Bonjour ! Je suis SoilClassifier IA, une IA créée par deux élèves ingénieurs, TCHOUPE GERMAIN BOVAL et ROGER ALEX. Comment puis-je vous aider aujourd\'hui concernant les sols ou les cultures ?"

    # 2. Extract entities (crop and soil)
    crop_mentioned = None
    for alias, official_name in CROP_ALIASES.items():
        if alias in user_message_lower:
            crop_mentioned = official_name
            break
    if not crop_mentioned:
        for crop in CROP_SOIL_SUITABILITY.keys():
            if crop in user_message_lower:
                crop_mentioned = crop
                break

    soil_type_mentioned = None
    soil_types = ["sableux", "argileux", "limoneux", "noir", "alluvial", "rouge", "latérite"]
    for soil in soil_types:
        if "sol " + soil in user_message_lower:
            soil_type_mentioned = "sol " + soil
            break

    # 3. Handle user providing soil type after being asked
    if not crop_mentioned and soil_type_mentioned and last_bot_message and "j\'ai besoin de connaître votre type de sol" in last_bot_message:
        crop_match = re.search(r'sur la culture de ([\w\s\'-]+)', last_bot_message)
        if not crop_match:
             crop_match = re.search(r'sur le ([\w\s\'-]+)', last_bot_message)
        
        if crop_match:
            crop_mentioned = crop_match.group(1).strip()
            # Now we have both, we can proceed to give the recommendation

    # 4. Route to the correct response logic

    # Case A: Crop and Soil are known
    if crop_mentioned and soil_type_mentioned:
        recommendation_data = CROP_SOIL_SUITABILITY.get(crop_mentioned, {}).get(soil_type_mentioned)
        if recommendation_data:
            return f"Pour un sol de type \"{soil_type_mentioned.title()}\" et la culture de {crop_mentioned}, voici la recommandation : {recommendation_data['recommendation']}"
        else:
            return f"Je n\'ai pas d\'information pour la combinaison de {crop_mentioned} et {soil_type_mentioned}."

    # Case B: Only Crop is mentioned
    if crop_mentioned:
        general_info = CROP_SOIL_SUITABILITY.get(crop_mentioned, {}).get("général", f"Je n\'ai pas d\'information générale sur {crop_mentioned}.")
        if latest_soil_type:
            soil_type_lower = latest_soil_type.lower()
            matched_soil_key = None
            for key in CROP_SOIL_SUITABILITY.get(crop_mentioned, {}).keys():
                if soil_type_lower in key:
                    matched_soil_key = key
                    break
            if matched_soil_key:
                recommendation_data = CROP_SOIL_SUITABILITY[crop_mentioned][matched_soil_key]
                return f"Pour votre sol de type \"{latest_soil_type}\", voici une recommandation pour la culture de {crop_mentioned} : {recommendation_data['recommendation']}"
        # If no soil type in context, give general info and ask for soil type
        return f"{general_info} Pour une recommandation plus précise, quel est votre type de sol ?"

    # Case C: Only Soil is mentioned
    if soil_type_mentioned:
        suitable_crops = []
        for crop, soils in CROP_SOIL_SUITABILITY.items():
            if soil_type_mentioned in soils:
                if soils[soil_type_mentioned]["suitability"] in ["idéal", "bon"]:
                    suitable_crops.append(crop)
        if suitable_crops:
            return f"Pour un {soil_type_mentioned}, vous pourriez envisager les cultures suivantes : {', '.join(suitable_crops)}."
        else:
            return f"Je n\'ai pas de recommandations de cultures spécifiques pour un {soil_type_mentioned}."

    # Case D: General recommendation request
    if "recommandation" in user_message_lower:
        return "Sur quelle culture ou sur quel sol souhaitez-vous des recommandations ?"

    # 5. General questions about predictions
    if "dernière prédiction de sol" in user_message_lower or "mon sol" in user_message_lower:
        if latest_soil_type:
            return f"Votre dernière prédiction de sol est : \"{latest_soil_type}\" avec une confiance de {latest_soil_confidence}%."
        else:
            return "Je n\'ai pas trouvé de dernière prédiction de sol pour vous. Avez-vous déjà effectué une analyse ?"

    if "dernière prédiction de culture" in user_message_lower or "ma culture" in user_message_lower or "culture recommandée" in user_message_lower:
        if latest_crop_type:
            return f"Votre dernière prédiction de culture est : \"{latest_crop_type}\"."
        else:
            return "Je n\'ai pas trouvé de dernière prédiction de culture pour vous. Avez-vous déjà effectué une analyse de caractéristiques ?"

    # 6. Fallback and other topics
    if "merci" in user_message_lower:
        return "De rien ! N\'hésitez pas si vous avez d\'autres questions sur les sols ou les cultures."
    elif "hors sujet" in user_message_lower or "autre chose" in user_message_lower or "donne moi les types de sols possible" in user_message_lower:
        return "Je suis là pour vous aider avec des questions liées aux sols et aux cultures. Concentrons-nous sur ce sujet, d\'accord ? Si vous avez une prédiction de sol ou de culture, je peux vous donner des recommandations."
    else:
        return "Je ne suis pas sûr de comprendre. Vous pouvez me poser des questions sur les recommandations de culture ou sur votre historique d\'analyse."


@csrf_exempt
@login_required
def send_message_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')

        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)

        user = request.user

        # Save user message
        ChatMessage.objects.create(
            user=user,
            message=user_message,
            is_from_user=True
        )

        # Fetch user's latest predictions for context
        latest_soil_prediction = Prediction.objects.filter(user=user).order_by('-timestamp').first()
        latest_crop_prediction = CropPrediction.objects.filter(user=user).order_by('-timestamp').first()
        last_bot_message_obj = ChatMessage.objects.filter(user=user, is_from_user=False).order_by('-timestamp').first()
        last_bot_message = last_bot_message_obj.message if last_bot_message_obj else None

        context_info = ""
        if latest_soil_prediction:
            context_info += f"\nVotre dernière prédiction de sol: {latest_soil_prediction.soil_type} (Confiance: {latest_soil_prediction.confidence:.2f}%)."
        if latest_crop_prediction:
            context_info += f"\nVotre dernière prédiction de culture: {latest_crop_prediction.predicted_crop}."
        
        # Construct LLM prompt
        llm_prompt = (
            f"Vous êtes SoilClassifier IA, un assistant expert en sols et cultures. "
            f"Votre objectif est de fournir des recommandations et de répondre aux questions des utilisateurs "
            f"strictement liées à leurs prédictions de sol et de culture. "
            f"Si l\'utilisateur s\'éloigne du sujet, ramenez-le gentiment sur le thème des sols et des cultures. "
            f"Voici le message de l\'utilisateur: \"{user_message}\"."
            f"{context_info}"
            f"\nRépondez de manière concise et utile."
        )

        bot_response_text = get_llm_response(llm_prompt, last_bot_message=last_bot_message)

        # Save bot response
        ChatMessage.objects.create(
            user=user,
            message=bot_response_text,
            is_from_user=False
        )

        return JsonResponse({'message': bot_response_text})
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def chat_history_api(request):
    messages = ChatMessage.objects.filter(user=request.user).order_by('timestamp')
    history = []
    for msg in messages:
        history.append({
            'id': msg.id,
            'message': msg.message,
            'is_from_user': msg.is_from_user,
            'timestamp': msg.timestamp.isoformat()
        })
    return JsonResponse(history, safe=False)

@csrf_exempt
@login_required
def delete_message_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message_id = data.get('message_id')
        if not message_id:
            return JsonResponse({'error': 'Message ID not provided'}, status=400)

        try:
            # Get the message and ensure it belongs to the current user
            message = ChatMessage.objects.get(id=message_id, user=request.user)
            message.delete()
            return JsonResponse({'status': 'success', 'message': 'Message deleted'})
        except ChatMessage.DoesNotExist:
            # Return 403 to prevent checking for message existence
            return JsonResponse({'error': 'Message not found or permission denied'}, status=403)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
@login_required
def clear_chat_history_api(request):
    if request.method == 'POST':
        try:
            ChatMessage.objects.filter(user=request.user).delete()
            return JsonResponse({'status': 'success', 'message': 'Chat history cleared'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)