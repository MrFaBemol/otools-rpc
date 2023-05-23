# otools-rpc

[![Version](https://img.shields.io/pypi/v/otools-rpc?color=blue&label=version)](https://pypi.org/project/otools-rpc/)
[![Status](https://img.shields.io/pypi/status/otools-rpc?color=orange.svg)](https://pypi.org/project/otools-rpc/)

otools-rpc is a Python package for interacting with the Odoo ERP system through XML-RPC requests. It provides a convenient way to communicate with Odoo and perform various operations. Please note that the package is currently in the testing/alpha phase, and further improvements and updates are expected.

## Features

[//]: # (### Environnement Class)

The `Environnement` class represents the environment for interacting with the Odoo ERP system. It provides the following features:

- Authentication: Authenticate with the Odoo system using username and password.
- Access Models: Access different models (tables) in the Odoo system.
- Caching: Caching mechanism to improve performance.
- Logging: Logging capabilities with customizable log levels.

## Installation

You can install otools-rpc using pip:

```console
$ pip install otools-rpc
```

See on pypi: https://pypi.org/project/otools-rpc/

## Usage

### Environment
Here are some examples of how to use otools-rpc to interact with the Odoo ERP system via the external API:

```python
from otools_rpc.external_api import Environment


url = "http://localhost:8069/"
username = "admin"
password = "admin"
master_password = "adminadmin"

# Create an instance of the environment
env = Environment(url, username, password, db='my_odoo')
env = env.with_context(lang='en_US')
print(env)

# Example: Create an invoice for a specific partner
partner_id = env['res.partner'].search([('name', '=', 'Mitchell Admin')], limit=1)
invoice_vals = {
    'partner_id': partner_id.id,
    'date_invoice': '2023-05-12',
    'type': 'out_invoice',
    'invoice_line_ids': [
        (0, 0, {
            'product_id': env['product.product'].search([('name', '=', 'Product A')], limit=1).id,
            'quantity': 5,
            'price_unit': 10.0,
        }),
        (0, 0, {
            'product_id': env['product.product'].search([('name', '=', 'Product B')], limit=1).id,
            'quantity': 3,
            'price_unit': 15.0,
        }),
    ],
}
invoice_id = env['account.move'].create(invoice_vals)
print("Created invoice:", invoice_id)

# Posting the invoice
invoice_id.action_post()

```

### DBManager
```python
from otools_rpc.db_manager import DBManager

url = "http://localhost:8069/"
master_password = "adminadmin"

dbmanager = DBManager(url, master_password)

#Return list of all the available DB in your Odoo ENV
dbmanager.dbobject.list()

#Duplicating my_odoo to my_new_odoo
db.manager.duplicate(db='my_odoo', new_name="my_new_odoo")

#Deleting my_new_odoo
db.manager.drop(db='my_new_odoo')
```

More details are coming soon...
