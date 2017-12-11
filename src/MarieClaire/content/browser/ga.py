# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone import api
import logging
import json
from MarieClaire.content import DBSTR
from sqlalchemy import create_engine
import datetime
import argparse
from apiclient.discovery import build
import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools

logger = logging.getLogger('MarieClaire.content')
LIMIT=20
ENGINE = create_engine(DBSTR, echo=True)


class ManaBasic(BrowserView):

    def execSql(self, execStr):
        conn = ENGINE.connect() # DB連線
        execResult = conn.execute(execStr)
        conn.close()
        if execResult.returns_rows:
            return execResult.fetchall()

    def isAnonymous(self):
        portal = api.portal.get()
        if api.user.is_anonymous():
            self.request.response.redirect('%s/login' % portal.absolute_url())
        return api.user.is_anonymous()

class SaveGaData(ManaBasic): #javascript版 顯示ga資料
    def __call__(self):
        sessionDuration = self.request.get('sessionDuration')
        users = self.request.get('users')
        today = datetime.date.today()
        execStr = """INSERT INTO ga_data(sessionDuration, 
                users , date) VALUES('{}', '{}', '{}') 
                """.format(sessionDuration, users, today.strftime('%Y-%m-%d'))
        self.execSql(execStr)


class GaDraw(ManaBasic):
    template = ViewPageTemplateFile('template/ga_draw.pt')

    def __call__(self):
        if self.isAnonymous():
            return
        else:
            return self.template()


class GetGaData(ManaBasic):
    def __call__(self):
        start = self.request.get('start')
        end = self.request.get('end')

        execStr = """SELECT * FROM ga_data WHERE date BETWEEN '{}' AND '{}' """.format(start, end)
        return self.execSql(execStr)

# class PythonShowGaDate(ManaBasic):  # plone版   顯示ga資料
#     def __call__(self):
#         SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
#         DISCOVERY_URI = ('https://analyticsreporting.googleapis.com/$discovery/rest')
#         CLIENT_SECRETS_PATH = '/home/henry/MarieClaire/zeocluster/src/MarieClaire.content/src/MarieClaire/content/browser/static/client_secrets.json'

#         parser = argparse.ArgumentParser(
#             formatter_class=argparse.RawDescriptionHelpFormatter,
#             parents=[tools.argparser])
#         flags = parser.parse_args([])


#         flow = client.flow_from_clientsecrets(
#             CLIENT_SECRETS_PATH, scope=SCOPES,
#             message=tools.message_if_missing(CLIENT_SECRETS_PATH))

#         storage = file.Storage('analyticsreporting.dat')
#         credentials = storage.get()
#         if credentials is None or credentials.invalid:
#             credentials = tools.run_flow(flow, storage, flags)
#         http = credentials.authorize(http=httplib2.Http())

#         # Build the service object.
#         analytics = build('analytics', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URI)
        
#         self.get_report(analytics)

#     def get_report(self, analytics):
#         # Use the Analytics Service Object to query the Analytics Reporting API V4.
#         response = analytics.reports().batchGet(
#             body={
#                 'reportRequests': [
#                 {
#                 'viewId': '166020368',
#                 'dateRanges': [{'startDate': '30daysAgo', 'endDate': 'today'}],
#                 'metrics': [{'expression': 'ga:sessions'}]
#                 }]
#             }
#         ).execute()
#         self.print_response(response)

#     def print_response(self, response):
#         """Parses and prints the Analytics Reporting API V4 response"""

#         for report in response.get('reports', []):
#             columnHeader = report.get('columnHeader', {})
#             dimensionHeaders = columnHeader.get('dimensions', [])
#             metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])
#             rows = report.get('data', {}).get('rows', [])

#             for row in rows:
#                 dimensions = row.get('dimensions', [])
#                 dateRangeValues = row.get('metrics', [])

#             for header, dimension in zip(dimensionHeaders, dimensions):
#                 print header + ': ' + dimension

#             for i, values in enumerate(dateRangeValues):
#                 print 'Date range (' + str(i) + ')'
#                 for metricHeader, value in zip(metricHeaders, values.get('values')):
#                     print metricHeader.get('name') + ': ' + value


