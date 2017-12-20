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


class GaReport(ManaBasic):
    template = ViewPageTemplateFile('template/ga_report.pt')

    def get_db_data(self):
        id = self.context.id
        postList = self.context.postList
        try:
            postList = postList.encode('utf-8').split('\r\n')
            if len(postList) == 1: #單獨一個postList跑sql會出錯
                postList = [postList[0], 'zzz']

            execStr = """ SELECT DISTINCT(page_title),url_id,page_url FROM ga_data WHERE 
                page_url IN {} """.format(tuple(postList))

            db_data = self.execSql(execStr)
            return db_data
        except:

            return 

    def __call__(self):
        if self.isAnonymous():
            return
        else:
            return self.template()


class GaEdit(ManaBasic):
    template = ViewPageTemplateFile('template/ga_edit.pt')
    def get_id(self):
        id = self.context.id
        return id
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
        select_type = self.request.get('select_type')
        select_data = self.request.get('select_data[]')
        if checkList is None:
            return json.dumps([{}, {}])

        if type(checkList) == str:
            checkList = [checkList, 'zzzzz']

        db_list = []
        day_list = []
        execStr = """SELECT page_url FROM ga_url WHERE url_id IN {}""".format(tuple(checkList))
        db_url = self.execSql(execStr)
        for url in db_url:
            tmp = dict(url)
            full_url = tmp['page_url'] + '%%'
            execStr = """ SELECT users,time_on_page,page_views,url_id,page_title,date FROM 
                ga_data WHERE full_url LIKE '{}' AND date BETWEEN '{}' AND '{}' 
                """.format(full_url, start, end)
            result = self.execSql(execStr)
            db_list.append(result)

        drawData = {}
        xs = {}
        if select_type == 'nav_pie':
            for db_data in db_list:
                execStr = """SELECT date FROM ga_data WHERE url_id = 
                    '{}' GROUP BY date""".format(dict(db_data[0])['url_id'])
                days = len(self.execSql(execStr))
                for data in db_data:
                    tmp = dict(data)
                    url_id = tmp['url_id']
                    page_title = tmp['page_title'][:10]
                    if drawData.has_key(url_id):
                        drawData[url_id][0].append(tmp['date'])
                        drawData[url_id][1][-1] += ( float(float(tmp['page_views'])/days) )
                    else:
                        xs['%s 瀏覽數' % page_title] = str(tmp['url_id'])
                        drawData[url_id] = [
                            [str(tmp['url_id']), tmp['date']],
                            ['%s 瀏覽數' % page_title, float(float(tmp['page_views'])/days)],
                        ]
        else:
            for db_data in db_list:
                for data in db_data:
                    tmp = dict(data)
                    url_id = tmp['url_id']
                    page_title = tmp['page_title'][:10]

                    if drawData.has_key(url_id):
                        if drawData[url_id][0][-1] == tmp['date']:
                            drawData[url_id][1][-1] += int(tmp['page_views'])
                            drawData[url_id][2][-1] += int(tmp['users'])
                            drawData[url_id][3][-1] =  round((drawData[url_id][3][-1] + float(tmp['time_on_page'])/int(tmp['page_views']))/2,2)
                        else:
                            drawData[url_id][0].append(tmp['date'])
                            drawData[url_id][1].append( int(tmp['page_views']) )
                            drawData[url_id][2].append( int(tmp['users']) )
                            drawData[url_id][3].append(round(float(tmp['time_on_page'])/int(tmp['page_views']),2))
                    else:
                        xs['%s 瀏覽數' % page_title] = str(tmp['url_id'])
                        xs['%s 使用人數' % page_title] = str(tmp['url_id'])
                        xs['%s 平均停留時間(秒)' % page_title] = str(tmp['url_id'])
                        drawData[url_id] = [
                            [str(tmp['url_id']), tmp['date']],
                            ['%s 瀏覽數' % page_title, int(tmp['page_views'])],
                            ['%s 使用人數' % page_title, int(tmp['users'])],
                            ['%s 平均停留時間(秒)' % page_title, round(float(tmp['time_on_page'])/int(tmp['page_views']),2)]
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

        execStr = """ SELECT * FROM ga_data
            WHERE url_id IN {} AND date BETWEEN '{}' AND '{}' """.format(tuple(ga_data_list), startDate, endDate)
        download_data = self.execSql(execStr)
        self.request.response.setHeader('Content-Type', 'application/csv')
        self.request.response.setHeader('Content-Disposition', 'attachment; filename="results.csv"')
        output = StringIO()
        output.write(u'\uFEFF'.encode('utf-8'))
        writer = csv.writer(output)
        writer.writerow(['名稱', '日期', '瀏覽數', '平均停留時間（秒）', '使用人數',])
        
        for data in download_data:
            tmp = dict(data)
            writer.writerow([
                tmp['page_title'],
                tmp['date'],
                tmp['page_views'],
                tmp['time_on_page'],
                tmp['users'],
            ])
        results = output.getvalue()
        output.close()
        return results