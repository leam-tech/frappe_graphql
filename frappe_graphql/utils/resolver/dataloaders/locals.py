import frappe
from frappe_graphql.utils.execution import DataLoader


def get_loader_from_locals(key: str):
    if not hasattr(frappe.local, "dataloaders"):
        frappe.local.dataloaders = frappe._dict()

    if key in frappe.local.dataloaders:
        return frappe.local.dataloaders.get(key)


def set_loader_in_locals(key: str, loader: DataLoader):
    if not hasattr(frappe.local, "dataloaders"):
        frappe.local.dataloaders = frappe._dict()

    frappe.local.dataloaders[key] = loader
