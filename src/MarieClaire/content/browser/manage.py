# -*- coding: utf-8 -*- 
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone import api
#from z3c.relationfield import RelationValue
#from zope.app.intid.interfaces import IIntIds
#from zope import component
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


class ManaCustomList(ManaBasic):
    template = ViewPageTemplateFile('template/mana_custom_list.pt')

    def __call__(self):
        if self.isAnonymous():
            return
        self.brain = api.content.find(Type='Custom', sort_on='created', sort_order='reverse')
        return self.template()


class CustomReport(ManaBasic):
    template = ViewPageTemplateFile('template/custom_report.pt')

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
        orderList = request.form.get('orderList[]')
        startDate = request.form.get('start')
        endDate = request.form.get('end')
        order_data = orderList.split(',')
        order_data_list = []
        for i in range(0, len(order_data)):
            order_data_list.append(order_data[i])

        # if type(orderList) == str:
        #     orderList = [orderList, 'zzzzz'] # tuple在單筆資料時最後面會出現逗號，sql查詢會出錯，所以加一筆'zzzz'避開
        execStr = """\
            SELECT dfp_ad_server.*,dfp_line_item.LINE_ITEM_NAME FROM `dfp_ad_server`,`dfp_line_item` 
            WHERE dfp_ad_server.LINE_ITEM_ID IN {} 
            AND dfp_line_item.LINE_ITEM_ID = dfp_ad_server.LINE_ITEM_ID AND(DATE BETWEEN '{}'
            AND '{}') ORDER BY DATE""".format(tuple(order_data_list), startDate, endDate)
        download_data = self.execSql(execStr)
        self.request.response.setHeader('Content-Type', 'application/csv')
        self.request.response.setHeader('Content-Disposition', 'attachment; filename="results.csv"')
        output = StringIO()
        output.write(u'\uFEFF'.encode('utf-8'))
        writer = csv.writer(output)
        writer.writerow(['名稱', '點擊數', '曝光數', '點擊率(%)', '日期', '點擊權重', '曝光權重'])
        
        for data in download_data:
            tmp = dict(data)
            writer.writerow([
                tmp['LINE_ITEM_NAME'],
                tmp['AD_SERVER_CLICKS'],
                tmp['AD_SERVER_IMPRESSIONS'],
                tmp['AD_SERVER_CTR']*100,
                tmp['DATE'].strftime('%Y-%m-%d'),
                tmp['cli_weight'],
                tmp['im_weight']
            ])
        results = output.getvalue()
        output.close()
        return results


class CustomEdit(ManaBasic):
    template = ViewPageTemplateFile('template/custom_edit.pt')

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
        execStr ="""SELECT dfp_ad_server.*,dfp_line_item.LINE_ITEM_NAME 
        FROM dfp_ad_server,dfp_line_item WHERE dfp_ad_server.ORDER_ID='{}' 
        and dfp_ad_server.LINE_ITEM_ID=dfp_line_item.LINE_ITEM_ID""".format(order_id)
        lineItemList = self.execSql(execStr)

        lineItemData = {}
        for item in lineItemList:
            tmp = dict(item)
            if lineItemData.has_key(tmp['LINE_ITEM_ID']):
                lineItemData[tmp['LINE_ITEM_ID']]['AD_SERVER_IMPRESSIONS']+=tmp['AD_SERVER_IMPRESSIONS']
                lineItemData[tmp['LINE_ITEM_ID']]['AD_SERVER_CLICKS']+=tmp['AD_SERVER_CLICKS']
            else:
                lineItemData[tmp['LINE_ITEM_ID']]={
                    'LINE_ITEM_NAME' : tmp['LINE_ITEM_NAME'],
                    'AD_SERVER_IMPRESSIONS' : tmp['AD_SERVER_IMPRESSIONS'],
                    'AD_SERVER_CLICKS' : tmp['AD_SERVER_CLICKS'],
                    'im_weight' : tmp['im_weight'],
                    'cli_weight' : tmp['cli_weight']
                }
        return lineItemData

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
        orderList = request.form.get('orderList[]')
        startDate = request.form.get('start')
        endDate = request.form.get('end')

        if orderList is None:
            return json.dumps([{}, {}])

        if type(orderList) == str:
            orderList = [orderList, 'zzzzz'] # tuple在單筆資料時最後面會出現逗號，sql查詢會出錯，所以加一筆'zzzz'避開
        
        execStr = """\
            SELECT dfp_ad_server.*,dfp_line_item.LINE_ITEM_NAME FROM `dfp_ad_server`,`dfp_line_item` 
            WHERE dfp_ad_server.LINE_ITEM_ID IN {} 
            AND dfp_line_item.LINE_ITEM_ID = dfp_ad_server.LINE_ITEM_ID AND(DATE BETWEEN '{}'
            AND '{}') ORDER BY DATE""".format(tuple(orderList), startDate, endDate)
        result = self.execSql(execStr)
        toList = []
        for item in result:
            tmp = dict(item)
            tmp['DATE'] = str(tmp['DATE'])
            toList.append(tmp)
        drawData = {}
        xs = {}
        for item in toList:
            orderId = item['LINE_ITEM_ID']
            orderDate = item['DATE']
            # 以下配合c3.js產出對應格式
            # 是否有order
            if drawData.has_key(orderId):
                if orderDate == drawData[orderId][0][-1]:
                    drawData[orderId][1][-1] += int(item['AD_SERVER_IMPRESSIONS']*item['im_weight'])
                    drawData[orderId][2][-1] += int(item['AD_SERVER_CLICKS']*item['cli_weight'])
                    drawData[orderId][3][-1] = round(float(drawData[orderId][2][-1]) / float(drawData[orderId][1][-1]), 1)
                else:
                    drawData[orderId][0].append(item['DATE'])
                    drawData[orderId][1].append( int(item['AD_SERVER_IMPRESSIONS']*item['im_weight']) )
                    drawData[orderId][2].append( int(item['AD_SERVER_CLICKS']*item['cli_weight']) )
                    drawData[orderId][3].append(round(float(drawData[orderId][2][-1]) / float(drawData[orderId][1][-1])*100, 1))
            else:
                xs['%s 曝光量' % item['LINE_ITEM_NAME']] = str(item['LINE_ITEM_ID'])
                xs['%s 點擊量' % item['LINE_ITEM_NAME']] = str(item['LINE_ITEM_ID'])
                xs['%s CTR%s' % (item['LINE_ITEM_NAME'], '(%)') ] = str(item['LINE_ITEM_ID'])
                drawData[orderId] = [
                    [str(item['LINE_ITEM_ID']), item['DATE']],
                    ['%s 曝光量' % item['LINE_ITEM_NAME'], int(item['AD_SERVER_IMPRESSIONS']*item['im_weight']) ],
                    ['%s 點擊量' % item['LINE_ITEM_NAME'], int(item['AD_SERVER_CLICKS']*item['cli_weight']) ],
                    ['%s CTR%s' % (item['LINE_ITEM_NAME'], '(%)'),
 ( round( (float(item['AD_SERVER_CLICKS'])*item['cli_weight']) / (float(item['AD_SERVER_IMPRESSIONS'])*item['im_weight'])*100 , 1) )],
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

""" 尚未使用
class ManaCustomAdd(ManaBasic):
    template = ViewPageTemplateFile('template/mana_custom_add.pt')
    def __call__(self):
        if self.isAnonymous():
            return

        return self.template()

"""

