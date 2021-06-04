from typing import Union, List

import frappe


def REQUIRE_ROLES(role: Union[str, List[str]], exc=frappe.PermissionError):
    def inner(func):
        def wrapper(*args, **kwargs):
            nonlocal exc

            roles = set()
            if isinstance(role, str):
                roles.add(role)
            elif isinstance(role, list):
                roles.update(role)

            roles.difference_update(frappe.get_roles())

            if len(roles):
                exc = exc or frappe.PermissionError
                raise exc(frappe._("Permission Denied"))

            return func(*args, **kwargs)

        return wrapper

    return inner
