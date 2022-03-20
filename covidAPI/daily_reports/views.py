from datetime import datetime, date
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
        data['dailyreport_name'] = dailyreport_name
        # TODO: validate country_region non empty, last_update non empty, confirmed, deaths, recovered, active, incident_rate, case_fatality_ratio non empty
        _fill_empty(data)
        dailyreports_entry = DailyReports.objects.filter(dailyreport_name=dailyreport_name, province_state=data["province_state"], country_region=data["country_region"],
                                                         last_update=data["last_update"]).first()
        if not dailyreports_entry:
            dailyreports_entry = DailyReports(**data)
            create_queue.append(dailyreports_entry)
        else:
            dailyreports_entry.confirmed, dailyreports_entry.deaths, dailyreports_entry.recovered, dailyreports_entry.active, dailyreports_entry.incident_rate, dailyreports_entry.case_fatality_ratio = data[
                "confirmed"], data["deaths"], data["recovered"], data["active"], data["incident_rate"], data["case_fatality_ratio"]
            update_queue.append(dailyreports_entry)

    DailyReports.objects.bulk_create(create_queue)
    DailyReports.objects.bulk_update(update_queue, [
                                     "confirmed", "deaths", "recovered", "active", "incident_rate", "case_fatality_ratio"])

    return HttpResponse('Upload successful', status=200)


def dailyreports_get(request, dailyreport_name):
    countries = request.GET['countries'].split(
        ",") if 'countries' in request.GET else None
    regions = request.GET['regions'].split(
        ",") if 'regions' in request.GET else None
    combined_key = request.GET['combined_key'] if 'combined_key' in request.GET else None
    data_type = request.GET['data_type'].split(",") if 'data_type' in request.GET else [
        'active', 'confirmed', 'deaths', 'recovered']
    start_date = convert_date(
        request.GET['start_date']) if 'start_date' in request.GET else date.min
    end_date = convert_date(
        request.GET['end_date']) if 'end_date' in request.GET else date.max
    format = request.GET['format'] if 'format' in request.GET else 'csv'

    query = {
        "dailyreport_name": dailyreport_name,
    }
    if countries:
        query["country_region__in"] = countries
    if regions:
        query["province_state__in"] = regions
    if combined_key:
        query["combined_key__exact"] = combined_key
    query["last_update__range"] = [start_date, end_date]

    dailyreports_list = DailyReports.objects.filter(**query)
    if format == "json":
        get_response_json(dailyreports_list, data_type)
    else:
        return get_response_csv(dailyreports_list, data_type)

    return HttpResponse('Received {}'.format(dailyreport_name))


def dailyreports_delete(request, dailyreport_name):
    dailyreports_entries = DailyReports.objects.filter(
        dailyreport_name=dailyreport_name)

    if dailyreports_entries:
        dailyreports_entries.delete()
        return HttpResponse('Successfully deleted', status=200)
    return HttpResponse('Dailyreports not found', status=404)


def get_response_csv(dailyreports_list, data_type):
    response = HttpResponse(content_type='application/csv')

    writer = csv.writer(response)
    writer.writerow(
        ['Province_State', 'Country_Region', 'Last_Update'] + data_type +
        ['Combined_Key', 'Incidence_Rate', 'Case-Fatality_Ratio']
    )
    for dailyreport in dailyreports_list:
        prefix = [
            dailyreport.province_state,
            dailyreport.country_region,
            dailyreport.last_update,
        ]

        middle = []
        for type in data_type:
            if type == "active":
                middle.append(dailyreport.active)
            elif type == "confirmed":
                middle.append(dailyreport.confirmed)
            elif type == "deaths":
                middle.append(dailyreport.deaths)
            else:
                middle.append(dailyreport.recovered)
        suffix = [
            dailyreport.combined_key,
            dailyreport.incident_rate,
            dailyreport.case_fatality_ratio,
        ]
        writer.writerow(prefix + middle + suffix)
    return response


def convert_date(date):
    return datetime.strptime(date, '%y-%m-%d')
