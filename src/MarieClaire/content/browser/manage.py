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


"""
class ManaCustomAdd(ManaBasic):
    template = ViewPageTemplateFile('template/mana_custom_add.pt')
    def __call__(self):
        if self.isAnonymous():
            return

        return self.template()

"""

