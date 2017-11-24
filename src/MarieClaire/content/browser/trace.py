# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone import api
import pymysql
import json
import datetime
from MarieClaire.content import mysqlInfo
from cStringIO import StringIO
import csv

class Show_trace(BrowserView):
    template = ViewPageTemplateFile('template/show_trace.pt')
    def get_trace_list(self):
        web_site = self.request.get('web_site')
        length = len(web_site.split('http'))
        count = 1
        url_list = []
        while count < length:
            url = 'http'+web_site.split('http')[count]
            count+=1
            connection = pymysql.connect(
                host=mysqlInfo['host'],
                user=mysqlInfo['id'],
                password=mysqlInfo['password'],
                db=mysqlInfo['dbName'],
                charset=mysqlInfo['charset'],
                cursorclass=pymysql.cursors.DictCursor
            )
            try:
                with connection.cursor() as cursor:

                        sql = """SELECT DISTINCT(title) FROM trace_page WHERE url='{}' """.format(url)
                        cursor.execute(sql)
                        result = cursor.fetchone()
                        url_list.append([result['title'],url])

                connection.commit()
            finally:
                connection.close()
            
        return url_list
    
    def get_ads_list(self):
        ads_list = self.request.get('ads')
        split_ads = ads_list.split(',')
        return split_ads
    
    # def downloadFile(self):
    #     self.request.response.setHeader('Content-Type', 'application/csv')
    #     self.request.response.setHeader('Content-Disposition', 'attachment; filename="results.csv"')

    #     output = StringIO()
    #     output.write(u'\uFEFF'.encode('utf-8'))
    #     writer = csv.writer(output)
    #     writer.writerow(['標題'])
    #     for item in self.brain:
    #         import pdb;pdb.set_trace()
    #         obj_item = item.getObject()


    def __call__(self):
        return self.template()


class Save_trace_page(BrowserView):
    def __call__(self):
        url = self.request.get('url')
        title = self.request.get('title')
        if not title:
            title = '無標題貼文'.decode('utf-8')
        connection = pymysql.connect(
            host=mysqlInfo['host'],
            user=mysqlInfo['id'],
            password=mysqlInfo['password'],
            db=mysqlInfo['dbName'],
            charset=mysqlInfo['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            with connection.cursor() as cursor:
                today = datetime.date.today().strftime('%Y-%m-%d')
                try:
                    sql = """SELECT day_count FROM trace_page WHERE url='{}' 
                        AND date='{}' """.format(url,today)
                    cursor.execute(sql)
                    result = cursor.fetchone()
                    result['day_count']+=1

                    sql = """UPDATE trace_page SET day_count={} WHERE url='{}' 
                        AND date='{}' """.format(result['day_count'], url, today)
                    cursor.execute(sql)
                except:
                    sql = """INSERT INTO trace_page(title, url, date, day_count) VALUES ('{}', '{}','{}',1)""".format(title, url, today)
                    cursor.execute(sql)

            connection.commit()
        finally:
            connection.close()


class Select_trace_page(BrowserView):
    def __call__(self):
        url = self.request.get('url')
        start_date = self.request.get('start_date')
        end_date = self.request.get('end_date')
        select_all = self.request.get('select_all')

        connection = pymysql.connect(
            host=mysqlInfo['host'],
            user=mysqlInfo['id'],
            password=mysqlInfo['password'],
            db=mysqlInfo['dbName'],
            charset=mysqlInfo['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            with connection.cursor() as cursor:
                if select_all == 'true':
                    sql = """SELECT  year(date) as year,month(date) as month ,day(date) as 
                        day,SUM(day_count) as day_count FROM trace_page WHERE date BETWEEN '{}' AND '{}' 
                        GROUP BY year(date),month(date),day(date)""".format(start_date, end_date)
                else:
                    sql = """SELECT day_count,date FROM trace_page WHERE url='{}' 
                        AND date BETWEEN '{}' AND '{}'""".format(url, start_date, end_date)
                cursor.execute(sql)
                trace_list = cursor.fetchall()
                data = []
                for trace in trace_list:
                    if select_all == 'true':
                        data.append({
                            'date_time':'{}-{}-{}'.format(trace['year'],trace['month'],trace['day']),
                            'count':trace['day_count']
                        })
                    else:
                        data.append({
                        'date_time':trace['date'],
                        'count':trace['day_count']
                        })
                
                json_data = json.dumps(data, default=str)
                return json_data

            connection.commit()

        finally:
            connection.close()

