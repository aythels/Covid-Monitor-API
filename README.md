# 24-tomkan0909-aythels

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

API is accessible via this link [​​https://covid-api-group24.herokuapp.com](https://covid-api-group24.herokuapp.com). 

**Disclaimer**: We are using heroku’s free tier that only provides 10,000 rows in our postgres database. 

## Routes
| Method   | Routes                                       | Status Codes  | Description                                                                                                                                                                                                                                                                                              |
|----------|----------------------------------------------|---------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `POST`   | `/time_series/{timeseries_name}/{data_type}` | `200 Upload successful` <br/> `400 Malformed request` <br/> `422 Invalid file contents` | Upload or update a timeseries. `data_type = deaths \|confirmed \| recovered`. Body must have a well formmated csv which means header of csv content should be `Province/State,Country/Region,Lat,Long, ...dates` where each date should have format `DD/MM/YY`. Columns under `Country/Region` cannot be empty. Content-type should be `application/csv` |
| `GET`    | `/time_series/{timeseries_name}/{data_type}` | `200 Successful operation`<br/>`400 Malformed Request`                       | Retrieve a timeseries. `data_type = deaths \| confirmed \| recovered \| active`. Optional params `start_date: YY/MM/DD`, `end_date: YY/MM/DD`, `countries: list of strings`, `regions: list of strings`, `format = csv \| json`                                                                          |
| `DELETE` | `/time_series/{timeseries_name}`             | `200 Successfully deleted` <br/> `404 Timeseries not found`                    | Delete a timeseries                                                                                                                                                                                                                                                                                      |
| `POST`   | `/daily_reports/{dailyreport_name}`          | `200 Upload successful` <br/> `400 Malformed request` <br/>`422 Invalid file contents` | Upload or update a dailyreport. Body must have a well formated csv which means header of csv content should be `FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key,Incidence_Rate,Case-Fatality_Ratio`. Columns under `Country_Region, Last_Update,Incidence_Rate, Case-Fatality_Ratio` cannot be empty Content-type should be `application/csv`                                      |
| `GET`    | `/daily_reports/{dailyreport_name}`          | `200 Successful operation` <br/> `400 Malformed Request`                       | Retrieve a dailyreport. Optional params  `start_date: YY/MM/DD` ,  `end_date: YY/MM/DD` ,  `countries: list of strings` ,  `regions: list of strings` ,  `format = csv \| json`, `combined_key = string`, `data_type = deaths \| confirmed \| recovered \| active`,                                      |
| `DELETE` | `/daily_reports/{dailyreport_name}`          | `200 Successfully deleted` <br/> `404 Timeseries not found`                    | Delete a dailyreport                                                                                                                                                                                                                                                                                     |

## Examples
Time Series `POST`
```bash
    curl -X 'POST' \
    'https://covid-api-group24.herokuapp.com/time_series/timeseries000/confirmed' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/csv' \
    -d 'Province/State,Country/Region,Lat,Long,1/22/20,1/23/20,1/24/20
    ,Afghanistan,33.93911,67.709953,1,2,3
    ,Albania,41.1533,20.1683,1,3,5
    Australian Capital Territory,Australia,-35.4735,149.0124,0,0,1
    New South Wales,Australia,-33.8688,151.2093,2,4,6
    '
```

Time Series `GET`
```bash
    curl -X 'GET' \
  'https://covid-api-group24.herokuapp.com/time_series/timeseries000/confirmed?start_date=20%2F1%2F22&end_date=20%2F1%2F24&countries=Afghanistan&format=csv' \
  -H 'accept: application/csv'
```

Time Series `DELETE`
```bash
    curl -X 'DELETE' \
  'https://covid-api-group24.herokuapp.com/time_series/timeseries000' \
  -H 'accept: application/json'

```

Daily Reports `POST`
```bash
    curl -X 'POST' \
    'https://covid-api-group24.herokuapp.com/daily_reports/dailyreport000' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/csv' \
    -d 'FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key,Incidence_Rate,Case-Fatality_Ratio
    45001,Abbeville,South Carolina,US,2020-06-06 02:33:00,34.22333378,-82.46170658,47,0,0,47,"Abbeville, South Carolina, US",191.625555510254,0.0
    22001,Acadia,Louisiana,US,2020-06-06 02:33:00,30.2950649,-92.41419698,467,26,0,441,"Acadia, Louisiana, US",752.6795068095737,5.56745182012848
    '
```
Daily Reports `GET`
```bash
    curl -X 'GET' \
    'https://covid-api-group24.herokuapp.com/daily_reports/dailyreport000?start_date=20%2F6%2F6&end_date=20%2F6%2F7&countries=US&regions=South%20Carolina,Louisiana&data_type=active&format=csv' \
    -H 'accept: application/csv'
```
Daily Reports `DELETE`
```bash
    curl -X 'DELETE' \
    'https://covid-api-group24.herokuapp.com/daily_reports/dailyreports000' \
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

<img width="813" alt="Screen Shot 2022-03-21 at 4 32 50 PM" src="https://user-images.githubusercontent.com/43018123/159358984-becc9bd5-e76d-4ad1-857a-9aad0aa5537e.png">

For daily reports, we simply stored all the information the user sends in a POST into one table. This is because there is only one date in each row of the csv, so there’s no need to accommodate for an arbitrary number of dates. The benefit of storing in one table is that, in the future, if we wanted to query for countries across different daily reports the user sends, we can easily query by country_name instead of having to do complex joins with a secondary table to get all our necessary data.

<img width="1111" alt="Screen Shot 2022-03-21 at 4 33 52 PM" src="https://user-images.githubusercontent.com/43018123/159359130-66458a8b-80e2-4f71-bccc-689efc9f8090.png">

### CI/ CD 
We use Github Actions for our CI/ CD. When a user creates a PR, our CI pipeline runs the unit tests and e2e tests, it will warn the user if any of the tests fail. Once a PR is ready to be merged into main. The main will re rerun the CI pipeline as a double check and run the CD pipeline which deploys our application to Heroku.

<img width="964" alt="Screen Shot 2022-03-21 at 4 35 09 PM" src="https://user-images.githubusercontent.com/43018123/159359336-0909c7e4-555d-45c4-b62d-0914293ff4c7.png">

## Pair Programming
### First Session
Our first pair programming sessions consisted of initializing a django project. Neither of us had any experience with setting up a Django application and connecting it to a database. We used pair programming to help each other troubleshoot and accelerate that process.

Since we used a custom database psql instead of sqlite db provided,.One challenge we encountered was connecting it to the Django application with the appropriate settings. This process was difficult because there was no official tutorial on Django on how to accomplish this according to our specifications. One participant got a head start on the process and was able to quickly onboard the other participant through pair programming. From there, we alternated roles as watcher and driver constantly to flesh out the remaining migration issues together. 

Since we were both new to Django when we both started, this peer programming session helped us learn about Django together where we could ask each other questions and clear up any assumptions we had about it. It helped sped up our on ramp process as sometimes one of us will have already discovered the answer to a question and help the other clarify their questions.

### Second Session
In contrast to the first session, pair programming was used near the end of the project in creating unit tests with a focus on improving code quality.

Discussing edge cases in the unit tests during the pair programming sessions allowed us to reflect on the implementation of the API routes. This was crucial in ensuring that we both understood the project prompt correctly since we worked on different parts of the API. In writing the unit tests, we encountered several bugs such as forgetting to type check an invalid parameter or formatting the export csv incorrectly. The root of the problem was identified quickly because we were able to bounce suggestions off each other in real time during the pair programming session.

### Positives
Can be used to introduce the project to the driver in the onboarding process. The watcher who is teaching can help troubleshoot minor but obscure bugs and difficulties that may arise during setup that would otherwise take a long time to resolve due to lack of experience with the tech stack.

Programmers have different syntax styles and come from different backgrounds. Peer programming thus enables idea and knowledge sharing which results in the innovation of new approaches and solutions to challenges when evaluating code architecture.

Can accelerate the creation of clean and efficient code. The driver is responsible for writing code while the watcher can act as an assistant to help the driver unblock any difficulties the moment they arise.

### Negatives
It is better for the watcher to be the one teaching instead of the driver. It is very easy to be confused in the learning process as the watcher since seeing is not as memorable as doing. 

The watcher may find the experience annoying and slow, or get confused due to intermissions such as the driver alt-tabbing to search something up in the process of experimentation and discovery.

Our conclusion regarding pair programming is that minimizing intermissions and confusion makes it more efficient. To achieve this, both participants need to meet a certain level of competency, turning the process from one of learning and discovery into one of refinement and improvement. 


## Creators

- [Elson Liang](https://github.com/aythels)
- [Tom Kan](https://github.com/TomKan0909)
