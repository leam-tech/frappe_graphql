from typing import List
import frappe
from .frappe_dataloader import FrappeDataloader
from frappe_graphql.utils.permissions import get_allowed_fieldnames_for_doctype
from .locals import get_loader_from_locals, set_loader_in_locals


def get_doctype_dataloader(doctype: str, fields: List[str] = None) -> FrappeDataloader:
    loader = get_loader_from_locals(doctype)
    if loader:
        return loader

    loader = FrappeDataloader(_get_document_loader_fn(doctype=doctype, fields=fields))
    set_loader_in_locals(doctype, loader)
    return loader


def _get_document_loader_fn(doctype: str, fields: List[str] = None):
    fieldnames = fields or get_allowed_fieldnames_for_doctype(doctype)

    def _load_documents(keys: List[str]):
        docs = frappe.get_list(
            doctype=doctype,
            filters=[["name", "IN", keys]],
            fields=fieldnames,
            limit_page_length=len(keys) + 1
        )

        sorted_docs = []
        for k in keys:
            doc = [x for x in docs if x.name == k]
            if not len(doc):
                sorted_docs.append(None)
                continue

            sorted_docs.append(doc[0])
            docs.remove(doc[0])

        return sorted_docs

    return _load_documents
