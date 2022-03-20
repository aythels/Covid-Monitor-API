from django.shortcuts import render

# Create your views here.
from io import StringIO
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


def _fill_empty(data):
    data['fips'] = -1 if data['fips'] == '' else data['fips']
    data['lat'] = 0.0 if data['lat'] == '' else data['lat']
    data['long'] = 0.0 if data['long'] == '' else data['long']


def dailyreports_post(request, dailyreport_name):
    # TODO: add methods to validate data
    body = request.body.decode('utf-8')
    reader = csv.reader(body.split('\n'), delimiter=',')
    # TODO: validate header has correct number of elements
    next(reader)

    keys = ["fips", "admin2", "province_state", "country_region", "last_update", "lat", "long",
            "confirmed", "deaths", "recovered", "active", "combined_key", "incident_rate", "case_fatality_ratio"]

    create_queue, update_queue = [], []
    for row in reader:
        # TODO: validate row has same number of elements as keys
        data = {
            k: row[i] for i, k in enumerate(keys)
        }
        # TODO: validate country_region non empty, last_update non empty, confirmed, deaths, recovered, active, incident_rate, case_fatality_ratio non empty
        _fill_empty(data)
        dailyreports_entry = DailyReports.objects.filter(province_state=data["province_state"], country_region=data["country_region"],
                                                         last_update=data["last_update"]).first()
        if not dailyreports_entry:
            dailyreports_entry = DailyReports(**data)
            create_queue.append(dailyreports_entry)
        else:
            dailyreports_entry.confirmed, dailyreports_entry.deaths, dailyreports_entry.recovered, dailyreports_entry.active,
            dailyreports_entry.incident_rate, dailyreports_entry.case_fatality_ratio = data[
                "confirmed"], data["deaths"], data["recovered"], data["active"],
            data["incident_rate"], data["case_fatality_ratio"]
            update_queue.append(dailyreports_entry)

    DailyReports.objects.bulk_create(create_queue)
    DailyReports.objects.bulk_update(update_queue, [
                                     "confirmed", "deaths", "recovered", "active", "incident_rate", "case_fatality_ratio"])

    return HttpResponse('Upload successful', status=200)


def dailyreports_get(request, dailyreport_name):
    return HttpResponse('Received {}'.format(dailyreport_name))


def dailyreports_delete(request, dailyreport_name):
    return HttpResponse('Received {}'.format(dailyreport_name))
