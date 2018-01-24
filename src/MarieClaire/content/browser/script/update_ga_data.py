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
CLIENT_SECRETS_PATH = '/home/marieclaire/Plone/zeocluster/src/MarieClaire.content/src/MarieClaire/content/browser/static/client_secrets.json'
VIEW_ID = '5906876'

EndDay = datetime.datetime.now()
StartDay = EndDay - datetime.timedelta(days = 90)

def execSql(execStr):
    conn = ENGINE.connect() # DB連線
    execResult = conn.execute(execStr)
    conn.close()
    if execResult.returns_rows:
        return execResult.fetchall()

def initialize_analyticsreporting():

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
    storage = file.Storage('/home/marieclaire/Plone/zeocluster/src/MarieClaire.content/src/MarieClaire/content/browser/script/analyticsreporting.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, flags)
    http = credentials.authorize(http=httplib2.Http())

    # Build the service object.
    analytics = build('analytics', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URI)

    return analytics

def get_report(analytics, index):
  # Use the Analytics Service Object to query the Analytics Reporting API V4.
    return analytics.reports().batchGet(
        body={
        'reportRequests': [
        {
            'viewId': VIEW_ID,
            'dateRanges': [{'startDate': StartDay.strftime('%Y-%m-%d'), 'endDate': EndDay.strftime('%Y-%m-%d')}],
            'metrics': [
                        {'expression': 'ga:timeOnPage'},
                        {'expression': 'ga:pageviews'},
                        {'expression': 'ga:sessions'},
                        {'expression': 'ga:users'},
                        {'expression': 'ga:pageviewsPerSession'},
                        {'expression': 'ga:avgSessionDuration'},
                        {'expression': 'ga:bounceRate'},
                        {'expression': 'ga:percentNewSessions'}
                        ],
            'dimensions': [
                            {'name': 'ga:hostname'},
                            {'name': 'ga:pagePath'},
                            {'name': 'ga:pageTitle'},
                            {'name': 'ga:date'},
                            {'name': 'ga:pagePathLevel1'},
                            {'name': 'ga:pagePathLevel2'},
                            {'name': 'ga:pagePathLevel3'},
                        ],
            "orderBys":[
                        {"fieldName":"ga:date"}
                        ],
            "pageToken": index,
            "pageSize": 10000
        }]
      }
  ).execute()

# def print_response(response):
#   """Parses and prints the Analytics Reporting API V4 response"""
#   for report in response.get('reports', []):
#     columnHeader = report.get('columnHeader', {})
#     dimensionHeaders = columnHeader.get('dimensions', [])
#     metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])
#     rows = report.get('data', {}).get('rows', [])

#     for row in rows:
#       dimensions = row.get('dimensions', [])
#       # dateRangeValues = row.get('metrics', [])
#       values = row.get('metrics', [])

#       for header, dimension in zip(dimensionHeaders, dimensions):
#         print header + ': ' + dimension
#       for metricHeader, value in zip(metricHeaders, values[0]['values']):
#         print metricHeader.get('name') + ': ' + value

      
def save2db(response, count):
  for report in response.get('reports', []):
    rows = report.get('data', {}).get('rows', [])
    for row in rows:
        dimensions = row.get('dimensions', [])
        host_name = dimensions[0].encode('utf-8')
        full_url = host_name + dimensions[1].encode('utf-8')

# page_url也要處理特殊字元
        page_url = host_name + dimensions[4].encode('utf-8') + dimensions[5].encode('utf-8').split('/')[1] + '/' + dimensions[6].encode('utf-8').split('/')[1]
#        page_url = page_url.replace('"','”'.decode('utf-8')).replace("'","’".decode('utf-8')).replace("%","％".decode('utf-8'))
        page_title = dimensions[2].replace('"','”'.decode('utf-8')).replace("'","’".decode('utf-8')).replace("%","％".decode('utf-8'))
        date = dimensions[3][:4] + '-' +dimensions[3][4:6] + '-' + dimensions[3][6:8]

        time_on_page = row.get('metrics',[])[0]['values'][0]
        page_views = row.get('metrics',[])[0]['values'][1]
        sessions = row.get('metrics',[])[0]['values'][2]
        users = row.get('metrics',[])[0]['values'][3]
        pageviewsPerSession = row.get('metrics',[])[0]['values'][4][:4]
        avgSessionDuration = row.get('metrics',[])[0]['values'][5][:4]
        bounceRate = row.get('metrics',[])[0]['values'][6][:4]
        percentNewSessions = row.get('metrics',[])[0]['values'][7][:4]
        try:
            execStr = """ SELECT url_id FROM ga_url WHERE page_url = "{}" """.format(page_url)
            url_id = execSql(execStr)
        except :
#先寫到檔案去，再決定怎麼後續處理
            with open('/tmp/wrong_page_url', 'a') as file:
                file.write('%s\n' % page_url)
            continue
#            import pdb;pdb.set_trace()

        if url_id == []: #判斷有沒有url_id，若沒有代表他是這url_id的第1筆，就直接寫進去
            execStr = """ INSERT INTO ga_url(page_url) VALUES("{}") """.format(page_url)
            execSql(execStr)

            execStr = """ SELECT url_id FROM ga_url WHERE page_url = "{}" """.format(page_url)
            tmp_url_id = execSql(execStr)
        
            execStr = """INSERT INTO ga_data( host_name, page_url, full_url, page_title, date,
                time_on_page, page_views, sessions, users, pageviewsPerSession, 
                avgSessionDuration, bounceRate, percentNewSessions, url_id) VALUES ('{}'
                , "{}", "{}", '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')
                """.format(host_name, page_url, full_url, page_title.encode('utf-8'), date, time_on_page, 
                page_views, sessions, users, pageviewsPerSession, avgSessionDuration, bounceRate, 
                percentNewSessions, dict(tmp_url_id[0]).get('url_id'))
            try:
                execSql(execStr)
            except:
                continue
                import pdb; pdb.set_trace()

        else:
            execStr = """ SELECT full_url FROM ga_data WHERE full_url = "{}" 
                AND date = '{}' """.format(full_url, date)

            try:
                result = execSql(execStr)
            except:
                continue
                import pdb;pdb.set_trace()

            if result == []:
                #判斷他完整的網址有沒有重複，若有就在判斷他新的page_view有沒有比舊的大
                #有的話才update，若完整的網址沒重複就直接寫進資料庫
                execStr = """INSERT INTO ga_data( host_name, page_url, full_url, page_title, date,
                    time_on_page, page_views, sessions, users, pageviewsPerSession, 
                    avgSessionDuration, bounceRate, percentNewSessions, url_id) VALUES ('{}'
                    , "{}", "{}", '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')
                    """.format(host_name, page_url, full_url, page_title.encode('utf-8'), date, time_on_page, 
                    page_views, sessions, users, pageviewsPerSession, avgSessionDuration, 
                    bounceRate, percentNewSessions, dict(url_id[0]).get('url_id'))
                try:
                    execSql(execStr)
                except:
                    continue
                    import pdb; pdb.set_trace()
            else:
                execStr = """SELECT page_views,page_title FROM ga_data WHERE page_url = "{}"
                     AND date = '{}' """.format(page_url, date)
                result = execSql(execStr)
                db_data = dict(result[0])

                if db_data['page_views'] < page_views:
                    execStr = """ UPDATE ga_data SET page_title = '{}', time_on_page = '{}'
                        , page_views = '{}', sessions = '{}', users = '{}', pageviewsPerSession = '{}'
                        , avgSessionDuration = '{}', bounceRate = '{}', percentNewSessions = '{}' 
                        WHERE url_id = '{}' AND date = '{}' """.format(page_title.encode('utf-8')
                        , time_on_page, page_views, sessions, users, pageviewsPerSession
                        , avgSessionDuration, bounceRate, percentNewSessions
                        , dict(url_id[0]).get('url_id'), date)
                    execSql(execStr)
        count+=1
    return count


def main(count):
  
    analytics = initialize_analyticsreporting()
    response = get_report(analytics, str(count))
    # print_response(response)
    new_count = save2db(response, count)

    if new_count%10000 == 0:
        main(new_count)

if __name__ == '__main__':
    main(0)
