from django.urls import path

from . import views

urlpatterns = [
    path('<str:timeseries_name>/<str:data_type>', views.timeseries, name='timeseries'),
]