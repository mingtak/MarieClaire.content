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
reload(sys)
sys.setdefaultencoding('utf-8')

class Manage_list(BrowserView):
    template = ViewPageTemplateFile('template/manage_list.pt')
    def __call__(self):
        return self.template()


class Welcome(BrowserView):
    template = ViewPageTemplateFile('template/welcome.pt')
    def __call__(self):
        return self.template()


class Event_list(BrowserView):
    template = ViewPageTemplateFile('template/event_list.pt')
    
    def get_event_data(self):
        portal = api.portal.get()
        brains = api.content.find(
            context=api.portal.get(), portal_type='Event', sort_on='created', 
                        sort_order='reverse')
        return brains

    def __call__(self):
        return self.template()


class Custom_list(BrowserView):
    template = ViewPageTemplateFile('template/custom_list.pt')
    
    def get_custom_data(self):
        portal = api.portal.get()
        brains = api.content.find(
            context=api.portal.get(), portal_type='Custom', sort_on='created', 
                        sort_order='reverse')
        
        return brains

    def get_ads_list(self, brain):
        ads_list = []

        item = brain.getObject()
        for ads in item.advertisement:
            ads_list.append(ads.to_path.split('/')[2])
        ads_list = ",".join(str(x) for x in ads_list)

        return ads_list
    
    def get_post_list(self, brain):
        item = brain.getObject()
        
        title = item.post.to_object.title
        web_site = item.post.to_object.web_site

        post_list = []
        post_list.append(title)
        post_list.append(web_site)

        return post_list

    def __call__(self):
        return self.template()


class Ads_list(BrowserView):
    template = ViewPageTemplateFile('template/ads_list.pt')
    
    def get_ads_data(self):
        portal = api.portal.get()
        brains = api.content.find(
            context=api.portal.get(), portal_type='Advertisement', sort_on='created', 
                        sort_order='reverse')
        return brains

    def __call__(self):
        return self.template()


class Add_event(BrowserView):
    def get_uid(self, item):
        portal = api.portal.get()
        contact = portal[item.getId]
        uid = api.content.get_uuid(obj=contact)
        return uid

    def __call__(self):
        goto = self.request.get('goto')
        url = 'template/{}.pt'.format(goto)

        template = ViewPageTemplateFile(url)

        return template(self)


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


class Do_add_content(BrowserView):
    def __call__(self):
        which_from = self.request.get('which_from')
        portal = api.portal.get()
        url = portal.absolute_url()

        if which_from == 'event_list':
            title = self.request.get('event_title')
            description = self.request.get('event_desc')
            start_date = self.request.get('event_start_date')
            end_date = self.request.get('event_end_date')
            start_time = self.request.get('start_time')
            end_time = self.request.get('end_time')

            start_date = start_date+' '+start_time
            end_date = end_date+' '+end_time

            sd = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M')
            ed = datetime.datetime.strptime(end_date, '%Y-%m-%d  %H:%M')

            obj = api.content.create(
            type='Event',
            title=title,
            start=sd,
            end=ed,
            description=description,
            container=portal)

        elif which_from == 'ads_list':

            title = self.request.get('ads_title')
            content = self.request.get('ads_content')
            weighted = float(self.request.get('ads_weighted'))

            obj = api.content.create(
            type='Advertisement',
            title=title,
            content=content,
            weighted=weighted,
            container=portal)
        elif which_from == 'custom_list':
            title = self.request.get('custom_title')
            ads = self.request.get('ads')
            web_site = self.request.get('web_site')
            intIds = component.getUtility(IIntIds)

            if type(ads) == str:
                one_ads = []
                one_ads.append(ads)

            website_list = []

            obj_website = api.content.find(UID=web_site)[0].getObject()
            if obj_website:
                obj_website = obj_website[0].getObject()
            website_list.append(RelationValue(intIds.getId(obj_website)))
            
            relation_list = []
            try:
                obj_ad = api.content.find(UID=one_ads[0])[0].getObject()
                relation_list.append(RelationValue(intIds.getId(obj_ad)))
            except:
                for ad in ads:
                    obj_ad = api.content.find(UID=ad)[0].getObject()
                    relation_list.append(RelationValue(intIds.getId(obj_ad)))
            
            obj = api.content.create(
            type='Custom',
            title=title,
            advertisement=relation_list,
            post=RelationValue(intIds.getId(obj_website)),
            container=portal)
        elif which_from == 'post_list':
            title = self.request.get('post_title')
            web_site = self.request.get('post_website')

            obj = api.content.create(
            type='Post',
            title=title,
            web_site=web_site,
            container=portal)

        self.request.response.redirect('{}/{}'.format(url, which_from))


class Delete_content(BrowserView):
    def __call__(self):
        event_id = self.request.get('event_id')
        backto = self.request.get('from')
        portal = api.portal.get()
        url = portal.absolute_url()

        api.content.delete(obj=portal[event_id])
        self.request.response.redirect('{}/{}'.format(url, backto))

