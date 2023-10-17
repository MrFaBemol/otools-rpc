from datetime import datetime, timedelta
from .recordset import RecordSet
from .utils import is_magic_number_list


class Cache(dict):
    """
    Master class of cache. Give access to models via dict notation. Ex:
    >>> cache = Cache(env)
    >>> cache['res.partner'].field_exists('name')
    >>> True
    """

    def __init__(self, env, default_expiration: int):
        super().__init__()
        self._env = env
        self.config = {
            'expiration': {
                'default': default_expiration
            }
        }

    def __str__(self):
        return f"Cache({self._env})"

    def __missing__(self, key: str):
        if not isinstance(key, str):
            raise TypeError(f"Cache key must be a string, not {type(key)} ({key})")
        self[key] = CacheModel(self, key)
        return self[key]

    @property
    def env(self):
        return self._env




class CacheModel(dict):
    """
    Basically a dict of CacheRecord
    Allows to perform operations on model level with dict notation. Ex:
    >>> cache = Cache(env)
    >>> cache_record_7 = cache['res.partner'][7]    # Return a CacheRecord of res.partner(7)
    """

    def __init__(self, cache: "Cache", name: str):
        super().__init__()
        self._name = name
        self._cache = cache
        self._fields = cache.env[name].fields_get()

    def __str__(self):
        return f"CacheModel({self._name})"

    def __missing__(self, key: int):
        if not isinstance(key, int):
            raise TypeError(f"Record id must be an int, not {type(key)} ({key} on model {self.name})")
        self[key] = CacheRecord(self, key)
        return self[key]

    @property
    def api(self):
        return self._cache.env[self._name]

    @property
    def cache(self):
        return self._cache

    @property
    def name(self):
        return self._name

    @property
    def fields(self):
        return self._fields

    def field_exists(self, field: str):
        return field in self._fields

    def cache_expired(self, field: str, res_ids: list[int]):
        return any(self[res_id][field].is_expired for res_id in res_ids)


    def update(self, op, records, res, *args, **kwargs):
        """
        `Main method` that is used by any method prefixed with @cache in RecordSet class
        Depending on the operation, res is different:
        - create:   res is a RecordSet
        - write:    res is a boolean
        - delete:   res is a boolean
        - read:     res is a list of dicts
        """
        fields_to_read_post_update = list()

        if op == 'create':
            records = res       # Do not remove, so we can keep only 1 read statement at the end
            vals_list = [args[0]] if isinstance(args[0], dict) else args[0]
            for record, vals in zip(records, vals_list):
                fields_to_read_post_update += self._sanitize_vals(vals)
                self[record.id] = CacheRecord(self, record['id'])
                self[record.id].update(vals)

        elif op == 'write' and res:
            vals = args[0]
            for record in records:
                fields_to_read_post_update += self._sanitize_vals(vals)
                self[record.id].update(vals)

        elif op == 'delete':
            for record in records:
                if record.id in self:
                    del self[record.id]

        elif op == 'read':
            for rec_dict in res:
                res_id = rec_dict.pop('id')
                self[res_id].update(rec_dict)


        if fields_to_read_post_update:
            records.read(fields_to_read_post_update)



    def _sanitize_vals(self, vals: dict) -> list:
        """ Remove keys that are magic numbers and return them as a list of fields names """
        fields_to_remove = list()
        for k, v in vals.items():
            if (
                self.field_exists(k)
                and self._fields[k]['type'] in ['one2many', 'many2many']
                and is_magic_number_list(v)
            ):
                fields_to_remove.append(k)

        for k in fields_to_remove:
            vals.pop(k)

        return fields_to_remove


class CacheRecord(dict):
    def __init__(self, model: "CacheModel", res_id: int):
        super().__init__()
        self._model = model
        self._env_record = model.api.browse(res_id)

    def __str__(self):
        return f"CacheRecord({self._env_record})"

    def __missing__(self, key: str):
        key = str(key)
        if not self._model.field_exists(key):
            raise KeyError(f"Field {key} does not exist on model {self._model.name}")

        self[key] = CacheField(self, key)
        return self[key]

    @property
    def env_record(self):
        return self._env_record

    @property
    def model(self):
        return self._model


    def update(self, data):
        for field, value in data.items():
            if not self._model.field_exists(field):
                self._model.cache.env.logger.error(f"Field {field} does not exist on model {self._model.name}")
                continue
            self[field].set(value)




class CacheField:

    def __init__(self, record: "CacheRecord", name: str, validity_duration: int = None):
        self._record = record
        self._value = None
        self.name = name
        self.validity_duration = validity_duration
        self.expiration = None

    def __str__(self):
        return f"{self._value}"


    @property
    def is_expired(self):
        return self.expiration is None or (datetime.utcnow() > self.expiration)

    @property
    def infos(self):
        return self._record.model.fields[self.name]

    def get(self):
        if self.is_expired:
            self._read()
        return self._value

    def set(self, value):
        """
        Set the value of the field with smart resolvers
        This saves the value in the cache and set the expiration date also
            All relations: set it as a RecordSet to manipulate the field easily
            Many2one: save the name of the record (returned by API by default)
            One2many: save the inverse relation (the m2o)
        """
        if self.infos['type'] in ['many2one', 'one2many', 'many2many']:
            comodel_name = self.infos['relation']
            res_id = value

            if self.infos['type'] == 'many2one' and isinstance(value, (tuple, list)):
                res_id = value[0]
                self._record.model.cache[comodel_name][res_id]['name'].set(value[1])
            elif self.infos['type'] == 'one2many':
                relation_field = self.infos['relation_field']
                for i in res_id:
                    self._record.model.cache[comodel_name][i][relation_field].set(self._record.env_record.id)

            if isinstance(value, RecordSet):
                res_id = value.ids
            value = self._record.model.cache.env[comodel_name].browse(res_id)

        self._value = value
        self._set_expiration()


    def _read(self):
        self.set(self._record.env_record.read([self.name])[0].get(self.name))

    def _set_expiration(self):
        validity_duration = self.validity_duration or self._record.model.cache.config['expiration']['default']
        self.expiration = datetime.utcnow() + timedelta(seconds=validity_duration)


