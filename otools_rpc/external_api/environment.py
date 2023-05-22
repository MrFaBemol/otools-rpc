import sys
import xmlrpc.client
import re
import copy
from typing import Union
from loguru import logger
from .recordset import RecordSet


class Environment(dict):
    # Todo: Add a cache system

    def __init__(self, url: str, username: str, password: str, db: str = None, auto_auth: bool = True, log_level: str = None, **kw):
        super().__init__(**kw)

        self._url = url[:-1] if url[-1] == "/" else url
        self._username = username
        self._password = password
        self._db = db or self._extract_db_from_url()

        self.common = xmlrpc.client.ServerProxy(f"{self._url}/xmlrpc/2/common", allow_none=True)
        self.models = None

        self.requests = list()
        self.cache = {}
        self._context = dict()          # Todo: use a frozendict for context things

        # Todo: make it an object
        self.user = None

        self.logger = logger
        self.logger.remove()
        self.logger.add(sys.stderr, level=log_level or "INFO")

        if auto_auth:
            self.authenticate()

    def __missing__(self, key):
        res = RecordSet(key, self)
        if self._has_missing_cache(key):
            self.cache.update({
                key: {
                    'fields': res.fields_get(),
                    'records': dict(),
                }
            })
        return res

    def __getitem__(self, key):
        assert self.user or key == 'res.users', "You must be authenticated to access models"
        return super(Environment, self).__getitem__(key)

    def __str__(self):
        return f"{self.__class__.__name__}<{id(self)}>"



    @property
    def uid(self):
        return self.user.get('id')

    @property
    def env(self):
        return self

    @property
    def context(self):
        return self._context

    @property
    def requests_count(self):
        return len(self.requests)


    # --------------------------------------------
    #                   PUBLIC
    # --------------------------------------------


    def authenticate(self):
        uid = self.common.authenticate(self._db, self._username, self._password, {})
        if uid:
            self.user = {'id': uid}
            self.models = xmlrpc.client.ServerProxy(f"{self._url}/xmlrpc/2/object", allow_none=True)
            self.user |= self['res.users'].browse(uid).read(['name', 'login'])[0]
            self.logger.info(f"Login successful on {self._url} ({self._db}) with res.users({uid}) - {self.user.get('name')} ({self.user.get('login')})")
        else:
            self.logger.error(f"Login failed on {self._url} ({self._db}) for {self._username}")

    def ref(self, xmlid):
        # xmlid = [xmlid] if isinstance(xmlid, str) else xmlid
        # Todo: add a multi version
        module, xml_id = xmlid.split(".")
        res = self['ir.model.data'].check_object_reference(module, xml_id)
        if res:
            return self[res[0]].browse(res[1])
        return None

    def with_context(self, **kw):
        self._context = self._context | kw
        return self


    def log_request(self, recordset, *args, **kwargs):
        # Todo: add more infos about performance.
        self.logger.trace(f"Executing {args[0]} on {recordset} with args: {args[1:]} / kwargs: {kwargs}")
        self.requests.append({
            'model': recordset._name,
            'method': args[0],
            'args': args[1:],
            'kwargs': kwargs
        })


    # --------------------------------------------
    #                   PRIVATE
    # --------------------------------------------


    def _extract_db_from_url(self, url: str = None) -> str:
        url = url or self._url
        db_re = r"(https?:\/\/)?([w]{3}\.)?([\w-]*)(.\w*)([\/\w]*)"
        return re.search(db_re, url).group(3)



    # --------------------------------------------
    #                   CACHE
    # --------------------------------------------


    def _has_missing_cache(self, key):
        return key not in self.cache

    def _update_cache_records(self, key, vals_dict: dict):
        self.cache[key]['records'].update(vals_dict)

    def update_cache_records(self, key: str, vals_list: list):
        """ Transform a read or search_read result into a usable dict and update the cache """
        vals_dict = dict()
        for r in copy.deepcopy(vals_list):
            i = r.pop('id')
            vals_dict[i] = r
        self._update_cache_records(key, vals_dict)

    def delete_cached_records(self, key: str, ids: Union[int, list[int]]):
        ids = ids if isinstance(ids, list) else [ids]
        for i in ids:
            self.cache[key]['records'].pop(i)

    # def get_cached_value(self, key: str, ids: Union[int, list] = None):
    #     ids = ids if isinstance(ids, list) else [ids]
    #     return self.cache[key]['records']
