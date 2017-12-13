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
from cStringIO import StringIO
import csv

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


class GaReport(ManaBasic):
    template = ViewPageTemplateFile('template/ga_report.pt')

    def get_db_data(self):
        execStr = """SELECT page_title, url_id FROM ga_data"""
        return self.execSql(execStr)

    def __call__(self):
        if self.isAnonymous():
            return
        else:
            return self.template()


class GetGaData(ManaBasic):
    def __call__(self):
        start = self.request.get('start')
        end = self.request.get('end')
        checkList = self.request.get('checkList[]')
        if checkList is None:
            return json.dumps([{}, {}])

        if type(checkList) == str:
            checkList = [checkList, 'zzzzz']
        execStr = """ SELECT * FROM ga_data WHERE url_id IN
            {} AND date BETWEEN '{}' AND '{}' """.format(tuple(checkList), start, end)
        
        result = self.execSql(execStr)
        drawData = {}
        xs = {}
        for data in result:
            tmp = dict(data)
            url_id = tmp['url_id']
            if drawData.has_key(url_id):
                drawData[orderId][0].append(tmp['date'])
                drawData[orderId][1].append( int(tmp['page_view']) )
                drawData[orderId][2].append( int(tmp['time_on_page']) )
            else:
                xs['%s 瀏覽數' % tmp['page_title']] = str(tmp['url_id'])
                xs['%s 停留時間' % tmp['page_title']] = str(tmp['url_id'])
                drawData[url_id] = [
                    [str(tmp['url_id']), tmp['date']],
                    ['%s 瀏覽數' % tmp['page_title'], int(tmp['page_view'])],
                    ['%s 停留時間' % tmp['page_title'], int(tmp['time_on_page'])]
                ]
        return json.dumps([xs, drawData])


class DelGaData(ManaBasic):

    def __call__(self):
        checkList = self.request.form.get('check_list[]')
        time = self.request.form.get('time')

        if type(checkList) == str:
            checkList = [checkList, 'zzzzz']
        execStr = """DELETE FROM ga_data WHERE url_id IN {} 
        AND date = '{}' """.format(tuple(checkList), time)
        self.execSql(execStr)


class DownloadGaFile(ManaBasic):
    def __call__(self):
        request = self.request
        checkList = request.form.get('checkList[]')
        startDate = request.form.get('start')
        endDate = request.form.get('end')
        ga_data = checkList.split(',')
        ga_data_list = []
        for i in range(0, len(ga_data)):
            ga_data_list.append(ga_data[i])

        execStr = """ SELECT page_title,page_view,time_on_page,date FROM ga_data
            WHERE url_id IN {} AND date BETWEEN '{}' AND '{}' """.format(tuple(ga_data_list), startDate, endDate)
        download_data = self.execSql(execStr)
        self.request.response.setHeader('Content-Type', 'application/csv')
        self.request.response.setHeader('Content-Disposition', 'attachment; filename="results.csv"')
        output = StringIO()
        output.write(u'\uFEFF'.encode('utf-8'))
        writer = csv.writer(output)
        writer.writerow(['名稱', '日期', '瀏覽數', '停留時間'])
        
        for data in download_data:
            tmp = dict(data)
            writer.writerow([
                tmp['page_title'],
                tmp['date'],
                tmp['page_view'],
                tmp['time_on_page'],

            ])
        results = output.getvalue()
        output.close()
        return results