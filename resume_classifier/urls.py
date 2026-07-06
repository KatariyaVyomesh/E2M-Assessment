from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from resumeapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name="home"),
    path('predict/', views.predict, name="predict"),
    path('results/', views.results, name="results"), # New results view
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')), # Silence 404s
]
