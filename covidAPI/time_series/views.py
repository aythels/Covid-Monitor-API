from os import times_result
from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def timeseries(request, timeseries_name):
    return HttpResponse('test route {}'.format(timeseries_name))
