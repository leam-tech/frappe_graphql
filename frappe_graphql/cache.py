import frappe

from frappe_graphql.utils.loader import FRAPPE_GRAPHQL_SCHEMA_REDIS_KEY


def clear_cache():
    frappe.cache().delete_value(keys=[FRAPPE_GRAPHQL_SCHEMA_REDIS_KEY])
