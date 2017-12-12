# -*- coding: utf-8 -*-
import argparse
from apiclient.discovery import build
import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools
import datetime
import requests
from sqlalchemy import create_engine

DBSTR = 'mysql+mysqldb://MarieClaire:MarieClaire@localhost/MarieClaire?charset=utf8mb4'
ACCOUNT = {'id':'MarieClaire', 'pwd':'MarieClaire'}
ENGINE = create_engine(DBSTR, echo=True)

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
DISCOVERY_URI = ('https://analyticsreporting.googleapis.com/$discovery/rest')
CLIENT_SECRETS_PATH = '/home/henry/MarieClaire/zeocluster/src/MarieClaire.content/src/MarieClaire/content/browser/static/client_secrets.json'
VIEW_ID = '142892363'

def execSql(execStr):
    conn = ENGINE.connect() # DB連線
    execResult = conn.execute(execStr)
    conn.close()
    if execResult.returns_rows:
        return execResult.fetchall()

def initialize_analyticsreporting():
  """Initializes the analyticsreporting service object.

  Returns:
    analytics an authorized analyticsreporting service object.
  """
  # Parse command-line arguments.
  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawDescriptionHelpFormatter,
      parents=[tools.argparser])
  flags = parser.parse_args([])

  # Set up a Flow object to be used if we need to authenticate.
  flow = client.flow_from_clientsecrets(
      CLIENT_SECRETS_PATH, scope=SCOPES,
      message=tools.message_if_missing(CLIENT_SECRETS_PATH))

  # Prepare credentials, and authorize HTTP object with them.
  # If the credentials don't exist or are invalid run through the native client
  # flow. The Storage object will ensure that if successful the good
  # credentials will get written back to a file.
  storage = file.Storage('analyticsreporting.dat')
  credentials = storage.get()
  if credentials is None or credentials.invalid:
    credentials = tools.run_flow(flow, storage, flags)
  http = credentials.authorize(http=httplib2.Http())

  # Build the service object.
  analytics = build('analytics', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URI)

  return analytics

def get_report(analytics):
  # Use the Analytics Service Object to query the Analytics Reporting API V4.
  return analytics.reports().batchGet(
      body={
        'reportRequests': [
        {
          'viewId': VIEW_ID,
          'dateRanges': [{'startDate': '7daysAgo', 'endDate': 'today'}],
          'metrics': [
                      {'expression': 'ga:timeOnPage'},
                      {'expression': 'ga:pageviews'}
                     ],
          'dimensions': [{'name': 'ga:pageTitle'},
                         {'name': 'ga:date'},
                         {'name': 'ga:pagePathLevel2'}
                     ],
          "orderBys":[
                      {
                        "fieldName":"ga:date",
                      }],
        }]
      }
  ).execute()

def print_response(response):
  """Parses and prints the Analytics Reporting API V4 response"""
  for report in response.get('reports', []):
    columnHeader = report.get('columnHeader', {})
    dimensionHeaders = columnHeader.get('dimensions', [])
    metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])
    rows = report.get('data', {}).get('rows', [])

    for row in rows:
      dimensions = row.get('dimensions', [])
      # dateRangeValues = row.get('metrics', [])
      values = row.get('metrics', [])

      for header, dimension in zip(dimensionHeaders, dimensions):
        print header + ': ' + dimension
      for metricHeader, value in zip(metricHeaders, values[0]['values']):
        print metricHeader.get('name') + ': ' + value
        
def save2db(response):
  for report in response.get('reports', []):
    rows = report.get('data', {}).get('rows', [])
    for row in rows:
      url = row.get('dimensions')[2]
      page_title = row.get('dimensions')[0]
      date = row.get('dimensions')[1].encode('utf-8')
      date = date[:4]+'-'+date[4:6]+'-'+date[6:8]
      for value in row.get('metrics',[]):
        time_on_page = value.get('values')[0]
        page_view = value.get('values')[1]

      execStr = """ SELECT url_id FROM ga_url WHERE url = '{}' """.format(url)
      url_id = execSql(execStr)
      if url_id == []:
        execStr = """ INSERT INTO ga_url(url) VALUES('{}') """.format(url)
        
        execSql(execStr)
        execStr = """ SELECT url_id FROM ga_url WHERE url = '{}' """.format(url)
        tmp_url_id = execSql(execStr)
        
        execStr ="""INSERT INTO ga_data(page_title, page_view, time_on_page, date, url_id) 
              VALUES('{}', '{}', '{}', '{}', '{}') 
              """.format(page_title.encode('utf-8'), page_view, time_on_page, date, dict(tmp_url_id[0]).get('url_id'))
        execSql(execStr)
      else:  
        execStr = """ UPDATE ga_data SET page_view = '{}',time_on_page 
          = '{}' WHERE url_id = '{}' AND date = '{}' """.format(page_view, time_on_page, url_id, date)
        execSql(execStr)

def main():
 
  analytics = initialize_analyticsreporting()
  response = get_report(analytics)
  # print_response(response)
  save2db(response)
if __name__ == '__main__':
  main()