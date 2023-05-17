import requests
import xmlrpc.client

class DBManager:
    
    def __init__(self, url: str, password: str, **kw):

        self._url = url[:-1] if url[-1] == "/" else url
        self._password = password

        self.dbobject = xmlrpc.client.ServerProxy('{}/xmlrpc/2/db'.format(self._url))
        self._duplicate_url = '{}/web/database/duplicate'.format(self._url)
        self._drop_url = '{}/web/database/drop'.format(self._url)
        
    def duplicate(self, name, new_name):
        res = requests.post(self._duplicate_url, data={'master_pwd': self._password, 'name': name, 'new_name': new_name})
        return res
    
    def unlink(self, name):
        res = requests.post(self._drop_url, data={'master_pwd': self._password, 'name': name})
        return res
    
    def rename(self, name, new_name):
        duplicate = self.duplicate(name, new_name)
        unlink = self.unlink(name)
        return duplicate, unlink


