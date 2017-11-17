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
        value_type=RelationChoice(title=_(u"Choice"),
                                  source=CatalogSource(Type='Advertisement'),),
        required=False,
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