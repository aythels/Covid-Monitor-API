from datetime import datetime

from django.test import TestCase
from .models import TimeSeries, TimeSeriesData
from .views import parse_post_header, gen_response_csv, gen_response_json, parse_post_row, parse_post_params


class TimeSeriesViewsPost(TestCase):
    def test_post_new(self):
        name = "abc"
        type = "deaths"
        body = """Province/State,Country/Region,Lat,Long,1/22/20,1/23/20
                  ,Afghanistan,33.93911,67.709953,0,0
                  Australian Capital Territory,Australia,-35.4735,149.0124,0,0"""

        response = self.client.post('/time_series/' + name + '/' + type, body, content_type='application/csv')
        self.assertEqual(response.status_code, 200)

    def test_post_existing(self):
        # altering deaths value to 999999 and 999998
        name = "abc"
        type = "deaths"
        body = """Province/State,Country/Region,Lat,Long,1/22/20,1/23/20
                  ,Afghanistan,33.93911,67.709953,999999,0
                  Australian Capital Territory,Australia,-35.4735,149.0124,999998,0"""

        response = self.client.post('/time_series/' + name + '/' + type, body, content_type='application/csv')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/time_series/' + name + '/' + type)
        self.assertIs(b"999999" in response.content, True)
        self.assertIs(b"999998" in response.content, True)

    def test_post_invalid_header(self):
        name = "abc"
        type = "deaths"
        body = """Pasdadasfasfasfasrovince/State,Country/Region,Lat,Long,1/22/20,1/23/20
                  ,Afghanistan,33.93911,67.709953,0,0
                  Australian Capital Territory,Australia,-35.4735,149.0124,0,0"""

        response = self.client.post('/time_series/' + name + '/' + type, body, content_type='application/csv')
        self.assertEqual(response.status_code, 400)

    def test_post_invalid_params(self):
        name = "abc"
        type = "deaths"
        body = """Province/State,Country/Region,Lat,Long,1/22/20,1/23/20
                  ,Afghanistan,3asfasfasfasfasfasffasfa3.93911,67.709953,0,0
                  Australian Capital Territory,Australia,-35.4735,149.0124,0,0"""

        response = self.client.post('/time_series/' + name + '/' + type, body, content_type='application/csv')
        self.assertEqual(response.status_code, 400)


class TimeSeriesViewsGet(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Row 1
        params_1 = {
            "timeseries_name": "test1",
            "data_type": TimeSeries.TypeChoice["deaths".upper()],
            "province_state": "BC",
            "country_region": "Canada",
            "lat": 49.2827,
            "long": 123.1207,
        }

        timeseries_1 = TimeSeries.objects.create(**params_1)

        data_1_a = {
            "timeseries": timeseries_1,
            "date": datetime.strptime("1/22/20", "%m/%d/%y"),
            "cases": 100,
        }
        data_1_b = {
            "timeseries": timeseries_1,
            "date": datetime.strptime("1/23/20", "%m/%d/%y"),
            "cases": 100,
        }

        TimeSeriesData.objects.create(**data_1_a)
        TimeSeriesData.objects.create(**data_1_b)

        # Row 2
        params_2 = {
            "timeseries_name": "test1",
            "data_type": TimeSeries.TypeChoice["deaths".upper()],
            "province_state": "ON",
            "country_region": "Canada",
            "lat": 25.1227,
            "long": 122.9807,
        }

        timeseries_2 = TimeSeries.objects.create(**params_2)

        data_2_a = {
            "timeseries": timeseries_2,
            "date": datetime.strptime("1/22/20", "%m/%d/%y"),
            "cases": 200,
        }
        data_2_b = {
            "timeseries": timeseries_2,
            "date": datetime.strptime("1/23/20", "%m/%d/%y"),
            "cases": 200,
        }

        TimeSeriesData.objects.create(**data_2_a)
        TimeSeriesData.objects.create(**data_2_b)

    def test_get_available(self):
        response = self.client.get('/time_series/test1/deaths')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(),
                         b'Province/State,'
                         b'Country/Region,'
                         b'Lat,'
                         b'Long,'
                         b'01/22/20,'
                         b'01/23/20\r\n'
                         b'BC,Canada,49.2827,123.1207,100,100\r\n'
                         b'ON,Canada,25.1227,122.9807,200,200')

    def test_get_available_specific(self):
        response = self.client.get('/time_series/test1/deaths', {
            'start_date': '2020-01-22',
            'end_date': '2020-01-23',
            'countries': ['Canada'],
            'regions': ['BC'],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(),
                         b'Province/State,'
                         b'Country/Region,'
                         b'Lat,'
                         b'Long,'
                         b'01/22/20,'
                         b'01/23/20\r\n'
                         b'BC,Canada,49.2827,123.1207,100,100')

    def test_get_available_json(self):
        response = self.client.get('/time_series/test1/deaths', {'format': 'json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(),
                         b'{'
                         b'"0": {'
                         b'"Province/State": "BC", '
                         b'"Country/Region": "Canada", '
                         b'"Lat": 49.2827, '
                         b'"Long": 123.1207, '
                         b'"01/22/20": 100, '
                         b'"01/23/20": 100}, '
                         b'"1": {'
                         b'"Province/State": "ON", '
                         b'"Country/Region": "Canada", '
                         b'"Lat": 25.1227, '
                         b'"Long": 122.9807, '
                         b'"01/22/20": 200, '
                         b'"01/23/20": 200}'
                         b'}')

    def test_get_unavailable(self):
        response = self.client.get('/time_series/sdgdsgdgsg/deaths')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(), b'Province/State,Country/Region,Lat,Long')

    def test_get_unavailable_json(self):
        response = self.client.get('/time_series/sdgdsgdgsg/deaths', {'format': 'json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(), b'{}')

    def test_get_invalid_params(self):
        response = self.client.get('/time_series/test1/asfasfsafsafasfa')
        self.assertEqual(response.status_code, 400)


class TimeSeriesViewsDelete(TestCase):

    @classmethod
    def setUp(cls):
        params_1 = {
            "timeseries_name": "test1",
            "data_type": TimeSeries.TypeChoice["deaths".upper()],
            "province_state": "BC",
            "country_region": "Canada",
            "lat": 49.2827,
            "long": 123.1207,
        }

        timeseries_1 = TimeSeries.objects.create(**params_1)

        data_1_a = {
            "timeseries": timeseries_1,
            "date": datetime.strptime("1/22/20", "%m/%d/%y"),
            "cases": 100,
        }
        data_1_b = {
            "timeseries": timeseries_1,
            "date": datetime.strptime("1/23/20", "%m/%d/%y"),
            "cases": 100,
        }

        TimeSeriesData.objects.create(**data_1_a)
        TimeSeriesData.objects.create(**data_1_b)

    def test_delete_available(self):
        response = self.client.delete('/time_series/test1')
        self.assertEqual(response.status_code, 200)

    def test_delete_unavailable(self):
        response = self.client.delete('/time_series/sfafasgasgasgasgagsa')
        self.assertEqual(response.status_code, 404)


class TimeSeriesViewsHelpersExport(TestCase):
    def test_export_csv(self):
        params_1 = {
            "timeseries_name": "test1",
            "data_type": TimeSeries.TypeChoice["deaths".upper()],
            "province_state": "BC",
            "country_region": "Canada",
            "lat": 49.2827,
            "long": 123.1207,
        }
        timeseries_1 = TimeSeries.objects.create(**params_1)

        data_1_a = {
            "timeseries": timeseries_1,
            "date": datetime.strptime("1/22/20", "%m/%d/%y"),
            "cases": 100,
        }
        data_1_b = {
            "timeseries": timeseries_1,
            "date": datetime.strptime("1/23/20", "%m/%d/%y"),
            "cases": 100,
        }
        timeseriesdata_1a = TimeSeriesData.objects.create(**data_1_a)
        timeseriesdata_1b = TimeSeriesData.objects.create(**data_1_b)

        response = gen_response_csv([timeseries_1], [timeseriesdata_1a, timeseriesdata_1b])
        self.assertEqual(response.content.strip(),
                         b'Province/State,'
                         b'Country/Region,'
                         b'Lat,'
                         b'Long,'
                         b'01/22/20,'
                         b'01/23/20\r\n'
                         b'BC,'
                         b'Canada,'
                         b'49.2827,'
                         b'123.1207,'
                         b'100,'
                         b'100')

    def test_export_csv_empty(self):
        response = gen_response_csv([], [])
        self.assertEqual(response.content.strip(),
                         b'Province/State,'
                         b'Country/Region,'
                         b'Lat,'
                         b'Long')

    def test_export_json(self):
        params_1 = {
            "timeseries_name": "test1",
            "data_type": TimeSeries.TypeChoice["deaths".upper()],
            "province_state": "BC",
            "country_region": "Canada",
            "lat": 49.2827,
            "long": 123.1207,
        }
        timeseries_1 = TimeSeries.objects.create(**params_1)

        data_1_a = {
            "timeseries": timeseries_1,
            "date": datetime.strptime("1/22/20", "%m/%d/%y"),
            "cases": 100,
        }
        data_1_b = {
            "timeseries": timeseries_1,
            "date": datetime.strptime("1/23/20", "%m/%d/%y"),
            "cases": 100,
        }
        timeseriesdata_1a = TimeSeriesData.objects.create(**data_1_a)
        timeseriesdata_1b = TimeSeriesData.objects.create(**data_1_b)

        response = gen_response_json([timeseries_1], [timeseriesdata_1a, timeseriesdata_1b])
        self.assertEqual(response.content.strip(),
                         b'{'
                         b'"0": {'
                         b'"Province/State": "BC", '
                         b'"Country/Region": "Canada", '
                         b'"Lat": 49.2827, '
                         b'"Long": 123.1207, '
                         b'"01/22/20": 100, '
                         b'"01/23/20": 100}'
                         b'}')

    def test_export_json_empty(self):
        response = gen_response_json([], [])
        self.assertEqual(response.content.strip(), b'{}')


class TimeSeriesViewsPostHelpers(TestCase):

    def test_parse_post_header_valid(self):
        str = 'Province/State,Country/Region,Lat,Long,1/22/20,1/23/20'.split(',')
        self.assertEqual(parse_post_header(str), [
            'Province/State',
            'Country/Region',
            'Lat',
            'Long',
            datetime(2020, 1, 22),
            datetime(2020, 1, 23)])

    def test_parse_post_header_invalid_length(self):
        str = 'Province/State'.split(',')
        self.assertEqual(parse_post_header(str), None)

    def test_parse_post_header_invalid_string(self):
        str = 'asfasfasfafa,Country/Region,Lat,Long,1/22/20,1/23/20'.split(',')
        self.assertEqual(parse_post_header(str), None)

    def test_parse_post_header_invalid_date(self):
        str = 'Province/State,Country/Region,Lat,Long,Jan 22 2020,Jan 23 2020'.split(',')
        self.assertEqual(parse_post_header(str), None)

    def test_parse_post_row_valid(self):
        header = 'Province/State,Country/Region,Lat,Long,1/22/20,1/23/20'.split(',')
        row = 'BC, Canada, 49.2827, 123.1207, 100, 100'.split(',')
        self.assertEqual(parse_post_row(header, row), {
            'Province/State': 'BC',
            'Country/Region': ' Canada',
            'Lat': 49.2827,
            'Long': 123.1207,
            'CASES': [100, 100]})

    def test_parse_post_row_invalid_length(self):
        header = 'Province/State,Country/Region,Lat,Long,1/22/20,1/23/20'.split(',')
        row = 'BC, Canada'.split(',')
        self.assertEqual(parse_post_row(header, row), None)

    def test_parse_post_row_invalid_country(self):
        header = 'Province/State,Country/Region,Lat,Long,1/22/20,1/23/20'.split(',')
        row = 'BC,, 49.2827, 123.1207, 100, 100'.split(',')
        self.assertEqual(parse_post_row(header, row), None)

    def test_parse_post_row_invalid_latlong(self):
        header = 'Province/State,Country/Region,Lat,Long,1/22/20,1/23/20'.split(',')
        row = 'BC, Canada, 9999, 9999, 100, 100'.split(',')
        self.assertEqual(parse_post_row(header, row), None)

    def test_parse_post_row_invalid_cases(self):
        header = 'Province/State,Country/Region,Lat,Long,1/22/20,1/23/20'.split(',')
        row = 'BC, Canada, 49.2827, 123.1207, asfasga, -30'.split(',')
        self.assertEqual(parse_post_row(header, row), None)

    def test_parse_post_params_valid(self):
        timeseries_name = 'abc'
        data_type = 'deaths'
        self.assertEqual(parse_post_params(timeseries_name, data_type), {
            "timeseries_name": timeseries_name,
            "data_type": TimeSeries.TypeChoice[data_type.upper()]
        })

    def test_parse_post_params_invalid(self):
        # invalid timeseries_name
        timeseries_name = None
        data_type = 'asfasfsafafsafafafs'
        self.assertEqual(parse_post_params(timeseries_name, data_type), None)

        timeseries_name = ''
        data_type = 'asfasfsafafsafafafs'
        self.assertEqual(parse_post_params(timeseries_name, data_type), None)

        # invalid data_type
        timeseries_name = 'abc'
        data_type = 'asfasfsafafsafafafs'
        self.assertEqual(parse_post_params(timeseries_name, data_type), None)
