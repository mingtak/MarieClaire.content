from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone import api
import pymysql
import json

class Show_trace(BrowserView):
    template = ViewPageTemplateFile('template/show_trace.pt')
    def get_trace_list(self):
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='henry!QAZ@WSX',
            db='MarieClaire',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            with connection.cursor() as cursor:
                
                sql = """SELECT DISTINCT url FROM `trace_page`"""
                cursor.execute(sql)
                result = cursor.fetchall()
                return result

            connection.commit()

        finally:
            connection.close()

    def __call__(self):
        return self.template()


class Save_trace_page(BrowserView):
    def __call__(self):
        url = self.request.get('url')
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='henry!QAZ@WSX',
            db='MarieClaire',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            with connection.cursor() as cursor:
                
                sql = """INSERT INTO trace_page(url) VALUES ('{}')""".format(url)
                cursor.execute(sql)
            connection.commit()

        finally:
            connection.close()


class Select_trace_page(BrowserView):
    def __call__(self):
        url = self.request.get('url')
        start_date = self.request.get('start_date')
        end_date = self.request.get('end_date')

        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='henry!QAZ@WSX',
            db='MarieClaire',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            with connection.cursor() as cursor:

                sql = """SELECT url,year(time) as year,month(time)as month,day(time) as day
                ,COUNT(day(time))as count FROM trace_page as tp WHERE url='{}' AND time 
                BETWEEN '{}' AND '{}' GROUP BY year(time),month(time),day(time)""".format(url, start_date, end_date)
                cursor.execute(sql)

                trace_list = cursor.fetchall()
                data = []
                for trace in trace_list:
                    data.append({
                        'url':trace['url'],
                        'date_time':'{}-{}-{}'.format(trace['year'],trace['month'],trace['day']),
                        'count':trace['count']
                    })
                json_data = json.dumps(data, default=str)
                return json_data

            connection.commit()

        finally:
            connection.close()
