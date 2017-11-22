# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from MarieClaire.content import _
from zope import schema
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from z3c.relationfield.schema import RelationList, RelationChoice
from plone.app.vocabularies.catalog import CatalogSource



class IMarieclaireContentLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class ITask(Interface):

    title = schema.TextLine(
        title=_(u'Title'),
        required=True,
    )

    description = schema.Text(
        title=_(u'Description'),
        required=False,
    )


class ICustom(Interface):

    title = schema.TextLine(
        title=_(u'Name'),
        required=True,
    )
    advertisement = RelationList(
        title=_(u"Advertisement"),
        value_type=RelationChoice(title=_(u"Choice Advertisement"),
                                  source=CatalogSource(Type='Advertisement'),),
        required=False,
    )
    post = RelationChoice(
        title=_(u'Post'),
        source=CatalogSource(Type="Post"),
        required=True,
    )

class IAdvertisement(Interface):

    title = schema.TextLine(
        title=_(u'Name'),
        required=True,
    )
    content = schema.Text(
        title=_(u'Content'),
        required=True,
    )
    weighted = schema.Float(
        title=_(u'Weighted'),
        required=False,
        default=1.0
    )

class IPost(Interface):

    title = schema.TextLine(
        title=_(u'Name'),
        required=True
    )
    web_site = schema.Text(
        title=_(u'Web_site'),
        required=True
    )