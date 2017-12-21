# -*- coding: utf-8 -*- 
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone import api
from z3c.relationfield import RelationValue
from zope.app.intid.interfaces import IIntIds
from zope import component
import datetime
import time
import sys
import argparse

import googleapiclient
from apiclient.discovery import build
import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools
reload(sys)
sys.setdefaultencoding('utf-8')


class Post_list(BrowserView):
    template = ViewPageTemplateFile('template/post_list.pt')
    
    def get_post_data(self):
        portal = api.portal.get()
        brains = api.content.find(
            context=api.portal.get(), portal_type='Post', sort_on='created', 
                        sort_order='reverse')
        return brains

    def __call__(self):
        return self.template()


