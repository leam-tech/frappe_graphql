from collections import OrderedDict
from typing import List

import frappe

from frappe_graphql.utils.permissions import get_allowed_fieldnames_for_doctype
from .frappe_dataloader import FrappeDataloader
from .locals import get_loader_from_locals, set_loader_in_locals


def get_child_table_loader(child_doctype: str, parent_doctype: str, parentfield: str,
                           path: str = None, fields: List[str] = None) -> FrappeDataloader:
    locals_key = (child_doctype, parent_doctype, parentfield)
    if path:
        # incase alias usage
        locals_key = locals_key + (path,)
    loader = get_loader_from_locals(locals_key)
    if loader:
        return loader

    loader = FrappeDataloader(_get_child_table_loader_fn(
        child_doctype=child_doctype,
        parent_doctype=parent_doctype,
        parentfield=parentfield,
        fields=fields
    ))
    set_loader_in_locals(locals_key, loader)
    return loader


def _get_child_table_loader_fn(child_doctype: str, parent_doctype: str, parentfield: str,
                               fields: List[str] = None):
    def _inner(keys):
        fieldnames = fields or get_allowed_fieldnames_for_doctype(
            doctype=child_doctype,
            parent_doctype=parent_doctype
        )

        rows = frappe.get_all(
            doctype=child_doctype,
            fields=fieldnames,
            filters=dict(
                parenttype=parent_doctype,
                parentfield=parentfield,
                parent=("in", keys),
            ),
            order_by="idx asc")

        _results = OrderedDict()
        for k in keys:
            _results[k] = []

        for row in rows:
            if row.parent not in _results:
                continue
            _results.get(row.parent).append(row)

        return _results.values()

    return _inner
