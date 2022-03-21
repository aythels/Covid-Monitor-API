from django.test import TestCase
from django.test.utils import setup_test_environment
from django.test import Client
from .models import DailyReports
from datetime import datetime


class DailyReportsViewsPost(TestCase):

    def test_post_new(self):
        body = """FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key,Incidence_Rate,Case-Fatality_Ratio
                45001,Abbeville,South Carolina,US,2020-06-06 02:33:00,34.22333378,-82.46170658,47,0,0,47,"Abbeville, South Carolina, US",191.625555510254,0
                22001,Acadia,Louisiana,US,2020-06-06 02:33:00,30.2950649,-92.41419698,467,26,0,441,"Acadia, Louisiana, US",752.6795068095737,5.56745182012848"""

        response = self.client.post('/daily_reports/test1', body, content_type='application/csv')
        self.assertEqual(response.status_code, 200)

    def test_post_existing(self):
        # altering deaths value to 999999 and 999998
        body = """FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key,Incidence_Rate,Case-Fatality_Ratio
                45001,Abbeville,South Carolina,US,2020-06-06 02:33:00,34.22333378,-82.46170658,47,999999,0,47,"Abbeville, South Carolina, US",191.625555510254,0
                22001,Acadia,Louisiana,US,2020-06-06 02:33:00,30.2950649,-92.41419698,467,999998,0,441,"Acadia, Louisiana, US",752.6795068095737,5.56745182012848"""

        response = self.client.post('/daily_reports/test1', body, content_type='application/csv')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/daily_reports/test1')
        self.assertIs(b"999999" in response.content, True)
        self.assertIs(b"999998" in response.content, True)

    def test_post_invalid_header(self):
        body = """qwfqwfwfafsfafasfasf,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key,Incidence_Rate,Case-Fatality_Ratio
                45001,Abbeville,South Carolina,US,2020-06-06 02:33:00,34.22333378,-82.46170658,47,999999,0,47,"Abbeville, South Carolina, US",191.625555510254,0
                22001,Acadia,Louisiana,US,2020-06-06 02:33:00,30.2950649,-92.41419698,467,999998,0,441,"Acadia, Louisiana, US",752.6795068095737,5.56745182012848"""

        response = self.client.post('/daily_reports/test1', body, content_type='application/csv')
        self.assertEqual(response.status_code, 400)

    def test_post_invalid_params(self):
        body = """FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key,Incidence_Rate,Case-Fatality_Ratio
                afasfasfasfas,Abbeville,South Carolina,US,2020-06-06 02:33:00,34.22333378,-82.46170658,47,999999,0,47,"Abbeville, South Carolina, US",191.625555510254,0
                22001,Acadia,Louisiana,US,2020-06-06 02:33:00,30.2950649,-92.41419698,467,999998,0,441,"Acadia, Louisiana, US",752.6795068095737,5.56745182012848"""

        response = self.client.post('/daily_reports/test1', body, content_type='application/csv')
        self.assertEqual(response.status_code, 400)


class DailyReportsViewsGet(TestCase):

    @classmethod
    def setUpTestData(cls):
        params = {
            "dailyreport_name": "test1",
            "fips": 1,
            "admin2": "admin1",
            "province_state": "BC",
            "country_region": "Canada",
            "last_update": datetime(2021, 11, 21, 16, 30),
            "lat": 12.02,
            "long": 13.04,
            "confirmed": 500,
            "deaths": 10,
            "recovered": 300,
            "active": 190,
            "combined_key": "BC, Canada",
            "incidence_rate": 4.324,
            "case_fatality_ratio": 5.237,
        }
        params2 = {
            "dailyreport_name": "test1",
            "fips": 2,
            "admin2": "admin2",
            "province_state": "ON",
            "country_region": "Toronto",
            "last_update": datetime(2022, 10, 25, 13, 32),
            "lat": 42.02,
            "long": 23.04,
            "confirmed": 700,
            "deaths": 120,
            "recovered": 80,
            "active": 500,
            "combined_key": "ON, Canada",
            "incidence_rate": 7.323,
            "case_fatality_ratio": 2.254,
        }

        DailyReports.objects.create(**params)
        DailyReports.objects.create(**params2)

    def test_get_available(self):
        response = self.client.get('/daily_reports/test1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(),
                         b'Province_State,'
                         b'Country_Region,'
                         b'Last_Update,Active,'
                         b'Confirmed,Deaths,'
                         b'Recovered,'
                         b'Combined_Key,'
                         b'Incidence_Rate,'
                         b'Case-Fatality_Ratio\r\n'
                         b'BC,Canada,2021-11-21 21:30:00+00:00,190,500,10,300,"BC, Canada",4.324,5.237\r\n'
                         b'ON,Toronto,2022-10-25 18:32:00+00:00,500,700,120,80,"ON, Canada",7.323,2.254')

    def test_get_available_json(self):
        response = self.client.get('/daily_reports/test1', {'format': 'json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(),
                         b'{"0": {'
                         b'"Province_State": "BC", '
                         b'"Country_Region": "Canada", '
                         b'"Last_Update": "2021-11-21 21:30:00", '
                         b'"Combined_Key": "BC, Canada", '
                         b'"Incidence_Rate": 4.324, '
                         b'"Case-Fatality_Ratio": 5.237, '
                         b'"Active": 190, '
                         b'"Confirmed": 500, '
                         b'"Deaths": 10, '
                         b'"Recovered": 300}, '
                         b'"1": {'
                         b'"Province_State": "ON", '
                         b'"Country_Region": "Toronto", '
                         b'"Last_Update": "2022-10-25 18:32:00", '
                         b'"Combined_Key": "ON, Canada", '
                         b'"Incidence_Rate": 7.323, '
                         b'"Case-Fatality_Ratio": 2.254, '
                         b'"Active": 500, '
                         b'"Confirmed": 700, '
                         b'"Deaths": 120, '
                         b'"Recovered": 80}}')

    def test_get_available_specific(self):
        response = self.client.get('/daily_reports/test1', {
            'start_date': '2021-11-21',
            'end_date': '2021-11-21',
            'countries': ['Canada'],
            'regions': ['BC'],
            'combined_key': 'BC, Canada',
            'data_type': 'deaths',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(),
                         b'Province_State,'
                         b'Country_Region,'
                         b'Last_Update,'
                         b'Deaths,'
                         b'Combined_Key,'
                         b'Incidence_Rate,'
                         b'Case-Fatality_Ratio\r\n'
                         b'BC,Canada,2021-11-21 21:30:00+00:00,10,"BC, Canada",4.324,5.237')

    def test_get_unavailable(self):
        response = self.client.get('/daily_reports/sfafasgasgasgasgagsa')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(),
                         b'Province_State,'
                         b'Country_Region,'
                         b'Last_Update,'
                         b'Active,'
                         b'Confirmed,'
                         b'Deaths,'
                         b'Recovered,'
                         b'Combined_Key,'
                         b'Incidence_Rate,'
                         b'Case-Fatality_Ratio')

    def test_get_invalid_params(self):
        response = self.client.get('/daily_reports/test1', {'start_date': 'asfasfasfasfasfas'})
        self.assertEqual(response.status_code, 400)


class DailyReportsViewsDelete(TestCase):

    @classmethod
    def setUp(cls):
        params = {
            "dailyreport_name": "test1",
            "fips": 1,
            "admin2": "admin1",
            "province_state": "BC",
            "country_region": "Canada",
            "last_update": datetime(2021, 11, 21, 16, 30),
            "lat": 12.02,
            "long": 13.04,
            "confirmed": 500,
            "deaths": 10,
            "recovered": 300,
            "active": 190,
            "combined_key": "BC, Canada",
            "incidence_rate": 4.324,
            "case_fatality_ratio": 5.237,
        }
        DailyReports.objects.create(**params)

    def test_delete_available(self):
        response = self.client.delete('/daily_reports/test1')
        self.assertEqual(response.status_code, 200)

    def test_delete_unavailable(self):
        response = self.client.delete('/daily_reports/sfafasgasgasgasgagsa')
        self.assertEqual(response.status_code, 404)
