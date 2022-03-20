from django.db import models
import datetime


class TimeSeries(models.Model):
    class TypeChoice(models.TextChoices):
        DEATHS = 'D'
        CONFIRMED = 'C'
        RECOVERED = 'R'

    data_type = models.CharField(max_length=1, choices=TypeChoice.choices)
    timeseries_name = models.CharField(max_length=1000)

    province_state = models.CharField(max_length=1000)
    country_region = models.CharField(max_length=1000)
    lat = models.FloatField()
    long = models.FloatField()

    def __str__(self):
        return "timeseries_name: {}, data_type: {}, province_state: {}, country_region: {}"\
            .format(self.timeseries_name, self.data_type, self.province_state, self.country_region)


class TimeSeriesData(models.Model):
    timeseries = models.ForeignKey(TimeSeries, on_delete=models.CASCADE)
    date = models.DateField()
    cases = models.IntegerField()

    def __str__(self):
        return "date: {}, cases: {}".format(self.date, self.cases)
