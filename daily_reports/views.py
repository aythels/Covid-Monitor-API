from datetime import datetime, date, timedelta
from django.shortcuts import render

# Create your views here.
from io import StringIO
from django.http import HttpResponse, JsonResponse
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
    return HttpResponse('Internal server error', status=500)


def dailyreports_post(request, dailyreport_name):
    body = request.body.decode('utf-8')
    reader = csv.reader(body.split('\n'), delimiter=',')

    # Validating header
    header = next(reader)
    if not validate_header(header):
        return HttpResponse('Malformed request', status=400)

    create_queue = []
    update_queue = []

    for row in reader:
        data = parse_post_row(header, row)

        # Validating row
        if not data:
            return HttpResponse('Malformed request', status=400)

        data['dailyreport_name'] = dailyreport_name

        dailyreports_entry = DailyReports.objects.filter(dailyreport_name=data["dailyreport_name"],
                                                         province_state=data["province_state"],
                                                         country_region=data["country_region"],
                                                         last_update=data["last_update"]).first()
        if not dailyreports_entry:
            dailyreports_entry = DailyReports(**data)
            create_queue.append(dailyreports_entry)
        else:
            dailyreports_entry.confirmed = data["confirmed"]
            dailyreports_entry.deaths = data["deaths"]
            dailyreports_entry.recovered = data["recovered"]
            dailyreports_entry.active = data["active"]
            dailyreports_entry.incidence_rate = data["incidence_rate"]
            dailyreports_entry.case_fatality_ratio = data["case_fatality_ratio"]
            update_queue.append(dailyreports_entry)

    # Bulk update or create
    DailyReports.objects.bulk_create(create_queue)
    DailyReports.objects.bulk_update(update_queue, [
        "confirmed",
        "deaths",
        "recovered",
        "active",
        "incidence_rate",
        "case_fatality_ratio"
    ])

    return HttpResponse('Upload successful', status=200)


def dailyreports_get(request, dailyreport_name):
    # validating params
    params = parse_get_params(request, dailyreport_name)
    if not params:
        return HttpResponse('Malformed request', status=400)

    query = {
        "dailyreport_name": params["dailyreport_name"],
        "last_update__range": [params["start_date"], params["end_date"]]
    }
    if params["countries"]:
        query["country_region__in"] = params["countries"]
    if params["regions"]:
        query["province_state__in"] = params["regions"]
    if params["combined_key"]:
        query["combined_key__exact"] = params["combined_key"]

    dailyreports_list = DailyReports.objects.filter(**query)

    if params["format"] == "json":
        return get_response_json(dailyreports_list, params["data_type"])
    return get_response_csv(dailyreports_list, params["data_type"])


def dailyreports_delete(request, dailyreport_name):
    dailyreports_entries = DailyReports.objects.filter(
        dailyreport_name=dailyreport_name)

    if dailyreports_entries:
        dailyreports_entries.delete()
        return HttpResponse('Successfully deleted', status=200)
    return HttpResponse('Dailyreports not found', status=404)


# **************************************************************************************************** HELPER FUNCTIONS

def get_response_json(dailyreports_list, data_type):
    data = {}

    for index, dailyreport in enumerate(dailyreports_list):
        row = {
            'Province_State': dailyreport.province_state,
            'Country_Region': dailyreport.country_region,
            'Last_Update': dailyreport.last_update.strftime("%Y-%m-%d %H:%M:%S"),
            'Combined_Key': dailyreport.combined_key,
            'Incidence_Rate': dailyreport.incidence_rate,
            'Case-Fatality_Ratio': dailyreport.case_fatality_ratio,
        }

        if "active" in data_type:
            row["Active"] = dailyreport.active
        if "confirmed" in data_type:
            row["Confirmed"] = dailyreport.confirmed
        if "deaths" in data_type:
            row["Deaths"] = dailyreport.deaths
        if "recovered" in data_type:
            row["Recovered"] = dailyreport.recovered

        data[index] = row

    return JsonResponse(data)


def get_response_csv(dailyreports_list, data_type):
    response = HttpResponse(content_type='application/csv')

    writer = csv.writer(response)
    writer.writerow(
        ['Province_State', 'Country_Region', 'Last_Update'] +
        [x.title() for x in data_type] +
        ['Combined_Key', 'Incidence_Rate', 'Case-Fatality_Ratio']
    )
    for dailyreport in dailyreports_list:
        prefix = [
            dailyreport.province_state,
            dailyreport.country_region,
            dailyreport.last_update,
        ]

        middle = []

        if "active" in data_type:
            middle.append(dailyreport.active)
        if "confirmed" in data_type:
            middle.append(dailyreport.confirmed)
        if "deaths" in data_type:
            middle.append(dailyreport.deaths)
        if "recovered" in data_type:
            middle.append(dailyreport.recovered)

        suffix = [
            dailyreport.combined_key,
            dailyreport.incidence_rate,
            dailyreport.case_fatality_ratio,
        ]
        writer.writerow(prefix + middle + suffix)
    return response


def validate_header(header):
    # Not enough columns
    if len(header) < 14:
        return False

    # Invalid Column Headers
    column_strings = [
        'FIPS',
        'Admin2',
        'Province_State',
        'Country_Region',
        'Last_Update',
        'Lat',
        'Long_',
        'Confirmed',
        'Deaths',
        'Recovered',
        'Active',
        'Combined_Key',
        'Incidence_Rate',
        'Case-Fatality_Ratio']
    for i in range(len(header)):
        if header[i] != column_strings[i]:
            return False
    return True


def parse_post_row(header, row):
    # Not enough columns
    if len(row) < len(header):
        return None

    # Assigning default values
    params = {
        "fips": -1 if row[0] == '' else row[0],
        "admin2": row[1],
        "province_state": row[2],
        "country_region": row[3],
        "last_update": row[4],
        "lat": 0.0 if row[5] == '' else row[5],
        "long": 0.0 if row[6] == '' else row[6],
        "confirmed": 0 if row[7] == '' else row[7],
        "deaths": 0 if row[8] == '' else row[8],
        "recovered": 0 if row[9] == '' else row[9],
        "active": 0 if row[10] == '' else row[10],
        "combined_key": row[11],
        "incidence_rate": row[12],
        "case_fatality_ratio": row[13],
    }

    # Default value check
    non_empty_keys = ["country_region", "last_update", "lat", "long", "confirmed", "deaths", "recovered", "active",
                      "incidence_rate", "case_fatality_ratio"]
    for key in non_empty_keys:
        if params[key] == "":
            return None

    # Type check

    def params_check(d_type, key):
        if params[key] != "":
            try:
                params[key] = d_type(params[key])
            except ValueError:
                return False
        return True

    if not params_check(int, 'fips'): return None
    if not params_check(float, 'lat'): return None
    if not params_check(float, 'long'): return None
    if not params_check(int, 'confirmed'): return None
    if not params_check(int, 'deaths'): return None
    if not params_check(int, 'recovered'): return None
    if not params_check(int, 'active'): return None
    if not params_check(float, 'incidence_rate'): return None
    if not params_check(float, 'case_fatality_ratio'): return None

    if params['last_update'] != "":
        try:
            params['last_update'] = datetime.strptime(params['last_update'], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    # Other

    if params["active"] == 0:
        params["active"] = params["confirmed"] - params["deaths"] - params["recovered"]

    if -90 > params['lat'] or params['lat'] > 90 or -180 > params['long'] or params['long'] > 180:
        return None

    return params


def parse_get_params(request, dailyreport_name):
    params = {
        "dailyreport_name": dailyreport_name,
        "countries": None,
        "regions": None,
        "combined_key": None,
        "data_type": ['active', 'confirmed', 'deaths', 'recovered'],
        "start_date": date.min,
        "end_date": date.max,
        "format": 'csv',
    }

    if 'countries' in request.GET:
        params["countries"] = request.GET['countries'].split(",")
    if 'regions' in request.GET:
        params["regions"] = request.GET['regions'].split(",")
    if 'combined_key' in request.GET:
        params["combined_key"] = request.GET['combined_key']
    if 'data_type' in request.GET:
        params["data_type"] = request.GET['data_type'].split(",")
        for t in params["data_type"]:
            if t not in ['active', 'confirmed', 'deaths', 'recovered']:
                return None
    if 'start_date' in request.GET:
        try:
            params["start_date"] = datetime.strptime(request.GET['start_date'], '%Y-%m-%d')
        except ValueError:
            return None
    if 'end_date' in request.GET:
        try:
            # Adding one day to end date because of off by one error due to hours
            params["end_date"] = datetime.strptime(request.GET['end_date'], '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            return None
    if 'format' in request.GET:
        if request.GET['format'] not in ["csv", "json"]:
            return None
        params["format"] = request.GET['format']

    return params
