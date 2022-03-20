from django.test import TestCase
from django.test.utils import setup_test_environment
from django.test import Client
from .models import DailyReports
from datetime import datetime, date, time, timezone

# Create your tests here.
class DailyReportsViewsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
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

    def test_get_daily_reports_simple_example(self):
        response = self.client.get('/daily_reports/test1')
        self.assertEqual(response.status_code, 200)
    
    def test_post_daily_reports_simple_example(self):
        body = """FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key,Incidence_Rate,Case-Fatality_Ratio
                45001,Abbeville,South Carolina,US,2020-06-06 02:33:00,34.22333378,-82.46170658,47,0,0,47,"Abbeville, South Carolina, US",191.625555510254,0
                22001,Acadia,Louisiana,US,2020-06-06 02:33:00,30.2950649,-92.41419698,467,26,0,441,"Acadia, Louisiana, US",752.6795068095737,5.56745182012848"""
        
        response = self.client.post('/daily_reports/test2', body, content_type='application/csv')
        self.assertEqual(response.status_code, 200)
    
    def test_delete_daily_reports_simple_example(self):
        response = self.client.delete('/daily_reports/test1')
        self.assertEqual(response.status_code, 200)