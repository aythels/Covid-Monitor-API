from django.urls import path

from . import views

urlpatterns = [
    path('<str:timeseries_name>', views.timeseries, name='timeseries'),
]
