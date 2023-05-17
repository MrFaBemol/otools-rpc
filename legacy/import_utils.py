import pandas



class OdooImportUtils:

    def __init__(self):
        self.df = None


    def read_excel(self, filename: str):
        self.df = pandas.DataFrame(pandas.read_excel(filename))

    def set_mapping_tree(self, tree: dict):
        pass




# Todo:--------------
# - if 'xml_id' in dict: 'write' else 'create'
# - check that all fields exist in model
# - if field in "key" is a many2one, check that the content is a xml_id (from format)
# - if value is a dict, make a search from the dict key/value: {'name': ['column_1']} -> search id where name == value of column_1 (limit 1)
# - if key is a related field, update the field with the value: 'categ_id.name': ['column_2'] > write categ_id.name with value of column_2




# test = {
#     "product.supplierinfo": {
#         # "xml_id": "ID Externe",       => À utiliser pour write au lieu de create
#         "mapping": {
#             "date_start": ["date_start"],
#             "date_end": ["date_end"],
#             "product_code": ["N° d’article"],
#             "product_tmpl_id": ["id"],
#             "min_qty": ["min_qty"],
#             "product_uom": {"name": ["product_uom"]},
#             "currency_id": {"name": ["currency_id"]},
#             "price": ["price"],
#             "delay": ["delay"],
#         }
#     }
# }
