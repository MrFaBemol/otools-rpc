from xmlrpc_utils import XMLRPCEnvironnement


url = "http://localhost:8069/"
username = "admin"
password = "admin"

env = XMLRPCEnvironnement(url, username, password, db='cary_v16')
env = env.with_context(lang='fr_CH')
print(env)

partners = env['res.partner'].search([])
partners.read(['name'])
# partners_count = env['res.partner'].search_count([])
print("=====================================================")
print()
for partner in partners:
    print(partner.name)
print("=====================================================")
print(env.requests_count)
print(env.requests)

# partner2 = env['res.partner'].search([('name', 'ilike', 'deco')])
# print(partner2)
# print(partner2.mapped('name'))







# print(env)
# print(env['account.move'].browse(16))

# res = env['account.account'].write(21, {'use_carbon_value': True, 'carbon_in_is_manual': True, 'carbon_in_factor_id': 31})
# print(res)

# print(env['res.partner.bank'].fields_get())

# print(env['account.move'].exists([16, -1, 43, 567891]))

# res_id = env['res.partner'].create({'name': "test creation contact"})
# print(res_id)
# print(env['res.partner'].read(res_id, ['name']))
#
# res = env['res.partner'].write(res_id, {'name': "changement GCA"})
# print(res)
# print(env['res.partner'].read(res_id, ['name']))
#
# res = env['res.partner'].unlink(res_id)
#



from database_utils import DBManager
url = ""
db_pass = ""

db_manager = DBManager(url, db_pass)
print(db_manager.dbobject.list())


