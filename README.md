# CovidAPI

## Table of contents

- [Introduction](#introduction)
- [Routes](#routes)
- [Examples](#examples)
- [Local Setup](#local-setup)
- [Program Design](#program-design)
- [Pair Programming](#pair-programming)
- [Creators](#creators) 


## Introduction
CovidAPI provides convenient access to retrieving, storing, and deleting covid related data in csv format. 

API is accessible via [​​https://covid-api-group24.herokuapp.com](https://covid-api-group24.herokuapp.com). 

**Disclaimer**: We are using heroku’s free tier that only provides 10,000 rows in our postgres database. 

## Routes
| Method   | Route                                                       | Status Code                                                                               | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|----------|-------------------------------------------------------------|-------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `POST`   | <br><pre>`/time_series/{timeseries_name}/{data_type}`</pre> | `200 Upload successful`<br><br>`400 Malformed request`<br><br>`422 Invalid file contents` | Create or update a Time Series<br><br>timeseries_name*: `string`<br>data_type*: `'deaths' \| 'confirmed' \| 'recovered'`<br><br>Body must have a well formatted csv which means header of csv content should be `Province/State, Country/Region, Lat, Long, ...dates`<br><br>Each date must be in the format `DD/MM/YY`. Columns under `Country/Region` cannot be empty.<br><br>Content-type should be `application/csv`                                                                   |
| `GET`    | <br><pre>`/time_series/{timeseries_name}/{data_type}`</pre> | `200 Successful operation`<br><br>`400 Malformed Request`                                 | Retrieve a Time Series<br><br>timeseries_name*: `string`<br>data_type*: `'deaths' \| 'confirmed' \| 'recovered' \| 'active'`<br>start_date: `YYYY-MM-DD`<br>end_date: `YYYY-MM-DD`<br>countries: `string[]`<br>regions: `string[]`<br>format: `'csv' \| 'json'`                                                                                                                                                                                                                            |
| `DELETE` | <br><pre>`/time_series/{timeseries_name}`</pre>             | `200 Successfully deleted`<br><br>`404 Timeseries not found`                              | Delete a Time Series<br><br>timeseries_name*: `string`                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `POST`   | <br><pre>`/daily_reports/{dailyreport_name}`</pre>          | `200 Upload successful`<br><br>`400 Malformed request`<br><br>`422 Invalid file contents` | Create or update a Daily Report<br><br>dailyreport_name*: `string`<br><br>Body must have a well formatted csv which means header of csv content should be `FIPS, Admin2, Province_State, Country_Region, Last_Update, Lat, Long_, Confirmed, Deaths, Recovered, Active, Combined_Key, Incidence_Rate, Case-Fatality_Ratio`.<br><br>Columns under `Country_Region`, `Last_Update`, `Incidence_Rate`, `Case-Fatality_Ratio` cannot be empty.<br><br>Content-type should be `application/csv` |
| `GET`    | <br><pre>`/daily_reports/{dailyreport_name}`</pre>          | `200 Successful operation`<br><br>`400 Malformed Request`                                 | Retrieve a Daily Report<br><br>dailyreport_name*: `string`<br>start_date: `YYYY-MM-DD`<br>end_date: `YYYY-MM-DD`<br>countries: `[string]`<br>regions: `[string]`<br>format: `'csv' \| 'json'`<br>combined_key: `'string'`<br>data_type: `'deaths' \| 'confirmed' \| 'recovered' \| 'active'`                                                                                                                                                                                               |
| `DELETE` | <br><pre>`/daily_reports/{dailyreport_name}`</pre>          | `200 Successfully deleted`<br><br>`404 Daily Reports not found`                           | Delete a Daily Report<br><br>dailyreport_name*: `string`                                                                                                                                                                                                                                                                                                                                                                                                                                   |

## Examples
Time Series `POST`
```bash
curl --location --request POST 'https://covid-api-group24.herokuapp.com/time_series/timeseries0000/confirmed' \
--header 'Content-Type: application/csv' \
--data-raw 'Province/State,Country/Region,Lat,Long,1/22/20,1/23/20,1/24/20
,Afghanistan,33.93911,67.709953,0,0,0
,Albania,41.1533,20.1683,1,3,5 
Australian Capital Territory,Australia,-35.4735,149.0124,0,0,1 
New South Wales,Australia,-33.8688,151.2093,2,4,6 '
```

Time Series `GET`
```bash
curl -X 'GET' \
'https://covid-api-group24.herokuapp.com/time_series/timeseries0000/confirmed?start_date=2020-01-22&end_date=2020-01-23&countries=Afghanistan&format=csv' \
-H 'accept: application/csv'
```

Time Series `DELETE`
```bash
curl -X 'DELETE' \
'https://covid-api-group24.herokuapp.com/time_series/timeseries0000' \
-H 'accept: application/json'
```

Daily Reports `POST`
```bash
curl --location --request POST 'https://covid-api-group24.herokuapp.com/daily_reports/dailyreport0000' \
--header 'Content-Type: application/csv' \
--header 'accept: application/json' \
--data-raw 'FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key,Incidence_Rate,Case-Fatality_Ratio
45001,Abbeville,South Carolina,US,2020-06-06 02:33:00,34.22333378,-82.46170658,47,0,0,47,"Abbeville, South Carolina, US",191.625555510254,0.0
22001,Acadia,Louisiana,US,2020-06-06 02:33:00,30.2950649,-92.41419698,467,26,0,441,"Acadia, Louisiana, US",752.6795068095737,5.56745182012848'
```
Daily Reports `GET`
```bash
curl -X 'GET' \
'https://covid-api-group24.herokuapp.com/daily_reports/dailyreport0000?start_date=2020-06-06&end_date=2020-06-07&countries=US&regions=South+Carolina&format=json' \
-H 'accept: application/csv'
```
Daily Reports `DELETE`
```bash
curl -X 'DELETE' \
'https://covid-api-group24.herokuapp.com/daily_reports/dailyreport0000' \
-H 'accept: application/json'
```

## Local Setup
1. Install from requirements.txt in root directory
`$ pip install -r requirements.txt `
2. Set up a PostgreSQL database locally according to the database configuration found in covidAPI/settings.py. 
3. Create Postgres tables  from covidAPI folder
```bash
$ python manage.py makemigrations time_series
$ python manage.py sqlmigrate time_series 0001
$ python manage.py migrate time_series
$ python manage.py makemigrations daily_reports
$ python manage.py sqlmigrate daily_reports 0001
$ python manage.py migrate daily_reports
```
4. Running server from root directory
`$ python manage.py runserver`
5. Access server through [http://127.0.0.1:8000/](http://127.0.0.1:8000/)


In order to run tests for projects
```bash
coverage run --source='.' manage.py test 
coverage report
```

<img width="599" alt="Screen Shot 2022-03-21 at 4 31 38 PM" src="https://user-images.githubusercontent.com/43018123/159358775-341a7a5c-d241-49ab-ad4a-162e90253af9.png">


## Program Design
### Tech Stack
Our API is built with Django for our web server, PostgreSQL for persistent storage, Gunicorn for Server Gateway Interface, Heroku for deployment, Github Actions for CI/CD, pytest-cov for test coverage.

### Project Structure
We utilized the default project structure django provides. Since time_series and daily_reports are not connected, we created two different ‘apps’ under our django project for each of them. Within an app there contains files, admin.py (file related to the admin configuration of Django), apps.py (exposes the app to whole django project), models.py (an ORM to define our model classes), tests.py (tests for our app; can contain both e2e and unit tests), urls.py(define a regex to match path to corresponding functions), views.py (contains the logic of process request and sending response). Within the main folder for django API(covidAPI in our case). settings.py contains important settings such as config necessary for deployment and connection to postgres database, urls.py contains the base route we are exposing on our server. 

### Data storage
For timeseries, we stored all metadata (Province,Country,Lat,Long) in one row of our database. The dates with counts for each date are then stored separately in another table with a foreign key that references the corresponding province, country. We designed our relationship this way because there is no way of knowing how many dates the user will send to us in the POST request, we want to accommodate any number of dates the user provides. An alternative consideration is to not use a RDMS and use a document database like MongoDB and we could bypass the need to have two data models/ tables.
<br/>
<br/>
<img width="813" alt="Screen Shot 2022-03-21 at 4 32 50 PM" src="https://user-images.githubusercontent.com/43018123/159358984-becc9bd5-e76d-4ad1-857a-9aad0aa5537e.png">

For daily reports, we simply stored all the information the user sends in a POST into one table. This is because there is only one date in each row of the csv, so there’s no need to accommodate for an arbitrary number of dates. The benefit of storing in one table is that, in the future, if we wanted to query for countries across different daily reports the user sends, we can easily query by country_name instead of having to do complex joins with a secondary table to get all our necessary data.<br/>
<br/>
<img width="1111" alt="Screen Shot 2022-03-21 at 4 33 52 PM" src="https://user-images.githubusercontent.com/43018123/159359130-66458a8b-80e2-4f71-bccc-689efc9f8090.png">

### CI/ CD 
We use Github Actions for our CI/ CD. When a user creates a PR, our CI pipeline runs the unit tests and e2e tests, it will warn the user if any of the tests fail. Once a PR is ready to be merged into main. The main will re rerun the CI pipeline as a double check and run the CD pipeline which deploys our application to Heroku.
<br/>
<br/>
![159359336-0909c7e4-555d-45c4-b62d-0914293ff4c7](https://user-images.githubusercontent.com/10892740/159366209-d63b8d99-8045-45fd-bf5e-1f96de9a46d0.png)

## Creators

- [Elson Liang](https://github.com/aythels)
- [Tom Kan](https://github.com/TomKan0909)
