from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("network/", views.network, name="network"),
    path("speedtest/", views.speed_test, name="speedtest"),
]
