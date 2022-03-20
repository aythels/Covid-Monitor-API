from io import StringIO
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import csv

from time_series.models import TimeSeries, TimeSeriesData
from datetime import date, datetime

# TODO Probably need a try catch block when saving to database due to character count or database errors

@csrf_exempt
def timeseries(request, timeseries_name, data_type):
    if request.method == 'POST':
        return timeseries_post(request, timeseries_name, data_type)
    elif request.method == 'GET':
        return timeseries_get(request, timeseries_name, data_type)
    elif request.method == 'DELETE':
        return timeseries_delete(request, timeseries_name)
    return HttpResponse('Internal server error', status=500)


def timeseries_post(request, timeseries_name, data_type):
    # Getting and verifying parameters
    params = parse_post_params(timeseries_name, data_type)
    if params is None:
        return HttpResponse('Malformed request', status=400)

    # Processing body
    body = request.body.decode('utf-8')

    reader = csv.reader(body.split('\n'), delimiter=',')

    # Array of header titles and date objects
    parsed_header = parse_post_header(next(reader, None))
    if parsed_header is None:
        return HttpResponse('Malformed request', status=400)

    # Array of row data objects
    parsed_rows = []

    # May be less memory efficient to do it this way but its a lot cleaner
    for row in reader:
        parsed_row = parse_post_row(parsed_header, row)
        if parsed_row is None:
            return HttpResponse('Malformed request', status=400)
        parsed_rows.append(parsed_row)

    for row in parsed_rows:
        # Writing TimeSeries
        data = {
            "timeseries_name": params["timeseries_name"],
            "data_type": params["data_type"],
            "province_state": row['Province/State'],
            "country_region": row['Country/Region'],
            "lat": row['Lat'],
            "long": row['Long'],
        }

        timeseries_entry, created = TimeSeries.objects.update_or_create(
            data_type=data["data_type"],
            timeseries_name=data["timeseries_name"],
            province_state=data["province_state"],
            country_region=data["country_region"],
            defaults=data,
        )

        to_create = []
        to_update = []

        timeseries_data_entry_all = TimeSeriesData.objects.filter(
            timeseries=timeseries_entry
        )

        # Writing TimeSeriesData
        for index, date in enumerate(parsed_header[4:]):
            data = {
                "timeseries": timeseries_entry,
                "date": date,
                "cases": row['CASES'][index],
            }

            # Search for TimeSeriesData by timeseries and date and create it if it does not exist
            timeseries_data_entry = timeseries_data_entry_all.filter(date=data["date"]).first()
            if not timeseries_data_entry:
                timeseries_data_entry = TimeSeriesData(**data)
                to_create.append(timeseries_data_entry)
            else:
                timeseries_data_entry.cases = data["cases"]
                to_update.append(timeseries_data_entry)

        # Update or Create all TimeSeriesData each iteration. **Tried updating all at once but incremental update still has fastest speed
        TimeSeriesData.objects.bulk_create(to_create)
        TimeSeriesData.objects.bulk_update(to_update, ['cases'])

    return HttpResponse('Upload successful', status=200)


def timeseries_get(request, timeseries_name, data_type):
    # TODO FIX ACTIVE FETCH

    # Getting and verifying parameters
    params = parse_get_params(request, timeseries_name, data_type)
    if params is None:
        return HttpResponse('Malformed request', status=400)

    # Creating query
    query = {
        "timeseries_name": params["timeseries_name"],
    }

    if params["data_type"] != "ACTIVE":
        query["data_type"] = params["data_type"]
    if params["countries"] is not None:
        query["country_region__in"] = params["countries"]
    if params["regions"] is not None:
        query["province_state__in"] = params["regions"]

    # Getting associated data entries based on query
    timeseries_list = TimeSeries.objects.filter(**query)

    if timeseries_list:
        timeseriesdata_list = TimeSeriesData.objects.filter(
            timeseries__in=timeseries_list, date__range=[params["start_date"], params["end_date"]])
        if params["format"] == "json":
            return gen_response_json(timeseries_list, timeseriesdata_list)
        return gen_response_csv(timeseries_list, timeseriesdata_list)

    return HttpResponse('Malformed request', status=400)


def timeseries_delete(request, timeseries_name):
    # Getting associated data entries
    timeseries_entries = TimeSeries.objects.filter(
        timeseries_name=timeseries_name)

    # Deleting entries
    if timeseries_entries:
        timeseries_entries.delete()
        return HttpResponse('Successfully deleted', status=200)

    return HttpResponse('Timeseries not found', status=404)


# **************************************************************************************************** HELPER FUNCTIONS

def parse_post_header(header):
    # Not enough columns
    if len(header) < 5:
        return None

    # Invalid columns headers
    if header[0] != 'Province/State':
        return None
    if header[1] != 'Country/Region':
        return None
    if header[2] != 'Lat':
        return None
    if header[3] != 'Long':
        return None

    # Invalid column dates
    dates = []
    for date in header[4:]:
        try:
            date_obj = datetime.strptime(date, "%m/%d/%y")
            dates.append(date_obj)
        except ValueError:
            return None

    return header[:4] + dates


def parse_post_row(header, row):
    # Not enough columns
    if len(row) != len(header):
        return None

    params = {
        'Province/State': row[0],
        'Country/Region': row[1],
        'Lat': 0.0 if row[2] == '' else row[2],
        'Long': 0.0 if row[3] == '' else row[3],
        'CASES': [],
    }

    # Country cannot be empty
    if params['Country/Region'] == '':
        return None

    # Latitude or longitude must be floats and within valid bounds
    try:
        params['Lat'] = float(params['Lat'])
    except ValueError:
        return None
    try:
        params['Long'] = float(params['Long'])
    except ValueError:
        return None

    if -90 > params['Lat'] or params['Lat'] > 90 or -180 > params['Long'] or params['Long'] > 180:
        return None

    # Cases must be integers > 0
    for cases in row[4:]:
        if not cases.isdigit():
            return None
        params['CASES'].append(cases)

    return params


def parse_post_params(timeseries_name, data_type):
    params = {
        "timeseries_name": None,
        "data_type": None,
    }

    # timeseries_name
    if timeseries_name:
        params["timeseries_name"] = timeseries_name
    else:
        return None

    # data_type
    if data_type:
        if data_type.upper() not in ["DEATHS", "CONFIRMED", "RECOVERED"]:
            return None
        params["data_type"] = TimeSeries.TypeChoice[data_type.upper()]
    else:
        return None

    return params


def parse_get_params(request, timeseries_name, data_type):
    params = {
        "timeseries_name": None,
        "data_type": None,
        "countries": None,
        "regions": None,
        "start_date": None,
        "end_date": None,
        "format": None,
    }

    # timeseries_name
    if timeseries_name:
        params["timeseries_name"] = timeseries_name
    else:
        return None

    # data_type
    if data_type:
        if data_type.upper() not in ["DEATHS", "CONFIRMED", "ACTIVE", "RECOVERED"]:
            return None
        params["data_type"] = TimeSeries.TypeChoice[data_type.upper()]
    else:
        return None

    # countries
    if 'countries' in request.GET:
        params["countries"] = request.GET['countries'].split(",")

    # regions
    if 'regions' in request.GET:
        params["regions"] = request.GET['regions'].split(",")

    # start_date
    if 'start_date' in request.GET:
        try:
            params["start_date"] = datetime.strptime(request.GET['start_date'], '%Y-%m-%d')
        except ValueError:
            return None
    else:
        params["start_date"] = date.min

    # end_date
    if 'end_date' in request.GET:
        try:
            params["end_date"] = datetime.strptime(request.GET['end_date'], '%Y-%m-%d')
        except ValueError:
            return None
    else:
        params["end_date"] = date.max

    # format
    if 'format' in request.GET:
        if request.GET['format'] not in ["csv", "json"]:
            return None
        params["format"] = request.GET['format']
    else:
        params["format"] = 'csv'

    return params


def gen_response_json(timeseries_list, timeseriesdata_list):
    # response = JsonResponse({'foo': 'bar'})

    data = {}

    for index, timeseries in enumerate(timeseries_list):
        row = {
            "Province/State": timeseries.province_state,
            "Country/Region": timeseries.country_region,
            "Lat": timeseries.lat,
            "Long": timeseries.long,
        }

        for timeseriesdata in timeseriesdata_list.filter(timeseries=timeseries).order_by('date'):
            date = timeseriesdata.date.strftime("%m/%d/%y")
            cases = timeseriesdata.cases
            row[date] = cases

        data[index] = row

    return JsonResponse(data)


def gen_response_csv(timeseries_list, timeseriesdata_list):
    # https://docs.djangoproject.com/en/4.0/ref/models/querysets/
    # https://docs.djangoproject.com/en/4.0/howto/outputting-csv/
    response = HttpResponse(content_type='application/csv')

    dates = []
    for date in timeseriesdata_list.values_list('date', flat=True).distinct().order_by('date'):
        dates.append(date.strftime("%m/%d/%y"))

    writer = csv.writer(response)
    writer.writerow(
        ['Province/State', 'Country/Region', 'Lat', 'Long'] + dates)

    for timeseries in timeseries_list:
        prefix = [
            timeseries.province_state,
            timeseries.country_region,
            timeseries.lat,
            timeseries.long,
        ]

        suffix = timeseriesdata_list.filter(timeseries=timeseries).values_list(
            'cases', flat=True).order_by('date')
        writer.writerow(prefix + list(suffix))

    return response
