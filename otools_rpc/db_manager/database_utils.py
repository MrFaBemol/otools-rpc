from loguru import logger
import requests
import xmlrpc.client


class DBManager:
    
    def __init__(self, url: str, password: str):

        # --------------------------------------------
        #                   PRIVATE
        # --------------------------------------------
        
        self._url = url[:-1] if url[-1] == "/" else url
        self._password = password

        self._duplicate_url = '{}/web/database/duplicate'.format(self._url)
        self._drop_url = '{}/web/database/drop'.format(self._url)
        
        
        # --------------------------------------------
        #                   PUBLIC
        # --------------------------------------------
        
        self.dbobject = xmlrpc.client.ServerProxy('{}/xmlrpc/2/db'.format(self._url))
        
    def duplicate(self, db, new_name):
        res = requests.post(self._duplicate_url, data={'master_pwd': self._password, 'name': db, 'new_name': new_name})
        return res
    
    def drop(self, db):
        res = requests.post(self._drop_url, data={'master_pwd': self._password, 'name': db})
        return res
    