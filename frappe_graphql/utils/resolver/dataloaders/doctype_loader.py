from typing import List

import frappe

from frappe_graphql.utils.execution import DataLoader
from .locals import get_loader_from_locals, set_loader_in_locals


def get_doctype_dataloader(doctype: str) -> DataLoader:
    loader = get_loader_from_locals(doctype)
    if loader:
        return loader

    loader = DataLoader(load_fn=_get_document_loader_fn(doctype=doctype))
    set_loader_in_locals(doctype, loader)
    return loader


def _get_document_loader_fn(doctype: str):

    def _load_documents(keys: List[str]):
        docs = frappe.get_all(
            doctype=doctype,
            filters=[["name", "IN", keys]],
            fields=["*"],
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
