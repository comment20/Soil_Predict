from django.urls import path
from .views import home 
# Import de la vue
from .views import result
from .api_views import SoilPredictAPI

urlpatterns = [
    path('', home, name='home'), 
    path('result/', result, name='result'),# ✅ page d’accueil avec upload
    path('api/predict/', SoilPredictAPI.as_view(), name='api_predict'),
]
