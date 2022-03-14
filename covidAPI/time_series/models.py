from django.db import models


class TimeSeries(models.Model):
    TYPECHOICE = [('D', 'Deaths'), ('C', 'Confirmed'),
                  ('A', 'Active'), ('R', 'Recovered')]
    type = models.CharField(max_length=1, choices=TYPECHOICE)
    timeseries_name = models.CharField(max_length=1000)
    province_state = models.CharField(max_length=1000)
    country_region = models.CharField(max_length=1000)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return "Timeseries: {}, province/state: {}, country/region: {}, latitude: {}, longitude: {}, type: {}".format(self.timeseries_name,
                                                                                                                      self.province_state, self.country_region, self.latitude, self.longitude, self.type)


class TimeSeriesData(models.Model):
    """
    Represents a single Buoy datapoint
    """
    timeseries = models.ForeignKey(TimeSeries, on_delete=models.CASCADE)
    date = models.DateTimeField()
    cases = models.IntegerField()

    def __str__(self):
        return "Date: {}, cases: {}".format(self.date, self.cases)
