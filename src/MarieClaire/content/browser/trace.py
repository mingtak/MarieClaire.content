from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone import api
import pymysql
import json
import datetime

class Show_trace(BrowserView):
    template = ViewPageTemplateFile('template/show_trace.pt')
    def get_trace_list(self):
        web_site = self.request.get('web_site')
        length = len(web_site.split('http'))
        count = 1
        url_list = []
        while count < length:
            url_list.append('http'+web_site.split('http')[count])
            count+=1
        return url_list
    
    def get_ads_list(self):
        ads_list = self.request.get('ads')
        split_ads = ads_list.split(',')
        return split_ads

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
                try:
                    sql = """SELECT day_count FROM trace_page WHERE url='{}'""".format(url)
                    cursor.execute(sql)
                    result = cursor.fetchone()
                    result['day_count']+=1
                    sql = """UPDATE trace_page SET day_count={} WHERE url='{}'""".format(result['day_count'], url)
                    cursor.execute(sql)
                except:
                    today = datetime.date.today().strftime('%Y-%m-%d')
                    sql = """INSERT INTO trace_page(url,date) VALUES ('{}',{})""".format(url,today)
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
            host='localhost',
            user='root',
            password='henry!QAZ@WSX',
            db='MarieClaire',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            with connection.cursor() as cursor:
                if select_all == 'true':
                    sql = """SELECT year(time) as year,month(time) as month,day(time) as day, 
                    COUNT(day(time)) as count FROM trace_page WHERE time BETWEEN'{}' 
                    AND '{}' GROUP BY year(time),month(time),day(time)""".format(start_date, end_date)
                else:
                    sql = """SELECT url,year(time) as year,month(time)as month,day(time) as day
                    ,COUNT(day(time))as count FROM trace_page as tp WHERE url='{}' AND time 
                    BETWEEN '{}' AND '{}' GROUP BY year(time),month(time),day(time)""".format(url, start_date, end_date)

                cursor.execute(sql)
                trace_list = cursor.fetchall()

                data = []
                for trace in trace_list:
                    data.append({
                        'date_time':'{}-{}-{}'.format(trace['year'],trace['month'],trace['day']),
                        'count':trace['count']
                    })
                
                json_data = json.dumps(data, default=str)
                return json_data

            connection.commit()

        finally:
            connection.close()
