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

    def checkUser(self):
        current = api.user.get_current().id
        roles = api.user.get_roles()
        if 'Manager' in roles or 'ALL' in self.context.ownerList:
            return True
        elif 'AE' in self.context.ownerList and 'Reader' in api.user.get_roles():
            return True
        elif 'PLANNER' in self.context.ownerList and 'Editor' in api.user.get_roles():
            return True 
        else:
            if self.context.ownerList is None:
                return False
            else:
                ownerList = self.context.ownerList.split('\n')
                for tmpId in ownerList:
                    if current == tmpId.strip():
                        return True
                    else:
                        continue
                return False

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
    
    def get_table_data(self):
        brain = self.context.tableList
        if brain == None:
            return 
        else:
            tableData = brain.encode('utf-8').split('\r\n')
            return tableData

    def __call__(self):
        if self.isAnonymous():
            return
        else:
            return self.template()


class GaEdit(ManaBasic):
    template = ViewPageTemplateFile('template/ga_edit.pt')

    def checkUser(self):
        current = api.user.get_current().id
        roles = api.user.get_roles()
        if 'Manager' in roles or 'ALL' in self.context.ownerList:
            return True
        elif 'AE' in self.context.ownerList and 'Reader' in api.user.get_roles():
            return True
        elif 'PLANNER' in self.context.ownerList and 'Editor' in api.user.get_roles():
            return True
        else:
            if self.context.ownerList is None:
                return False
            else:
                ownerList = self.context.ownerList.split('\n')
                for tmpId in ownerList:
                    if current == tmpId.strip():
                        return True
                    else:
                        continue
                return False


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

# 針對 url_id會被過濾掉的解 start
        db_url = []
        db_url_id = []
        for tmp_url_id in checkList:
            execStr = """SELECT page_url FROM ga_url WHERE url_id = '{}'""".format(tmp_url_id)
            tmp_db_url = self.execSql(execStr)
            for tmp_item in tmp_db_url:
                db_url.append(tmp_item)
                db_url_id.append(tmp_url_id)

        for i in range(len(db_url)):
            tmp = dict(db_url[i])
            full_url = tmp['page_url'] + '%%'
            logger.info('LINE 139: %s' % db_url[i])
            execStr = """ SELECT users,time_on_page,page_views,url_id,page_title,date FROM
                ga_data WHERE full_url LIKE '{}' AND date BETWEEN '{}' AND '{}'
                """.format(full_url, start, end)
            result = self.execSql(execStr)
            tmp_result = []
            for tmp_item in result:
                tmp_result.append(dict(tmp_item))
                tmp_result[-1]['url_id'] = db_url_id[i]
            result = tmp_result
            db_list.append(result)
# 針對 url_id會被過濾掉的解 end

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
                        drawData[url_id][1][-1] += (float(float(tmp['page_views'])/days))
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
                            drawData[url_id][3][-1] =  round((drawData[url_id][3][-1]+float(tmp['time_on_page'])/int(tmp['page_views']))/2, 2)
                        else:
                            drawData[url_id][0].append(tmp['date'])
                            drawData[url_id][1].append(int(tmp['page_views']))
                            drawData[url_id][2].append(int(tmp['users']))
                            drawData[url_id][3].append(round(float(tmp['time_on_page'])/int(tmp['page_views']), 2))
                    else:
                        xs['%s 瀏覽數' % page_title] = str(tmp['url_id'])
                        xs['%s 使用人數' % page_title] = str(tmp['url_id'])
                        xs['%s 平均停留時間(秒)' % page_title] = str(tmp['url_id'])
                        drawData[url_id] = [
                            [str(tmp['url_id']), tmp['date']],
                            ['%s 瀏覽數' % page_title, int(tmp['page_views'])],
                            ['%s 使用人數' % page_title, int(tmp['users'])],
                            ['%s 平均停留時間(秒)' % page_title, round(float(tmp['time_on_page'])/int(tmp['page_views']), 2)]
                        ]

        # bar chart use.柱型圖補0，使能堆疊
        if select_type == 'nav_bar':
            execStr = """SELECT DISTINCT(DATE) FROM ga_data WHERE url_id in {} 
            AND DATE BETWEEN '{}' AND '{}'""".format(tuple(checkList), start, end)
            dayList = self.execSql(execStr)
            if type(self.request.form.get('checkList[]')) == str:
                checkList = [self.request.form.get('checkList[]')] 
            for checked in checkList:
                for day in dayList:
                    tmp = dict(day)
                    date = str(tmp['DATE'])
                    if date not in drawData[checked][0]:
                        drawData[checked][0].append(date)
                        drawData[checked][1].append(0)
                        drawData[checked][2].append(0)
                        drawData[checked][3].append(0)

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
            WHERE url_id IN {} AND date BETWEEN '{}' AND
             '{}' """.format(tuple(ga_data_list), startDate, endDate)
        download_data = self.execSql(execStr)
        self.request.response.setHeader('Content-Type', 'application/csv')
        self.request.response.setHeader('Content-Disposition', 'attachment; filename="results.csv"')
        output = StringIO()
        output.write(u'\uFEFF'.encode('utf-8'))
        writer = csv.writer(output)
        writer.writerow(['名稱', '日期', '瀏覽數', '平均停留時間（秒）', '使用人數'])

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

class AuthorityEdit(ManaBasic):
    template = ViewPageTemplateFile('template/authority_edit.pt')
    def checkUser(self):
        current = api.user.get_current().getUserName()
        brain = api.content.find(context=self.context)
        roles = api.user.get_roles()
        if 'Manager' in roles or 'ALL' in self.context.ownerList:
            return True
        elif 'AE' in self.context.ownerList and 'Reader' in api.user.get_roles():
            return True
        elif 'PLANNER' in self.context.ownerList and 'Editor' in api.user.get_roles():
            return True
        else:
            if brain[0].getObject().ownerList == None:
                return False
            else:
                ownerList = brain[0].getObject().ownerList.split('\n')
                for owner in ownerList:
                    if owner == current.strip():
                        return True
                    else:
                        continue
                return False

    def get_id(self):
        id = self.context.id
        return id

    def __call__(self):
        return self.template()

class UpdataGaTableData(ManaBasic):

    def __call__(self):
        SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
        DISCOVERY_URI = ('https://analyticsreporting.googleapis.com/$discovery/rest')
        CLIENT_SECRETS_PATH = '/home/marieclaire/Plone/zeocluster/src/MarieClaire.content/src/MarieClaire/content/browser/static/client_secrets.json'
        
        parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[tools.argparser])
        flags = parser.parse_args([])

        flow = client.flow_from_clientsecrets(
            CLIENT_SECRETS_PATH, scope=SCOPES,
            message=tools.message_if_missing(CLIENT_SECRETS_PATH))

        storage = file.Storage('/home/marieclaire/Plone/zeocluster/analyticsreporting.dat')
        credentials = storage.get()
        if credentials is None or credentials.invalid:
            credentials = tools.run_flow(flow, storage, flags)
        http = credentials.authorize(http=httplib2.Http())

        # Build the service object.
        analytics = build('analytics', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URI)

        self.get_report(analytics)

    def get_report(self, analytics):
        VIEW_ID = '5906876'
        brain = api.content.find(Type="Custom")
        for item in brain:
            brain_tableList = item.getObject().tableList
            try:
                tableList = brain_tableList.split('\r\n')
                for data in tableList:
                    page_url = data.split(',')[0]
                    start_date = data.split(',')[1]
                    end_date = data.split(',')[2]

                    response = analytics.reports().batchGet(
                        body={
                        'reportRequests': [
                            {
                            'viewId': VIEW_ID,
                            'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
                            'metrics': [
                                        {'expression': 'ga:pageviews'},
                                        ],
                            'dimensions': [
                                            {'name': 'ga:date'},
                                            {'name': 'ga:sourceMedium'},
                                            {'name': 'ga:pagePath'}
                                        ],
                            "orderBys":[
                                        {"fieldName":"ga:date"}
                                        ],
                            "filtersExpression": 'ga:pagePath=~%s' %page_url,
                            }],
                        }
                    ).execute()
                    self.save2db(response)
            except:
                pass

    def save2db(self, response):
        for report in response.get('reports', []):
            rows = report.get('data', {}).get('rows', [])
            for row in rows:
                dimensions = row.get('dimensions', [])
                date = str(dimensions[0][:4] + '-' +dimensions[0][4:6] + '-' + dimensions[0][6:8])
                title = str(dimensions[1])
                page_url = str(dimensions[2])
                page_views = row.get('metrics',[])[0]['values'][0]
                try:
                    execStr = """SELECT date,title FROM ga_table WHERE date = '{}' AND 
                        title = '{}'""".format(date, title)
                    result = self.execSql(execStr)
                except:
                    import pdb;pdb.set_trace()
                
                if result == []:
                    execStr = """INSERT INTO ga_table(page_url,title,page_views,date) VALUES('{}',
                        '{}', '{}', '{}')""".format(page_url, title, page_views, date)
                    self.execSql(execStr)


class GaTable(ManaBasic):
    template = ViewPageTemplateFile('template/ga_table.pt')

    def __call__(self):
        checkList = self.request.get('checkList')
        page_url = checkList.split(',')[0]
        start_date = checkList.split(',')[1]
        end_date = checkList.split(',')[2]
        firstTime = checkList.split(',')[3]
        tableData = {}
        dayList = []
        weekSum = []

        # 抓title，並再每個title欄位內先填入空值
        execStr = """SELECT DISTINCT(title) FROM ga_table WHERE date BETWEEN '{}' AND 
            '{}' AND page_url = '{}'""".format(start_date, end_date, page_url)
        result_page_title = self.execSql(execStr)
        page_title_list = []
        for title in result_page_title:
            tmp = dict(title)
            title = tmp['title']
            page_title_list.append(title)
            tableData[title] = ['']
        self.page_title_list = page_title_list #table 的title
        #第一次報表資料產生
        first_section_time = datetime.datetime.strptime(start_date, '%Y-%m-%d') + datetime.timedelta(days = int(firstTime)-1)
        execStr = """SELECT title,SUM(page_views) as sum_pv FROM ga_table WHERE page_url 
            = '{}' AND date BETWEEN '{}' AND '{}' GROUP BY title 
            """.format(page_url, start_date, first_section_time)
        result_first_section = self.execSql(execStr)

        for data in result_first_section:
            tmp = dict(data)
            title = tmp['title']
            page_views = int(tmp['sum_pv'])

            tableData[title] = [page_views]

        for title in page_title_list:#先再之後的空位填上空值，讓之後好判斷有無資料
            tableData[title].append('')

        #抓一個區間的總數
        execStr = """SELECT SUM(page_views) as sum_pv FROM ga_table WHERE page_url = '{}' 
            AND date BETWEEN'{}' AND '{}'""".format(page_url, start_date, first_section_time)
        result_week_sum = self.execSql(execStr)
        for data in result_week_sum:
            tmp =dict(data)
            page_views = tmp['sum_pv']
            if page_views == None:
                weekSum.append('')
                weekSum.append('')
            else:
                weekSum.append(int(page_views))
                weekSum.append('')

        #填入開始及結束時間
        dayList.append(['{}~{}'.format(start_date,datetime.datetime.strftime(first_section_time, '%Y-%m-%d'))])

        next_section_time = first_section_time + datetime.timedelta(days=7)

        while next_section_time <= datetime.datetime.strptime(end_date, '%Y-%m-%d'):
            execStr = """SELECT title,SUM(page_views) as sum_pv FROM ga_table WHERE 
                page_url = '{}' AND date BETWEEN '{}' AND '{}' GROUP BY title
                """.format(page_url, first_section_time, next_section_time)
            result_next_section = self.execSql(execStr)

            tmp_title_list = list(page_title_list)

            for data in result_next_section:
                tmp = dict(data)
                title = tmp['title']
                page_views = int(tmp['sum_pv'])
                #有值的填入數字然後把填過的title刪掉
                tableData[title].append(page_views)
                tableData[title].append('')
                tmp_title_list.remove(title)
            #沒背填到的title補空格
            for title in tmp_title_list:
                tableData[title].append('')
                tableData[title].append('')

            execStr = """SELECT SUM(page_views) as sum_pv FROM ga_table WHERE page_url = '{}' 
            AND date BETWEEN'{}' AND '{}'""".format(page_url, first_section_time, next_section_time)
            result_week_sum = self.execSql(execStr)
            for data in result_week_sum:
                tmp =dict(data)
                page_views = tmp['sum_pv']

                if page_views == None:
                    weekSum.append('')
                    weekSum.append('')
                else:
                    weekSum.append(int(page_views))
                    weekSum.append('')

            dayList.append(['{}~{}'.format(datetime.datetime.strftime(first_section_time+datetime.timedelta(days=1), '%Y-%m-%d'), 
                datetime.datetime.strftime(next_section_time, '%Y-%m-%d'))])
            #計算下個7天的時間
            first_section_time = next_section_time
            next_section_time += datetime.timedelta(days=7)

        else:
            #最後一筆
            execStr = """SELECT title,SUM(page_views) as sum_pv FROM ga_table WHERE 
                page_url = '{}' AND date BETWEEN '{}' AND '{}' GROUP BY title
                """.format(page_url, first_section_time, end_date)
            result_last_section = self.execSql(execStr)

            tmp_title_list = list(page_title_list)

            for data in result_last_section:
                tmp = dict(data)
                title = tmp['title']
                page_views = int(tmp['sum_pv'])

                tableData[title].append(page_views)
                tableData[title].append('')
                tmp_title_list.remove(title)

            for title in tmp_title_list:
                tableData[title].append('')
                tableData[title].append('')

            execStr = """SELECT SUM(page_views) as sum_pv FROM ga_table WHERE page_url = '{}' 
            AND date BETWEEN'{}' AND '{}'""".format(page_url, first_section_time, end_date)
            result_week_sum = self.execSql(execStr)
            for data in result_week_sum:
                tmp =dict(data)
                page_views = tmp['sum_pv']
                if page_views == None:
                    weekSum.append('')
                    weekSum.append('')
                else:
                    weekSum.append(int(page_views))
                    weekSum.append('')

            dayList.append(['{}~{}'.format(
                datetime.datetime.strftime(first_section_time+datetime.timedelta(days=1), '%Y-%m-%d')
                , str(end_date))])
        
        self.tableData = tableData #table內的值
        self.dayList = dayList #時間區間
        self.weekSum = weekSum #全部區間的總數
        return self.template()
