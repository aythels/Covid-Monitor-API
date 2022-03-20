from django.urls import path

from . import views

urlpatterns = [
    path('<str:dailyreport_name>', views.dailyreports, name='dailyreports')
]
