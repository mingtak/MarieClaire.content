from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone import api
import pymysql


class Show_trace(BrowserView):
    template = ViewPageTemplateFile('template/show_trace.pt')
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