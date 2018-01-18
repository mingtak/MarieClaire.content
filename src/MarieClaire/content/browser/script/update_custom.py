# -*- coding: utf-8 -*-
import requests
from sqlalchemy import create_engine

DBSTR = 'mysql+mysqldb://MarieClaire:MarieClaire@localhost/MarieClaire?charset=utf8mb4'
ACCOUNT = {'id':'editor', 'pwd':'editor'}
ENGINE = create_engine(DBSTR, echo=True)


def execSql(execStr):
    conn = ENGINE.connect() # DB連線
    execResult = conn.execute(execStr)
    conn.close()
    if execResult.returns_rows:
        return execResult.fetchall()


def main():

    execStr = "SELECT * FROM `dfp_advertiser` WHERE 1"
    result = execSql(execStr)

    for item in result:
        print '%s: %s' % (item['ADVERTISER_ID'], item['ADVERTISER_NAME'])
        id = item['ADVERTISER_ID']
        title = item['ADVERTISER_NAME']

        req = requests.get('http://localhost:8080/Plone/custom/%s' % id,
                  headers={'Accept': 'application/json'},
                  auth=(ACCOUNT['id'], ACCOUNT['pwd'])
              )

        if req.status_code == 200:
            if req.json()['title'] == title:
                continue
            else:
                try:
                    requests.patch('http://localhost:8080/Plone/custom/%s' % id,
                        headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                        json={'title': title},
                        auth=(ACCOUNT['id'], ACCOUNT['pwd'])
                    )
                except:pass

        try:
            requests.post('http://localhost:8080/Plone/custom/',
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                json={'@type': 'Custom', 'id': id, 'title': title},
                auth=(ACCOUNT['id'], ACCOUNT['pwd'])
            )
            print 'ok'
        except:pass

if __name__ == '__main__':
    main()
