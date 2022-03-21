from datetime import datetime

from django.test import TestCase
from .models import TimeSeries, TimeSeriesData
from .views import parse_post_header


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


class TimeSeriesViewsHelper(TestCase):

    def test_parse_post_header_valid(self):
        str = 'Province/State,Country/Region,Lat,Long,1/22/20,1/23/20'.split(',')
        self.assertEqual(parse_post_header(str), [
            'Province/State',
            'Country/Region',
            'Lat',
            'Long',
            datetime(2020, 1, 22),
            datetime(2020, 1, 23)])

    def test_parse_post_header_invalid(self):
        str = 'Provinasfasfasfce/State,Country/Region,Lat,Long,1/22/20,1/23/20'.split(',')
        self.assertEqual(parse_post_header(str), None)
