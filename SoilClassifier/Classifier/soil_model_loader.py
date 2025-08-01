import tensorflow as tf
import numpy as np

# Charger le modèle une seule fois
model = tf.keras.models.load_model("soil_model.h5",compile=False)

class_names = {2: "Clay_Soil", 1: "Black_Soil", 3: "RED_Soil", 0: "ALLUVIAL_Soil"}

def predict_soil(image_path):
    input_shape = model.input_shape[1:3] 
    img = tf.keras.utils.load_img(image_path, target_size=input_shape)
    img_array = tf.keras.utils.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0

    pred = model.predict(img_array)[0]
    predicted_index = np.argmax(pred)
    confidence = pred[predicted_index] * 100

    return class_names[predicted_index], confidence
