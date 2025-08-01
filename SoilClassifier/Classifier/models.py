from django.db import models
# --- models.py (dans ton app "classifier") ---
from django.db import models

class Prediction(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    image_name = models.CharField(max_length=255)
    soil_type = models.CharField(max_length=50)
    confidence = models.FloatField()

    def __str__(self):
        return f"{self.timestamp} - {self.soil_type} ({self.confidence}%)"


# Create your models here.
