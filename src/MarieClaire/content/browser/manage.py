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

    def __call__(self):
        if self.isAnonymous():
            return

        return self.template()


class GetDfpReport(ManaBasic):
#    template = ViewPageTemplateFile('template/custom_report.pt')

    def __call__(self):

        if self.isAnonymous():
            return
        context = self.context
        request = self.request
        orderList = request.form['orderList[]']

        execStr = """\
            SELECT dfp_ad_server.*, dfp_order.ORDER_NAME
            FROM dfp_ad_server, dfp_order
            WHERE dfp_order.ORDER_ID = dfp_ad_server.ORDER_ID
                  and dfp_order.ORDER_ID IN {}
            ORDER BY DATE""".format(tuple(orderList))

        result = self.execSql(execStr)
        toList = []
        for item in result:
            tmp = dict(item)
            tmp['DATE'] = str(tmp['DATE'])
            toList.append(tmp)

        drawData = {}
        xs = {}
        for item in toList:
            orderId = item['ORDER_ID']
            orderDate = item['DATE']

            # 以下配合c3.js產出對應格式
            # 是否有order
            if drawData.has_key(orderId):
                if orderDate == drawData[orderId][0][-1]:
                    drawData[orderId][1][-1] += item['AD_SERVER_IMPRESSIONS']
                    drawData[orderId][2][-1] += item['AD_SERVER_CLICKS']
                    drawData[orderId][3][-1] = round(float(drawData[orderId][2][-1]) / float(drawData[orderId][1][-1]), 6)
                else:
                    drawData[orderId][0].append(item['DATE'])
                    drawData[orderId][1].append(item['AD_SERVER_IMPRESSIONS'])
                    drawData[orderId][2].append(item['AD_SERVER_CLICKS'])
                    drawData[orderId][3].append(round(float(drawData[orderId][2][-1]) / float(drawData[orderId][1][-1]), 6))
            else:
                xs['%s 曝光量' % item['ORDER_NAME']] = str(item['ORDER_ID'])
                xs['%s 點擊量' % item['ORDER_NAME']] = str(item['ORDER_ID'])
                xs['%s CTR' % item['ORDER_NAME']] = str(item['ORDER_ID'])
                drawData[orderId] = [
                    [str(item['ORDER_ID']), item['DATE']],
                    ['%s 曝光量' % item['ORDER_NAME'], item['AD_SERVER_IMPRESSIONS'] ],
                    ['%s 點擊量' % item['ORDER_NAME'], item['AD_SERVER_CLICKS']],
                    ['%s CTR' % item['ORDER_NAME'], ( round(float(item['AD_SERVER_CLICKS']) / float(item['AD_SERVER_IMPRESSIONS']), 6) )],
                ]


        return json.dumps([xs, drawData])

"""
class ManaCustomAdd(ManaBasic):
    template = ViewPageTemplateFile('template/mana_custom_add.pt')
    def __call__(self):
        if self.isAnonymous():
            return

        return self.template()

"""

