from datetime import datetime
from io import StringIO
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.http import JsonResponse
import csv
import datetime

from time_series.models import TimeSeries, TimeSeriesData
from datetime import date, time, datetime

CONSTS = {'province_state_key': 'Province/State',
          'country_region_key': 'Country/Region',
          'latitude_key': 'Lat',
          'longitude_key': 'Long'}


@csrf_exempt
def timeseries(request, timeseries_name, data_type):
    if request.method == 'POST':
        return timeseries_post(request, timeseries_name, data_type)
    elif request.method == 'GET':
        return timeseries_get(request, timeseries_name, data_type)
    elif request.method == 'DELETE':
        return timeseries_delete(timeseries_name)

    return HttpResponse('Internal server error', status=500)


def timeseries_post(request, timeseries_name, data_type):
    # TODO: VERIFY BODY (can probably just brute force this with a try and catch block)
    # return HttpResponse('Invalid file contents', status=422)

    # Parameters
    body = request.body.decode('utf-8')

    # Writing CSV
    reader = csv.reader(body.split('\n'), delimiter=',')
    header_dates = next(reader, None)[4:]
    to_create = []
    to_update = []

    for row in reader:
        # Writing TimeSeries
        data = {
            "timeseries_name": timeseries_name,
            "data_type": TimeSeries.TypeChoice[data_type.upper()],
            "province_state": row[0],
            "country_region": row[1],
            "lat": row[2],
            "long": row[3],
        }

        # Search for TimeSeries and create it if it does not exist
        # TODO: Allow overwriting of province_state, country_region and lat and long fields?
        timeseries_entry = TimeSeries.objects.filter(**data).first()
        if not timeseries_entry:
            timeseries_entry = TimeSeries(**data)
            timeseries_entry.save()

        # Writing TimeSeriesData
        for index, value in enumerate(row[4:]):
            data = {
                "timeseries": timeseries_entry,
                "date": convert_date(header_dates[index]),
                "cases": value,
            }

            # Search for TimeSeriesData by timeseries and date and create it if it does not exist
            timeseries_data_entry = TimeSeriesData.objects.filter(
                timeseries=data["timeseries"],
                date=data["date"]).first()
            if not timeseries_data_entry:
                timeseries_data_entry = TimeSeriesData(**data)
                to_create.append(timeseries_data_entry)
            else:
                timeseries_data_entry.cases = data["cases"]
                to_update.append(timeseries_data_entry)

    # Update or Create all TimeSeriesData at once
    TimeSeriesData.objects.bulk_create(to_create)
    TimeSeriesData.objects.bulk_update(to_update, ['cases'])

    return HttpResponse('Upload successful', status=200)


def timeseries_get(request, timeseries_name, data_type):
    # TODO: VERIFY PARAMETERS
    # return HttpResponse('Invalid file contents', status=422)

    # parameters
    countries = request.GET['countries'].split(",") if 'countries' in request.GET else None
    regions = request.GET['regions'].split(",") if 'regions' in request.GET else None
    start_date = convert_date(request.GET['start_date']) if 'start_date' in request.GET else date.min
    end_date = convert_date(request.GET['end_date']) if 'end_date' in request.GET else date.max
    format = request.GET['format'] if 'format' in request.GET else 'csv'

    # Creating query
    query = {
        "timeseries_name": timeseries_name,
        "data_type": TimeSeries.TypeChoice[data_type.upper()],
    }
    if countries: query["country_region__in"] = countries
    if regions: query["province_state__in"] = regions

    # Getting associated data entries based on query
    timeseries_list = TimeSeries.objects.filter(**query)

    if timeseries_list:
        timeseriesdata_list = TimeSeriesData.objects.filter(timeseries__in=timeseries_list, date__range=[start_date, end_date])
        if format == "json":
            return gen_response_json(timeseries_list, timeseriesdata_list)
        return gen_response_csv(timeseries_list, timeseriesdata_list)

    return HttpResponse('Malformed request', status=400)


def timeseries_delete(timeseries_name):
    # Getting associated data entries
    timeseries_entries = TimeSeries.objects.filter(timeseries_name=timeseries_name)

    # Deleting entries
    if timeseries_entries:
        timeseries_entries.delete()
        return HttpResponse('Successfully deleted', status=200)

    return HttpResponse('Timeseries not found', status=404)


# **************************************************************************************************** HELPER FUNCTIONS

def gen_response_json(timeseries_list, timeseriesdata_list):
    #data = serializers.serialize("json", timeseries_list)
    response = JsonResponse({'foo': 'bar'})
    # TODO: Implement this

    return response


def gen_response_csv(timeseries_list, timeseriesdata_list):
    # https://docs.djangoproject.com/en/4.0/ref/models/querysets/
    # https://docs.djangoproject.com/en/4.0/howto/outputting-csv/
    response = HttpResponse(content_type='application/csv')

    dates = []
    for date in timeseriesdata_list.values_list('date', flat=True).distinct().order_by('date'):
        dates.append(date.strftime("%m/%d/%y"))

    writer = csv.writer(response)
    writer.writerow(['Province/State', 'Country/Region', 'Lat', 'Long'] + dates)

    for timeseries in timeseries_list:
        prefix = [
            timeseries.province_state,
            timeseries.country_region,
            timeseries.lat,
            timeseries.long,
        ]

        suffix = timeseriesdata_list.filter(timeseries=timeseries).values_list('cases', flat=True).order_by('date')
        writer.writerow(prefix + list(suffix))

    return response


def convert_date(date):
    # 1/23/20 to 2020-01-23
    date_split = date.split('/')

    month = date_split[0].zfill(2)
    day = date_split[1].zfill(2)
    year = date_split[2]

    new_date = month + "-" + day + "-" + year

    return datetime.datetime.strptime(new_date, '%m-%d-%y')
