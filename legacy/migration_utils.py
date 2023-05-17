from log_utils import LoggingUtils
from odoo import api, SUPERUSER_ID, _




def _assert_xor_parameters(*args, check_falsy: bool = False):
    """
    Check that only ONE argument is set (not None). Equivalent of chained XOR with reduce
    :param args: several arguments
    :param check_falsy: if True, at least ONE argument must have a truthy value
    :return: True if only one argument is set
    """
    check_fn = bool if check_falsy else (lambda v: v is not None)
    not_none_values = [a for a in args if check_fn(a)]
    return len(not_none_values) == 1


HOOK_LEVELS = [
    'UNKNOWN',
    'PRE',
    'POST',
    'END',
    'INIT',
]


class OdooMigrationUtils(LoggingUtils):

    def __init__(self, cr, version, mode: str = None):
        self.version = version
        self.env = api.Environment(cr, SUPERUSER_ID, {})
        self.mode = HOOK_LEVELS.index(mode) if mode in HOOK_LEVELS else 0
        super(OdooMigrationUtils, self).__init__(f"[{HOOK_LEVELS[self.mode]}]")



    # --------------------------------------------
    #                   MODULES
    # --------------------------------------------


    def uninstall_modules(self, *modules_names):
        self.info(f"Uninstalling modules: {modules_names}")
        modules = self.env['ir.module.module'].search([('name', 'in', list(modules_names))])
        modules.button_uninstall()

    def upgrade_modules(self, *modules_names):
        self.info(f"Upgrading modules: {modules_names}")
        modules = self.env['ir.module.module'].search(
            [('name', 'in', list(modules_names))]
        )
        modules.button_upgrade()

    # --------------------------------------------
    #                   ASSETS
    # --------------------------------------------


    def delete_assets(self, *asset_names):
        self.info(f"Deleting assets: {asset_names}")
        try:
            with self.env.cr.savepoint():
                queries = [
                    f"DELETE FROM ir_asset WHERE name LIKE '%{name}%'"
                    for name in asset_names
                ]
                self.env.cr.execute(";".join(queries))

        except Exception as e:
            self.error(str(e))
            raise


    # --------------------------------------------
    #                   FIELDS
    # --------------------------------------------


    def move_studio_fields_to_python(self, fields_by_model: dict[str, list[tuple[str, str]]], delete_studio: bool = True) -> None:
        """
        Copy data from Studio field to his equivalent in python, then delete the studio field from Odoo & PSQL
        It is mandatory that the field exists in python code, but there is no check on type for now, so use carefully.
        :param fields_by_model: a dict formatted as follow:
            {
                'python.model.name': [
                    ('x_studio_field_name', 'python_field_name'),
                    ...
                ],
                ...
            }
        :param delete_studio: whether method must delete studio fields or not.
        :return: None
        """

        try:
            with self.env.cr.savepoint():
                for model_name, fields_list in fields_by_model.items():
                    table_name = self.env[model_name]._table
                    studio_names, python_names = map(set, zip(*fields_list))

                    fields_list_str = "\n".join([f"\t- {sn} > {pn}" for sn, pn in fields_list])
                    self.info(f"Copying studio fields values to python fields for model {model_name} (table name: {table_name})\n{fields_list_str}")

                    # Check that all columns exists
                    self.env.cr.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}' AND column_name IN {tuple(studio_names | python_names)}")
                    missing_columns = (studio_names | python_names) - set(next(zip(*self.env.cr.fetchall())))
                    if missing_columns:
                        raise ValueError(f"Missing column(s) in `{table_name}` table: {', '.join([c for c in missing_columns])}")

                    # Copy studio values into python fields.
                    # Studio names are enclosed in double quotes because users might have used uppercase letters.
                    # I expect python dev not to btw (¬､¬)
                    queries = [
                        f"UPDATE {table_name} SET {python_name} = \"{studio_name}\" WHERE \"{studio_name}\" IS NOT NULL"
                        for studio_name, python_name in fields_list
                    ]
                    self.env.cr.execute(";".join(queries))

                    if delete_studio:
                        self.delete_fields({
                            model_name: list(studio_names),
                        })


        except Exception as e:
            self.error(str(e))
            raise



    def delete_fields(self, fields_by_model: dict[str, list[str]], use_orm: bool = True) -> None:
        """
        Delete fields from the database
        :param fields_by_model: a dict with key = model technical name, value = list of fields names
            Ex:
                {
                    'crm.lead': ['field_1', 'field_2'],
                    'res.partner': ['field_1'],
                }
        :param use_orm: if False, will use SQL statements instead of a safe unlink() call
        :return: None
        """
        if not use_orm:
            raise NotImplementedError("You can only delete fields using the ORM methods for now")

        for model, field_list in fields_by_model.items():
            self.info(f"Deleting fields for {model}: {field_list}")
            fields = self.env['ir.model.fields'].search([
                ('model_id.model', '=', model),
                ('name', 'in', field_list),
            ])
            fields.unlink()



    # --------------------------------------------
    #                   RECORDS
    # --------------------------------------------


    def write(self, model: str, vals: dict, domain: list = None, active_test: bool = True, use_orm: bool = True):
        """
            The main purpose of this method is to use it with the `use_orm=False`. Otherwise, it is juste a simple write()
            :return: A recordset
        """
        domain = domain or []
        records = self.env[model].with_context(active_test=active_test).search(domain)
        self.info(f"Updating records: {records}")
        if records:
            if use_orm:
                records.write(vals)
            else:
                str_updates = ",".join(["%s=%s" % (f, "'" + v + "'" if isinstance(v, str) else v) for f, v in vals.items()])
                self.env.cr.execute(f"UPDATE {self.env[model]._table} SET {str_updates} WHERE id IN {tuple(records.ids)}")
        return records


    # --------------------------------------------
    #                   VIEWS
    # --------------------------------------------


    def _get_views_from_xml_ids(self, xml_ids: list[str], raise_if_missing: bool = False):
        # Remove all duplicates before the search
        unique_xml_ids = set(xml_ids or [])
        views = self.env['ir.ui.view']
        missing_xml_ids = list()
        for xml_id in unique_xml_ids:
            try:
                views |= self.env.ref(xml_id)
            except KeyError:
                missing_xml_ids.append(xml_id)

        if missing_xml_ids and raise_if_missing:
            missing_str = '\n'.join([f"\t- {xml_id}" for xml_id in missing_xml_ids])
            raise ValueError(f"The views with the following XML ids are missing in the database: {missing_str}")

        return views

    def _get_views_from_names(self, names: list[str]):
        unique_names = set(names or [])
        views = self.env['ir.ui.view'].with_context(active_test=False).search([('name', 'in', list(unique_names))])
        return views

    def _get_views_from_models(self, model_names: list[str]):
        unique_names = set(model_names or [])
        views = self.env['ir.ui.view'].with_context(active_test=False).search([('model', 'in', list(unique_names))])
        return views

    def _get_views_from_modules(self, module_names: list[str]):
        unique_names = set(module_names or [])
        views = self.env['ir.ui.view']
        for module in unique_names:
            views |= self.env['ir.ui.view'].with_context(active_test=False).search([('model_data_id.module', '=', module)])
        return views

    def activate_views(self, xml_ids: list = None, names: list = None, models: list = None, modules: list = None) -> bool:
        views = self._get_views_from_xml_ids(xml_ids) | self._get_views_from_names(names) | self._get_views_from_models(models) | self._get_views_from_modules(modules)
        self.info(f"Activating views: {views}")
        return views.write({'active': True})

    def deactivate_views(self, xml_ids: list = None, names: list = None, models: list = None, modules: list = None) -> bool:
        views = self._get_views_from_xml_ids(xml_ids) | self._get_views_from_names(names) | self._get_views_from_models(models) | self._get_views_from_modules(modules)
        self.info(f"Deactivating views: {views}")
        return views.write({'active': False})





