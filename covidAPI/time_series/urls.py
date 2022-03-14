from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:timeseries_name>/', views.timeseries, name='timeseries'),
]
