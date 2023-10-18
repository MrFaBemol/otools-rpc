from typing import Any


def is_magic_number(val: Any) -> bool:
    """ See https://www.odoo.com/documentation/16.0/developer/reference/backend/orm.html#odoo.fields.Command """
    return (
        # Magic numbers are a tuple of 3 elements
        isinstance(val, tuple) and len(val) == 3
        # First element is an int between 0 and 6 included
        and isinstance(val[0], int) and (0 <= val[0] <= 6)
        # Second element is an int
        and isinstance(val[1], int)
        # Third element is either a dict, a list of ints or a 0
        and (isinstance(val[2], (dict, list)) or val[2] == 0)
    )

def is_magic_number_list(vals_list: Any) -> bool:
    return isinstance(vals_list, list) and all(is_magic_number(v) for v in vals_list)


def is_relational_field(field_type: str) -> bool:
    return field_type in ['many2one', 'one2many', 'many2many']