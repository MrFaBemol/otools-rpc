import sys
import xmlrpc.client
import re
from loguru import logger as loguru_logger
from .recordset import RecordSet
from .common import frozendict
from .cache import Cache


class Environment(dict):

    def __init__(
            self,
            url: str,
            username: str,
            password: str,
            db: str = None,
            auto_auth: bool = True,
            logger: loguru_logger = None,
            log_level: str = None,

            cache_default_expiration: int = 10,
            cache_no_expiration: bool = False,
            cache_enabled: bool = True,
            **kw
    ):
        super().__init__(**kw)

        self._url = url[:-1] if url[-1] == "/" else url
        self._username = username
        self._password = password
        self._db = db or self._extract_db_from_url()

        # --------------------------------------------
        #                LOGGING
        # --------------------------------------------
        self.logger = logger if isinstance(logger, type(loguru_logger)) else loguru_logger
        try:
            self.logger.level("FTRACE", no=3, color="<blue>")       # Allow multiple environnements to share the same logger
        except TypeError:
            pass

        if logger is None:
            self.logger.remove()
            self.logger.add(sys.stderr, level=log_level or "INFO")


        self.common = xmlrpc.client.ServerProxy(f"{self._url}/xmlrpc/2/common", allow_none=True)
        self.models = None
        self.requests = list()
        self._context = frozendict()

        # Todo: make it an object
        self.user = None

        # --------------------------------------------
        #                   CACHE
        # --------------------------------------------
        if not self.cache_enabled:
            cache_default_expiration = 0
        elif cache_no_expiration:
            cache_default_expiration = 31_536_000       # 1 year for fun (365 * 24 * 60 * 60)

        # Cache will always be created even if we don't use it to store infos
        # It is used for helpers like field_exists()
        self.cache = Cache(self, cache_default_expiration)
        self.cache_enabled = cache_enabled


        if auto_auth:
            self.authenticate()

    def __missing__(self, key):
        return RecordSet(key, self, context=self._context)

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
        self._context = self._context.copy(**kw)
        return self


    def log_request(self, recordset, *args, **kwargs):
        # Todo: add more infos about performance.
        self.logger.trace(f"Executing {args[0]} on {recordset}")
        self.logger.log("FTRACE", f"└── with args: {args[1:]} / kwargs: {kwargs}")
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


