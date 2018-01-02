from plone import api
#from zExceptions import Redirect
def modifyCustom(item, event):
    portal = api.portal.get()
    request = item.REQUEST
    request.response.redirect('/')
    #import pdb; pdb.set_trace()
#    returnc