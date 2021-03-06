# -*- coding: utf-8 -*-
"""Init and utils."""

from zope.i18nmessageid import MessageFactory

_ = MessageFactory('MarieClaire.content')

mysqlInfo = {
    'id': 'MarieClaire',
    'password': 'MarieClaire',
    'host': 'localhost',
    'port': '3306',
    'dbName': 'MarieClaire',
    'charset': 'utf8mb4',
}

# mysql參數
DBSTR = 'mysql+mysqldb://MarieClaire:MarieClaire@localhost/MarieClaire?charset=utf8mb4'
