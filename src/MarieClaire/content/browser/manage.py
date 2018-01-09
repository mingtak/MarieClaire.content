# -*- coding: utf-8 -*- 
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone import api
import datetime
from DateTime import DateTime
import logging
import json
from MarieClaire.content import DBSTR
from sqlalchemy import create_engine
from cStringIO import StringIO
import csv
from plone.protect.interfaces import IDisableCSRFProtection
from zope.interface import alsoProvides

logger = logging.getLogger('MarieClaire.content')
LIMIT=20
ENGINE = create_engine(DBSTR, echo=True)

class UpdateCustom(BrowserView):

    def __call__(self):
        context = self.context
        request = self.request
        portal = api.portal.get()
        alsoProvides(request, IDisableCSRFProtection)

        if api.user.is_anonymous():
            request.response.redirect(portal.absolute_url())
            return

        if 'form.widgets.ownerList' in request.form:
            context.ownerList = request.form['form.widgets.ownerList']
        if 'form.widgets.postList' in request.form:
            context.postList = request.form['form.widgets.postList']
        if 'form.widgets.tableList' in request.form:
            context.tableList = request.form['form.widgets.tableList']

        request.response.redirect('%s/manage_list' % portal.absolute_url())
        return


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


class UpdateWeight(ManaBasic):

    def __call__(self):
        if self.isAnonymous():
            return
        
        request = self.request
        update_type = request.form.get('update_type')
        update_id = request.form.get('update_id')
        weight_name = request.form.get('weight_name')
        weight = request.form.get('weight')

        if update_type == 'order':
            execStr = """\
                UPDATE dfp_ad_server
                SET {} = {} WHERE ORDER_ID = '{}'""".format(weight_name, weight, update_id)
        else:
            execStr = """UPDATE dfp_ad_server SET {} = {} 
                WHERE LINE_ITEM_ID = '{}'""".format(weight_name, weight, update_id)
        self.execSql(execStr)
        return weight

class UpdateEst(ManaBasic):
    def __call__(self):
        update_id = self.request.form.get('update_id')
        est_name = self.request.form.get('est_name')
        value = self.request.form.get('value')
        update_type = self.request.form.get('update_type')

        if update_type == 'Est_weight':
            execStr = """UPDATE dfp_line_item SET {} = {} WHERE ORDER_ID = '{}'
                """.format(est_name, value, update_id)
        else:
            execStr = """UPDATE dfp_line_item SET {} = {} WHERE 
                LINE_ITEM_ID = '{}' """.format(est_name, value, update_id)

        self.execSql(execStr)
        return value


class UpdateDateData(ManaBasic):
    def __call__(self):
        update_name = self.request.form.get('update_name')
        line_item_id = self.request.form.get('line_item_id')
        value = self.request.form.get('value')
        date = self.request.form.get('date')
        execStr = """UPDATE dfp_ad_server SET {} = {} WHERE LINE_ITEM_ID = '{}' AND 
        date = '{}' """.format(update_name, value, line_item_id, date)
        self.execSql(execStr)
        return value


class ManaCustomList(ManaBasic):
    template = ViewPageTemplateFile('template/mana_custom_list.pt')
    def getCustomList(self):
        current = api.user.get_current().getUserName()
        brains = api.content.find(Type='Custom', sort_on='created', sort_order='reverse')
        result = []
        for brain in brains:
            item = brain.getObject()
            item_ownerList = item.ownerList
            if item_ownerList != None:
                ownerList = item_ownerList.split('\r\n')
                for owner in ownerList:
                    if current == owner:
                        result.append({
                            'title': item.title,
                            'url':brain.getURL()
                        })
        return result

    def __call__(self):
        if self.isAnonymous():
            return
        return self.template()


class CustomReport(ManaBasic):
    template = ViewPageTemplateFile('template/custom_report.pt')
    def checkUser(self):
        current = api.user.get_current().getUserName()
        brain = api.content.find(context=self.context)
        if current == 'admin':
            return True
        else:
            if brain[0].getObject().ownerList == None:
                return False
            else:
                ownerList = brain[0].getObject().ownerList.split('\r\n')
                for owner in ownerList:
                    if owner == current:
                        return True
                    else:
                        return False

    def getOrder(self):
        id = self.context.id
        execStr = "SELECT * FROM dfp_order WHERE ADVERTISER_ID = '%s'" % id 
        return self.execSql(execStr)

    def getLineItem(self, order_id):
        execStr = "SELECT * FROM dfp_line_item WHERE ORDER_ID = '{}'".format(order_id)
        return self.execSql(execStr)

    def __call__(self):
        if self.isAnonymous():
            return

        return self.template()


class DownloadFile(ManaBasic):
    def __call__(self):
        request = self.request
        checkList = request.form.get('checkList[]')
        startDate = request.form.get('start')
        endDate = request.form.get('end')
        line_item_data = checkList.split(',')
        line_item_list = []
        for i in range(0, len(line_item_data)):
            line_item_list.append(line_item_data[i])

        execStr = """\
            SELECT dfp_ad_server.*,dfp_line_item.LINE_ITEM_NAME FROM `dfp_ad_server`,`dfp_line_item` 
            WHERE dfp_ad_server.LINE_ITEM_ID IN {} 
            AND dfp_line_item.LINE_ITEM_ID = dfp_ad_server.LINE_ITEM_ID AND(DATE BETWEEN '{}'
            AND '{}') ORDER BY DATE""".format(tuple(line_item_list), startDate, endDate)
        download_data = self.execSql(execStr)
        self.request.response.setHeader('Content-Type', 'application/csv')
        self.request.response.setHeader('Content-Disposition', 'attachment; filename="results.csv"')
        output = StringIO()
        output.write(u'\uFEFF'.encode('utf-8'))
        writer = csv.writer(output)
        writer.writerow(['名稱', '日期', '點擊數', '曝光數', '點擊率(%)'])
        
        for data in download_data:
            tmp = dict(data)
            writer.writerow([
                tmp['LINE_ITEM_NAME'],
                tmp['DATE'].strftime('%Y-%m-%d'),
                tmp['AD_SERVER_CLICKS'],
                tmp['AD_SERVER_IMPRESSIONS'],
                tmp['AD_SERVER_CTR']*100,
            ])
        results = output.getvalue()
        output.close()
        return results


class CustomEdit(ManaBasic):
    template = ViewPageTemplateFile('template/custom_edit.pt')

    def checkUser(self):
        current = api.user.get_current().getUserName()
        brain = api.content.find(context=self.context)
        if current == 'admin':
            return True
        else:
            if brain[0].getObject().ownerList == None:
                return False
            else:
                ownerList = brain[0].getObject().ownerList.split('\r\n')
                for owner in ownerList:
                    if owner == current:
                        return True
                    else:
                        return False

    def getOrderList(self):
        id = self.context.id
        execStr = """\
            SELECT dfp_ad_server.*, dfp_order.ORDER_NAME
            FROM dfp_ad_server, dfp_order
            WHERE dfp_order.ORDER_ID = dfp_ad_server.ORDER_ID
                  and dfp_ad_server.ADVERTISER_ID = '{}'
            ORDER BY DATE""".format(id)
        return self.execSql(execStr)
    def getLineItem(self, order_id):
        execStr = """SELECT dfp_ad_server.*,dfp_line_item.LINE_ITEM_NAME 
        FROM dfp_ad_server,dfp_line_item WHERE dfp_ad_server.ORDER_ID='{}' 
        and dfp_ad_server.LINE_ITEM_ID=dfp_line_item.LINE_ITEM_ID""".format(order_id)
        lineItemList = self.execSql(execStr)
        
        lineItemData = {}
        for item in lineItemList:
            tmp = dict(item)
            Est_dict = self.getEst(tmp['LINE_ITEM_ID'])
            if lineItemData.has_key(tmp['LINE_ITEM_ID']):
                lineItemData[tmp['LINE_ITEM_ID']]['AD_SERVER_IMPRESSIONS']+=tmp['AD_SERVER_IMPRESSIONS']
                lineItemData[tmp['LINE_ITEM_ID']]['AD_SERVER_CLICKS']+=tmp['AD_SERVER_CLICKS']
            else:
                lineItemData[tmp['LINE_ITEM_ID']]={
                    'LINE_ITEM_NAME' : tmp['LINE_ITEM_NAME'],
                    'AD_SERVER_IMPRESSIONS' : tmp['AD_SERVER_IMPRESSIONS'],
                    'AD_SERVER_CLICKS' : tmp['AD_SERVER_CLICKS'],
                    'im_weight' : tmp['im_weight'],
                    'cli_weight' : tmp['cli_weight'],
                    'EstImp' : Est_dict['EstImp'],
                    'EstCTR' : Est_dict['EstCTR'],
                }
        return lineItemData

    def getEst(self, line_item_id):
        execStr = """SELECT EstImp,EstCTR FROM dfp_line_item WHERE LINE_ITEM_ID = 
            '{}'""".format(line_item_id)
        return dict(self.execSql(execStr)[0])
    
    def get_date_data(self, line_item_id):
        
        execStr = """SELECT dfp_ad_server.* FROM dfp_ad_server WHERE LINE_ITEM_ID = '{}' 
            ORDER BY DATE""".format(line_item_id)
        result_data = self.execSql(execStr)
        date_data = {}        
        for data in result_data:
            tmp = dict(data)
            date = str(tmp['DATE'])
            impressions = tmp['AD_SERVER_IMPRESSIONS']
            click = tmp['AD_SERVER_CLICKS']
            ctr = '%s %%' %round((float(click)/float(impressions)*100),2)
            date_data[date] = {
                'impressions':impressions,
                'clicks':click,
                'ctr':ctr,
                'cli_weight':tmp['cli_weight'],
                'im_weight':tmp['im_weight'],
            }
        return date_data 

    def get_date_list(self, line_item_id):
        execStr = """SELECT date FROM dfp_ad_server WHERE LINE_ITEM_ID = '{}'
        ORDER BY DATE""".format(line_item_id)
        result = self.execSql(execStr)
        date_list = []
        for item in result:
            tmp = dict(item)
            date_list.append(str(tmp['date']))
        return date_list

    def __call__(self):
        if self.isAnonymous():
            return
        
        orderList = self.getOrderList()
        orderIds = []
        orderData = {}
        for item in orderList:
            tmp = dict(item)
            if tmp['ORDER_ID'] not in orderIds:
                orderIds.append(tmp['ORDER_ID'])
            if not orderData.has_key(tmp['ORDER_ID']):
                orderData[tmp['ORDER_ID']] = {
                    'ORDER_NAME': tmp['ORDER_NAME'],
                    'AD_SERVER_IMPRESSIONS': tmp['AD_SERVER_IMPRESSIONS'],
                    'AD_SERVER_CLICKS': tmp['AD_SERVER_CLICKS'],
                    'im_weight': tmp['im_weight'],
                    'cli_weight': tmp['cli_weight'],
                }
            else:
                orderData[tmp['ORDER_ID']]['AD_SERVER_IMPRESSIONS'] += tmp['AD_SERVER_IMPRESSIONS']
                orderData[tmp['ORDER_ID']]['AD_SERVER_CLICKS'] += tmp['AD_SERVER_CLICKS']

        self.orderIds = orderIds
        self.orderData = orderData

        return self.template()


class GetDfpReport(ManaBasic):

    def __call__(self):

        if self.isAnonymous():
            return
        context = self.context
        request = self.request
        checkList = request.form.get('checkList[]')
        startDate = request.form.get('start')
        endDate = request.form.get('end')
        select_type = request.form.get('select_type')

        if checkList is None:
            return json.dumps([{}, {}])

        if type(checkList) == str:
            checkList = [checkList, 'zzzzz'] # tuple在單筆資料時最後面會出現逗號，sql查詢會出錯，所以加一筆'zzzz'避開
        
        execStr = """\
            SELECT dfp_ad_server.*,dfp_line_item.LINE_ITEM_NAME FROM `dfp_ad_server`,`dfp_line_item` 
            WHERE dfp_ad_server.LINE_ITEM_ID IN {} 
            AND dfp_line_item.LINE_ITEM_ID = dfp_ad_server.LINE_ITEM_ID AND(DATE BETWEEN '{}'
            AND '{}') ORDER BY DATE""".format(tuple(checkList), startDate, endDate)
        result = self.execSql(execStr)
        toList = []
        for item in result:
            tmp = dict(item)
            tmp['DATE'] = str(tmp['DATE'])
            toList.append(tmp)
        drawData = {}
        xs = {}
        for item in toList:
            line_item_id = item['LINE_ITEM_ID']
            Date = item['DATE']
            # 以下配合c3.js產出對應格式
            # 是否有order
            if select_type == 'nav_pie':
                execStr = """SELECT date FROM dfp_ad_server WHERE LINE_ITEM_ID = '{}' AND 
                    DATE BETWEEN '{}' AND '{}' """.format(line_item_id, startDate, endDate)
                days = len(self.execSql(execStr))
                if drawData.has_key(line_item_id):
                    if Date == drawData[line_item_id][0][-1]:
                        drawData[line_item_id][1][-1] += float(item['AD_SERVER_IMPRESSIONS']*item['im_weight']/days)
                        drawData[line_item_id][2][-1] += float(item['AD_SERVER_CLICKS']*item['cli_weight']/days)
                    else:
                        drawData[line_item_id][0].append(item['DATE'])
                        drawData[line_item_id][1].append( float(item['AD_SERVER_IMPRESSIONS']*item['im_weight']/days) )
                        drawData[line_item_id][2].append( float(item['AD_SERVER_CLICKS']*item['cli_weight']/days) )
                else:
                    xs['%s 曝光量' % item['LINE_ITEM_NAME']] = str(item['LINE_ITEM_ID'])
                    xs['%s 點擊量' % item['LINE_ITEM_NAME']] = str(item['LINE_ITEM_ID'])
                    drawData[line_item_id] = [
                        [str(item['LINE_ITEM_ID']), item['DATE']],
                        ['%s 曝光量' % item['LINE_ITEM_NAME'], float(item['AD_SERVER_IMPRESSIONS']*item['im_weight']/days) ],
                        ['%s 點擊量' % item['LINE_ITEM_NAME'], float(item['AD_SERVER_CLICKS']*item['cli_weight']/days) ],
                    ]
            else:
                if drawData.has_key(line_item_id):
                    if Date == drawData[line_item_id][0][-1]:
                        drawData[line_item_id][1][-1] += int(item['AD_SERVER_IMPRESSIONS']*item['im_weight'])
                        drawData[line_item_id][2][-1] += int(item['AD_SERVER_CLICKS']*item['cli_weight'])
                        drawData[line_item_id][3][-1] = round(float(drawData[line_item_id][2][-1]) / float(drawData[line_item_id][1][-1]), 1)
                    else:
                        drawData[line_item_id][0].append(item['DATE'])
                        drawData[line_item_id][1].append( int(item['AD_SERVER_IMPRESSIONS']*item['im_weight']) )
                        drawData[line_item_id][2].append( int(item['AD_SERVER_CLICKS']*item['cli_weight']) )
                        drawData[line_item_id][3].append(round(float(drawData[line_item_id][2][-1]) / float(drawData[line_item_id][1][-1])*100, 1))
                else:
                    xs['%s 曝光量' % item['LINE_ITEM_NAME']] = str(item['LINE_ITEM_ID'])
                    xs['%s 點擊量' % item['LINE_ITEM_NAME']] = str(item['LINE_ITEM_ID'])
                    xs['%s CTR%s' % (item['LINE_ITEM_NAME'], '(%)') ] = str(item['LINE_ITEM_ID'])
                    drawData[line_item_id] = [
                        [str(item['LINE_ITEM_ID']), item['DATE']],
                        ['%s 曝光量' % item['LINE_ITEM_NAME'], int(item['AD_SERVER_IMPRESSIONS']*item['im_weight']) ],
                        ['%s 點擊量' % item['LINE_ITEM_NAME'], int(item['AD_SERVER_CLICKS']*item['cli_weight']) ],
                        ['%s CTR%s' % (item['LINE_ITEM_NAME'], '(%)'),
                    ( round( (float(item['AD_SERVER_CLICKS'])*item['cli_weight'])/(float(item['AD_SERVER_IMPRESSIONS'])*item['im_weight'])*100 , 1) )],
                    ]

        return json.dumps([xs, drawData])


class DelLineItem(ManaBasic):

    def __call__(self):
        checkList = self.request.form.get('check_list[]')
        time = self.request.form.get('time')

        if type(checkList) == str:
            checkList = [checkList, 'zzzzz']
        execStr = """DELETE FROM dfp_ad_server WHERE LINE_ITEM_ID IN {} 
        AND DATE = '{}' """.format(tuple(checkList), time)
        self.execSql(execStr)

class GetDfpTable(ManaBasic):
    template = ViewPageTemplateFile('template/custom_table.pt')
    def __call__(self):

        request = self.request
        select_type = request.form.get('select_type')
        checkList = request.form.get('checkList[]')
        startDate = request.form.get('start')
        endDate = request.form.get('end')
        if type(checkList) == str:
            checkList = [checkList, 'zzzzz']

        if select_type == 'nav_table':
            execStr = """\
                SELECT dfp_ad_server.*,dfp_line_item.LINE_ITEM_NAME,dfp_line_item.EstImp
                ,dfp_line_item.EstCTR FROM `dfp_ad_server`,`dfp_line_item` 
                WHERE dfp_ad_server.LINE_ITEM_ID IN {} 
                AND dfp_line_item.LINE_ITEM_ID = dfp_ad_server.LINE_ITEM_ID 
                ORDER BY DATE""".format(tuple(checkList))
            result = self.execSql(execStr)
            tableData = {}
            delivery_imp = 0
            delivery_clk = 0
            for item in result:
                tmp = dict(item)
                line_item_id = tmp['LINE_ITEM_ID']
                Date = str(tmp['DATE'])
                line_item_name = str(tmp['LINE_ITEM_NAME'])
                cli_weight = tmp['cli_weight']
                im_weight = tmp['im_weight']
                if tableData.has_key(line_item_id):
                        tableData[line_item_id][1][-1] += round(tmp['AD_SERVER_IMPRESSIONS']*im_weight,0)
                        tableData[line_item_id][2][-1] += round(tmp['AD_SERVER_CLICKS']*cli_weight,0)
                else:
                    tableData[line_item_id] = [
                        [line_item_name.split('_')[0],line_item_name.split('_')[1],line_item_name.split('_')[2]],
                        [round(tmp['AD_SERVER_IMPRESSIONS']*im_weight,0)],
                        [round(tmp['AD_SERVER_CLICKS']*cli_weight,0)],
                        [tmp['AD_SERVER_CTR']],#這沒用到，再template另外計算
                        [tmp['EstImp']],
                        [tmp['EstCTR']]
                    ]
                # 計算總數
                delivery_imp += round(tmp['AD_SERVER_IMPRESSIONS']*im_weight,0)
                delivery_clk += round(tmp['AD_SERVER_CLICKS']*cli_weight,0)
            self.delivery_imp = int(delivery_imp)
            self.delivery_clk = int(delivery_clk)
            self.delivery_ctr = '%s %%' %(round( (float(delivery_clk) / float(delivery_imp) *100), 2))
            self.tableData = tableData

            execStr = """SELECT EstImp,EstCTR FROM dfp_line_item WHERE LINE_ITEM_ID IN {}
                """.format(tuple(checkList))
            result_est = self.execSql(execStr)
            # 預期目標的總數
            sum_Est_imp = 0
            sum_Est_clk = 0
            for item in result_est:
                tmp = dict(item)
                imp = int(tmp['EstImp'])
                ctr = float(tmp['EstCTR'])
                sum_Est_imp += imp
                sum_Est_clk += int(imp*ctr/100)
            self.Est_imp = sum_Est_imp
            self.Est_clk = sum_Est_clk
            self.Est_ctr = round(float(self.Est_clk / self.Est_imp *100),2)

        elif select_type == 'nav_detail':
            # 抓兩日的差距
            execStr = """SELECT MIN(DATE),MAX(DATE) FROM dfp_ad_server WHERE
                LINE_ITEM_ID IN {} """.format(tuple(checkList))
            day_result = self.execSql(execStr)
            min_day = dict(day_result[0])['MIN(DATE)']
            max_day = dict(day_result[0])['MAX(DATE)']
            days = (max_day - min_day).total_seconds()/60/60/24
            day_list = []
            for i in range(0, int(days)+1):
                day = str(min_day + datetime.timedelta(days=i))
                day_list.append(day)

            self.day_list = day_list
            # 抓title
            execStr = """SELECT LINE_ITEM_NAME FROM dfp_line_item WHERE LINE_ITEM_ID 
                IN {}""".format(tuple(checkList))
            result_day_title = self.execSql(execStr)
            day_title = []
            for title in result_day_title:
                tmp = dict(title)
                day_title.append(tmp['LINE_ITEM_NAME'])
            self.day_title = day_title

            # 抓line_item的data
            result_day_data = {}
            sum_oneday_data = {}
            for checked in checkList:
                execStr = """SELECT AD_SERVER_IMPRESSIONS,AD_SERVER_CLICKS,DATE,LINE_ITEM_ID 
                    ,im_weight,cli_weight FROM `dfp_ad_server` WHERE LINE_ITEM_ID = '{}' 
                    ORDER BY DATE
                    """.format(checked)
                result = self.execSql(execStr)
                tmp_dayList = list(day_list)
                for item in result:
                    tmp = dict(item)
                    date = str(tmp['DATE'])
                    impressions = round(tmp['AD_SERVER_IMPRESSIONS']*tmp['im_weight'], 0)
                    clicks = round(tmp['AD_SERVER_CLICKS']*tmp['cli_weight'], 0)
                    ctr = round(float(clicks) / float(impressions)*100,2)
                    if result_day_data.has_key(date):
                        result_day_data[date].append(int(impressions))
                        result_day_data[date].append(int(clicks))
                        result_day_data[date].append('%s %%' %ctr)
                    else:
                        result_day_data[date] = [int(impressions), int(clicks), '%s %%' %ctr]
                    # 算一天總合
                    if sum_oneday_data.has_key(date):
                        sum_oneday_data[date][0] += int(impressions)
                        sum_oneday_data[date][1] += int(clicks)
                    else:
                        sum_oneday_data[date] = [int(impressions), int(clicks)]
                    # 若那天有資料填入就刪掉那天日期    
                    tmp_dayList.remove(date) 
                # 把剩餘的日期填空
                for tmp_day in tmp_dayList:
                    if result_day_data.has_key(tmp_day):
                        result_day_data[tmp_day].append('')
                        result_day_data[tmp_day].append('')
                        result_day_data[tmp_day].append('')
                    else:
                        result_day_data[tmp_day] = ['', '', '']
                    if sum_oneday_data.has_key(tmp_day):
                        pass
                    else:
                        sum_oneday_data[tmp_day] = [0,0]

            self.sum_oneday_data = sum_oneday_data
            self.result_day_data = result_day_data
            
            # 抓預期目標
            oneday_EstImp = 0
            oneday_EstClk = 0
            execStr = """SELECT EstImp,EstCTR FROM dfp_line_item WHERE LINE_ITEM_ID 
                IN {}""".format(tuple(checkList))
            result_est = self.execSql(execStr)
            estList = []
            for est in result_est:
                tmp = dict(est)
                click = int(round(float(tmp['EstImp'])*float(tmp['EstCTR'])/100,0))
                estList.append(tmp['EstImp'])
                estList.append(click)
                estList.append('%s %%' %tmp['EstCTR'])
                oneday_EstImp += int(tmp["EstImp"])
                oneday_EstClk += click
            oneday_ctr = '%s %%'%(round(float(oneday_EstClk) / float(oneday_EstImp)*100,2))
            self.est = estList
            self.oneday_EstImp = oneday_EstImp
            self.oneday_EstClk = oneday_EstClk
            self.oneday_ctr = oneday_ctr
            # 抓最後達成結果
            result_sum_list = []
            reaching_rate_list = []
            total_reaching_imp = 0
            total_reaching_cli = 0
            
            for checked in checkList:
                sum_imp = 0
                sum_click = 0
                # 單個LINE_ITEM_ID 的資料
                execStr = """SELECT AD_SERVER_IMPRESSIONS,AD_SERVER_CLICKS,im_weight
                    ,cli_weight FROM `dfp_ad_server` WHERE LINE_ITEM_ID = '{}'
                    """.format(checked)
                result_sum = self.execSql(execStr)
                if result_sum != []:#單選一個會多跑一次空值
                    for item in result_sum:
                        tmp = dict(item)
                        sum_imp += round((int(tmp['AD_SERVER_IMPRESSIONS'])*tmp['im_weight']),0)
                        sum_click += round((int(tmp['AD_SERVER_CLICKS'])*tmp['cli_weight']),0)
                    ctr = round(float(sum_click)/float(sum_imp)*100, 2)
                    result_sum_list.append(int(sum_imp))
                    result_sum_list.append(int(sum_click))
                    result_sum_list.append('%s %%' %ctr)
                    total_reaching_imp += int(sum_imp)
                    total_reaching_cli += int(sum_click)
                    total_reaching_ctr = '%s %%'%(round(float(total_reaching_cli) / float(total_reaching_imp)*100,2))
                self.total_reaching_imp = total_reaching_imp
                self.total_reaching_cli = total_reaching_cli
                self.total_reaching_ctr = total_reaching_ctr
                execStr = """SELECT EstImp FROM dfp_line_item WHERE LINE_ITEM_ID = '{}'
                    """.format(checked)
                result_estimp = self.execSql(execStr)
                if result_estimp != []:#單選一個會多跑一次空值
                    for item in result_estimp:
                        tmp = dict(item)
                        est_imp = tmp['EstImp']
                        reaching_rate ='%s %%' %(round(sum_imp / int(est_imp)*100, 2))
                        reaching_rate_list.append(reaching_rate)
            sum_reaching_rate = 0
            for rate in reaching_rate_list:
                sum_reaching_rate += float(rate.split('%')[0])
            self.sum_reaching_rate = '%s %%' %(round(sum_reaching_rate / len(reaching_rate_list), 2))
            self.reaching_rate_list = reaching_rate_list
            self.sum_list = result_sum_list
        # 判斷點擊
        if select_type == 'nav_table':
            self.select_table = True
            self.select_detail = False
        else:
            self.select_detail = True
            self.select_table = False

        return self.template()


class CustomValue(BrowserView):
    template = ViewPageTemplateFile('template/custom_value.pt')
    def checkUser(self):
        current = api.user.get_current().getUserName()
        brain = api.content.find(context=self.context)
        if current == 'admin':
            return True
        else:
            if brain[0].getObject().ownerList == None:
                return False
            else:
                ownerList = brain[0].getObject().ownerList.split('\r\n')
                if current in ownerList:
                    return True
                else:
                    return False

    def __call__(self):
        return self.template()


class IsManager(BrowserView):

    def __call__(self):
        return 'Manager' in api.user.get_roles()


""" 尚未使用
class ManaCustomAdd(ManaBasic):
    template = ViewPageTemplateFile('template/mana_custom_add.pt')
    def __call__(self):
        if self.isAnonymous():
            return

        return self.template()

"""


