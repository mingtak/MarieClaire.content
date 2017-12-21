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
        return 'Already Update OK.'

class UpdateEst(ManaBasic):
    def __call__(self):
        update_id = self.request.form.get('update_id')
        est_name = self.request.form.get('est_name')
        value = self.request.form.get('value')
        execStr = """UPDATE dfp_line_item SET {} = {} WHERE 
            LINE_ITEM_ID = '{}' """.format(est_name, value, update_id)
        self.execSql(execStr)
        return 'Already Update OK.'

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
    def __call__(self):
        return 


""" 尚未使用
class ManaCustomAdd(ManaBasic):
    template = ViewPageTemplateFile('template/mana_custom_add.pt')
    def __call__(self):
        if self.isAnonymous():
            return

        return self.template()

"""
