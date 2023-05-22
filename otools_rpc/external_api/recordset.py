import copy
from .common import assert_same_model, cache, log_request, model
from typing import Union


class RecordSet:
    def __init__(self, name, env, ids: list[int] = None, context: dict = None):
        self._name = name
        self._env = env
        self._curr = -1
        self._ids = self._sanitize_ids(ids or list())

        """
        Each recordset has its own context, but inherits it:
            1) from the recordset it was created
            2) from the general environment 
        """
        self._context = copy.deepcopy(context) or copy.deepcopy(env.context) or dict()

        self.logger = self._env.logger

    def __str__(self):
        return f"{self._name}({', '.join(map(str, self._ids))})"

    def __bool__(self):
        return bool(self._ids)

    def __len__(self):
        return len(self._ids)

    def __iter__(self):
        self._curr = -1
        return self

    def __next__(self):
        if self._curr < len(self) - 1:
            self._curr += 1
            return RecordSet(self._name, self._env, [self._ids[self._curr]])
        raise StopIteration

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self._recordset(self._ids[item])
        elif isinstance(item, str):
            return getattr(self, item)

    def __getattr__(self, attr):
        if attr in self._env.cache.get(self._name, dict()).get('fields', list()):
            # Todo: code this instead of having a weird patch
            # self.ensure_one()
            return self._env.cache[self._name]['records'].get(self.id, dict()).get(attr, False)
        else:
            def wrapper(*args, **kw):
                return self._execute(attr, *args, **kw)
            return wrapper

    # --- Operators ---
    @assert_same_model('union')
    def __or__(self, other):
        return self._recordset(self.ids + other.ids)

    @assert_same_model('union')
    def __ior__(self, other):
        self._ids += other.ids
        return self

    def ensure_one(self):
        if len(self) != 1:
            raise ValueError(f"Expected singleton: {self}")

    # --- Properties ---
    @property
    def env(self):
        return self._env

    @property
    def ids(self):
        return self._ids

    @property
    def context(self):
        return self._context

    @property
    def id(self):
        self.ensure_one()
        return False if not self._ids else self._ids[0]

    @property
    def _model(self):
        return self._env[self._name]
        # return self._recordset(list())


    def _recordset(self, ids: Union[list[int], int]):
        ids = [ids] if isinstance(ids, int) else ids
        return self.__class__(self._name, self._env, ids, context=self._context)

    @staticmethod
    def _sanitize_ids(ids: Union[list[int], int]):
        ids = ids if isinstance(ids, list) else [ids]
        seen = set()
        return [i for i in ids if not (i in seen or seen.add(i))]

    @staticmethod
    def _format_domain(domain: list[tuple]) -> list[list]:
        return list(map(list, domain))

    @log_request
    def _execute(self, method, *args, **kw):
        """ Add ids in args if method is not @model decorated"""
        if not (m := getattr(self, method, None)) or (getattr(m, '_api', None) != 'model'):
            args = [self._ids] + list(args)
        kw['context'] = self.context | kw.get('context', dict())

        return self._env.models.execute_kw(
            self._env._db,
            self._env.uid,
            self._env._password,
            self._name,
            method,
            args,
            kw,
        )

    # --------------------------------------------
    #                   ORM
    # --------------------------------------------


    def browse(self, ids: Union[int, list[int]]) -> "RecordSet":
        return self._recordset(ids)

    def fields_get(self, attributes: list[str] = None):
        attributes = attributes or ['string', 'help', 'type']
        return self._execute('fields_get', attributes=attributes)

    @model
    def check_object_reference(self, module, xml_id):
        # Extra safety check, don't delete (even if nobody should use it directly)
        if self._name != 'ir.model.data':
            return self['ir.model.data'].check_object_reference(module, xml_id)
        return self._execute('check_object_reference', module, xml_id)

    def with_context(self, **kw):
        self._context = self._context | kw
        return self


    # --- CRUD ---


    @model
    def search(self, domain: list[tuple], **kw):
        ids = self._execute('search', self._format_domain(domain), **kw)
        return self._recordset(ids)

    def read(self, fields: list[str] = None, **kw):
        fields = fields or list()
        res = self._execute('read', fields=fields, **kw)
        self._env.update_cache_records(self._name, res)
        return res

    @model
    def search_read(self, domain: list[tuple], fields: list[str] = None, **kw):
        fields = fields or list()
        res = self._execute('search_read', self._format_domain(domain), fields=fields, **kw)
        self._env.update_cache_records(self._name, res)
        return self._recordset([r.get('id') for r in res])

    @model
    def search_count(self, domain: list[tuple]):
        return self._execute('search_count', self._format_domain(domain))

    @model
    def create(self, vals_list: Union[dict, list[dict]]):
        vals_list = vals_list if isinstance(vals_list, list) else [vals_list]
        ids = self._execute('create', vals_list)
        return self._recordset(ids)

    def write(self, vals: dict):
        return self._execute('write', vals)

    @cache('delete')
    def unlink(self):
        res = self._execute('unlink')
        if res:
            self._env.delete_cached_records(self._name, self._ids)
        return res

    def copy(self):
        res_id = self._execute('copy')
        return self._recordset(res_id)


    def mapped(self, field: str):
        return [getattr(rec, field) for rec in self]


