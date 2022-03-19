from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import csv
from daily_reports.models import DailyReports


@csrf_exempt
def dailyreports(request, dailyreport_name):
    if request.method == 'POST':
        return dailyreports_post(request, dailyreport_name)
    elif request.method == 'GET':
        return dailyreports_get(request, dailyreport_name)
    elif request.method == 'DELETE':
        return dailyreports_delete(request, dailyreport_name)
    else:
        return HttpResponse('Internal server error', status=500)


def dailyreports_post(request, dailyreport_name):
    return HttpResponse('Received {}'.format(dailyreport_name))


def dailyreports_get(request, dailyreport_name):
    return HttpResponse('Received {}'.format(dailyreport_name))


def dailyreports_delete(request, dailyreport_name):
    return HttpResponse('Received {}'.format(dailyreport_name))
