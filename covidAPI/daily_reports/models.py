from django.db import models

# Create your models here.
# FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,
# Deaths,Recovered,Active,Combined_Key,Incident_Rate,Case_Fatality_Ratio


class DailyReports(models.Model):
    fips = models.IntegerField()
    admin2 = models.CharField(max_length=1000)
    province_state = models.CharField(max_length=1000)
    country_region = models.CharField(max_length=1000)
    last_update = models.DateTimeField()
    lat = models.FloatField()
    long = models.FloatField()
    confirmed = models.IntegerField()
    deaths = models.IntegerField()
    recovered = models.IntegerField()
    active = models.IntegerField()
    combined_key = models.CharField(max_length=1000)
    incident_rate = models.FloatField()
    case_fatality_ratio = models.FloatField()
