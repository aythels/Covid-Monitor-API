from io import StringIO
from os import times_result
from time import clock_getres, time
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import csv

from time_series.models import TimeSeries, TimeSeriesData


@csrf_exempt
def timeseries(request, timeseries_name: str):
    if request.method == 'POST':
        return timeseries_post(request, timeseries_name)

    elif request.method == 'GET':
        return timeseries_get(request, timeseries_name)

    return HttpResponse('test route {}'.format(timeseries_name))


def timeseries_post(request, timeseries_name):
    # for some reason doc doesnt mention but this gets the params passed into URL
    data_type_converter = {'Deaths': 'D', 'Confirmed': 'C', 'Recovered': 'R'}

    if 'data_type' in request.GET:
        data_type = request.GET['data_type']
        if data_type not in data_type_converter:
            return HttpResponse('Malformed Content', status=400)
        data_type = data_type_converter[data_type]
    else:
        return HttpResponse('Malformed Content', status=400)

    body = request.body.decode('utf-8')

    f_body = StringIO(body)
    reader = csv.DictReader(f_body, delimiter=',')
    province_state_key, country_region_key, latitude_key, longitude_key, \
        *dates = reader.fieldnames
    # TODO: Create a util method that makes sure CSV fieldnames are well formated, correct string and dates are well formated

    # TODO: Create a util method to make sure no values are None in row and values are well formatted

    for row in reader:
        province_state, country_region, latitude, longitude = row[province_state_key], row[
            country_region_key], row[latitude_key], row[longitude_key]

        # check if timeseries row already exists
        timeseries_cp = TimeSeries.objects.filter(type=data_type, timeseries_name=timeseries_name, province_state=province_state,
                                                  country_region=country_region)

        if timeseries_cp:
            timeseries = timeseries_cp.first()
        else:
            timeseries = TimeSeries(type=data_type, timeseries_name=timeseries_name, province_state=province_state,
                                    country_region=country_region, latitude=latitude, longitude=longitude)
            timeseries.save()

        for date in dates:
            cases = row[date]
            timeseries_data_cp = TimeSeriesData.objects.filter(
                timeseries=timeseries, date=date).first()
            if timeseries_data_cp:
                timeseries_data_cp.cases = cases
                timeseries_data_cp.save()
            else:
                timeseries_data = TimeSeriesData(
                    timeseries=timeseries, date=date, cases=cases)
                timeseries_data.save()

    return HttpResponse('Upload Successfull')


def timeseries_get(request, timeseries_name):
    pass
