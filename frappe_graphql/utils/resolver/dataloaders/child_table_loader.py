from collections import OrderedDict

from graphql_sync_dataloaders import SyncDataLoader

import frappe

from frappe_graphql.utils.permissions import get_allowed_fieldnames_for_doctype
from .locals import get_loader_from_locals, set_loader_in_locals


def get_child_table_loader(child_doctype: str, parent_doctype: str, parentfield: str) \
        -> SyncDataLoader:
    locals_key = (child_doctype, parent_doctype, parentfield)
    loader = get_loader_from_locals(locals_key)
    if loader:
        return loader

    loader = SyncDataLoader(_get_child_table_loader_fn(
        child_doctype=child_doctype,
        parent_doctype=parent_doctype,
        parentfield=parentfield,
    ))
    set_loader_in_locals(locals_key, loader)
    return loader


def _get_child_table_loader_fn(child_doctype: str, parent_doctype: str, parentfield: str):
    def _inner(keys):
        fieldnames = get_allowed_fieldnames_for_doctype(
            doctype=child_doctype,
            parent_doctype=parent_doctype
        )

        select_fields = ", ".join([f"`{x}`" if "`" not in x else x for x in fieldnames])

        rows = frappe.db.sql(f"""
        SELECT
            {select_fields}
        FROM `tab{child_doctype}`
        WHERE
            parent IN %(parent_keys)s
            AND parenttype = %(parenttype)s
            AND parentfield = %(parentfield)s
        ORDER BY idx
        """, dict(
            parent_keys=keys,
            parenttype=parent_doctype,
            parentfield=parentfield,
        ), as_dict=1)

        _results = OrderedDict()
        for k in keys:
            _results[k] = []

        for row in rows:
            if row.parent not in _results:
                continue
            _results.get(row.parent).append(row)

        return _results.values()

    return _inner
