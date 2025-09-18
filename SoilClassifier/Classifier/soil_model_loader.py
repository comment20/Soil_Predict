import tensorflow as tf
import numpy as np
from django.conf import settings
import os

# Construire le chemin absolu vers le modèle
model_path = os.path.join(settings.BASE_DIR, 'sol_classification.h5')

# Charger le modèle une seule fois
model = tf.keras.models.load_model(model_path, compile=False)

# Dictionnaire des classes de sol, trié par ordre alphabétique pour correspondre au modèle
class_names = {
    0: 'Sol Alluvial', 1: 'Sol Andosol', 2: 'Sol Aride', 3: 'Sol noire', 4: 'Sol de cendre', 5: 'Sol Argileux', 6: 'Entisol',
    7: 'Humus', 8: 'Inceptisol', 9: 'Sol Latérite', 10: 'Sol de Montagne', 11: 'Sol Sableux', 12: 'Sol Tourbe',
    13: 'Sol Rouge', 14: 'Sol sableux', 15: 'Sol sablo argileux', 16: 'Sol jaune', 17: 'Sol Crayeux', 18: 'Sol Charbonneux',
    19: 'Sol sechesse', 20: 'image non sol', 21: 'mary', 22: 'normal', 23: 'le sable', 24: 'limon',
    25: 'sol avec insects'
}

def predict_soil(image_path):
    input_shape = model.input_shape[1:3] 
    img = tf.keras.utils.load_img(image_path, target_size=input_shape)
    img_array = tf.keras.utils.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0

    pred = model.predict(img_array)[0]
    predicted_index = np.argmax(pred)
    confidence = pred[predicted_index] * 100

    # Utilise .get() pour une récupération sûre du nom de la classe
    predicted_label = class_names.get(predicted_index, "Classe non définie")

    return predicted_label, confidence
