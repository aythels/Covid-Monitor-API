from io import StringIO
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import csv

from time_series.models import TimeSeries, TimeSeriesData
from datetime import date, datetime

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


def _post_body_check(reader):
    cols_count = len(reader.fieldnames)
    if cols_count < 5:
        return HttpResponse('Malformed Content', status=400)

    province_state_key, country_region_key, latitude_key, longitude_key, \
    *dates = reader.fieldnames

    if province_state_key != CONSTS['province_state_key'] or \
            country_region_key != CONSTS['country_region_key'] or \
            latitude_key != CONSTS['latitude_key'] or \
            longitude_key != CONSTS['longitude_key']:
        return HttpResponse('Malformed Content', status=400)

    for date in dates:
        try:
            date = datetime.strptime(date, "%m/%d/%y")
        except:
            return HttpResponse('Invalid File Contents', status=422)

    for row in reader:
        if len(row) != cols_count:
            return HttpResponse('Malformed Content', status=400)

        province_state, country_region, latitude, longitude = row[province_state_key], row[
            country_region_key], row[latitude_key], row[longitude_key]

        latitude = 0.0 if latitude == '' else latitude
        longitude = 0.0 if longitude == '' else longitude

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except:
            return HttpResponse('Invalid File Contents', status=422)

        if country_region == '':  # Country cannot be empty
            return HttpResponse('Invalid File Contents', status=422)
        if -90 > latitude or latitude > 90 or -180 > longitude or longitude > 180:
            return HttpResponse('Invalid File Contents', status=422)

        for date in dates:
            cases = row[date]
            try:
                cases = int(cases)
            except:
                return HttpResponse('Invalid File Contents', status=422)
            if cases < 0:
                return HttpResponse('Invalid File Contents', status=422)


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
        params["data_type"] = data_type.upper()
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
        if params["format"] not in ["csv", "json"]:
            return None
    else:
        params["format"] = 'csv'

    return params


@csrf_exempt
def timeseries_post(request, timeseries_name, data_type):
    # TODO FIX DATA TYPE

    try:
        data_type = TimeSeries.TypeChoice[data_type.upper()]
    except:
        return HttpResponse('Malformed Content', status=400)

    body = request.body.decode('utf-8')
    # Writing CSV
    # reader = csv.reader(body.split('\n'), delimiter=',')
    # header_dates = next(reader, None)[4:]
    # TODO: change this to such that the readers are uniformed; currently uses a DictReader and normal reader
    f_body = StringIO(body)
    reader = csv.DictReader(f_body, delimiter=',')
    res = _post_body_check(reader)
    if res:
        return res

    reader = csv.reader(body.split('\n'), delimiter=',')
    header_dates = next(reader, None)[4:]

    for row in reader:
        # Writing TimeSeries
        data = {
            "timeseries_name": timeseries_name,
            "data_type": data_type,
            "province_state": row[0],
            "country_region": row[1],
            "lat": row[2] if row[2] != '' else 0.0,
            "long": row[3] if row[3] != '' else 0.0,
        }

        # Search for TimeSeries and create it if it does not exist
        # TODO: Allow overwriting of province_state, country_region and lat and long fields?
        timeseries_entry = TimeSeries.objects.filter(data_type=data["data_type"],
                                                     timeseries_name=data["timeseries_name"],
                                                     province_state=data["province_state"],
                                                     country_region=data["country_region"]).first()
        if not timeseries_entry:
            timeseries_entry = TimeSeries(**data)
            timeseries_entry.save()

        to_create = []
        to_update = []

        timeseries_data_entry_all = TimeSeriesData.objects.filter(
            timeseries=timeseries_entry
        )

        # Writing TimeSeriesData
        for index, value in enumerate(row[4:]):
            data = {
                "timeseries": timeseries_entry,
                "date": convert_date(header_dates[index]),
                "cases": value,
            }

            # Search for TimeSeriesData by timeseries and date and create it if it does not exist
            timeseries_data_entry = timeseries_data_entry_all.filter(
                date=data["date"]).first()
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


@csrf_exempt
def timeseries_get(request, timeseries_name, data_type):
    # Getting and verifying parameters
    params = parse_get_params(request, timeseries_name, data_type)
    if not params:
        return HttpResponse('Malformed request', status=400)

    # Creating query
    query = {
        "timeseries_name": params["timeseries_name"],
    }

    if params["data_type"] != "ACTIVE":
        query["data_type"] = TimeSeries.TypeChoice[params["data_type"]]
    if params["countries"]:
        query["country_region__in"] = params["countries"]
    if params["regions"]:
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


@csrf_exempt
def timeseries_delete(timeseries_name):
    # Getting associated data entries
    timeseries_entries = TimeSeries.objects.filter(
        timeseries_name=timeseries_name)

    # Deleting entries
    if timeseries_entries:
        timeseries_entries.delete()
        return HttpResponse('Successfully deleted', status=200)

    return HttpResponse('Timeseries not found', status=404)


# **************************************************************************************************** HELPER FUNCTIONS

def gen_response_json(timeseries_list, timeseriesdata_list):
    # data = serializers.serialize("json", timeseries_list)
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


def convert_date(date):
    # 1/23/20 to 2020-01-23

    date_split = date.split('/')

    month = date_split[0].zfill(2)
    day = date_split[1].zfill(2)
    year = date_split[2]

    new_date = month + "-" + day + "-" + year

    return datetime.strptime(new_date, '%m-%d-%y')
