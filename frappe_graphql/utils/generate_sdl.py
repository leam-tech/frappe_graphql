import os
import frappe
from frappe.model import display_fieldtypes, table_fields, default_fields


def make_doctype_sdl_files(target_dir, app=None, modules=[], doctypes=[], ignore_root_file=False):
    doctypes = get_doctypes(
        app=app,
        modules=modules,
        doctypes=doctypes
    )

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    def write_file(filename, contents):
        target_file = os.path.join(target_dir, f"{frappe.scrub(filename)}.graphql")
        with open(target_file, "w") as f:
            f.write(contents)

    if not ignore_root_file:
        write_file("root", get_root_sdl())

    for doctype in doctypes:
        sdl = get_doctype_sdl(doctype)
        write_file(doctype, sdl)


def get_doctypes(app=None, modules=None, doctypes=[]):
    modules = list(modules or [])
    doctypes = list(doctypes or [])
    if app:
        if app not in frappe.get_installed_apps():
            raise Exception("App {} is not installed in this site".format(app))

        modules.extend([x.name for x in frappe.get_all(
            "Module Def",
            {"app_name": app}
        )])

    if modules:
        for module in modules:
            if not frappe.db.exists("Module Def", module):
                raise Exception("Invalid Module: " + module)

        doctypes.extend([x.name for x in frappe.get_all(
            "DocType",
            {"module": ["IN", modules]}
        )])

    if doctypes:
        for dt in doctypes:
            if not frappe.db.exists("DocType", dt):
                raise Exception("Invalid DocType: " + dt)
    else:
        doctypes = [x.name for x in frappe.get_all("DocType")]

    return doctypes


def get_root_sdl():
    sdl = "schema {\n\tquery: Query\n\tmutation: Mutation\n}"

    sdl += "\n\ninterface BaseDocType {"
    for field in default_fields:
        if field in ("idx", "docstatus"):
            fieldtype = "Int"
        elif field in ("owner", "modified_by"):
            fieldtype = "User!"
        else:
            fieldtype = "String"
        sdl += f"\n  {field}: {fieldtype}"
    sdl += "\n  owner__name: String!"
    sdl += "\n  modified_by__name: String!"
    sdl += "\n}"

    sdl += "\n\n" + MUTATIONS

    sdl += "\n\ntype Query {"
    sdl += "\n\tping: String!"
    sdl += "\n}"

    return sdl


def get_doctype_sdl(doctype):
    meta = frappe.get_meta(doctype)
    sdl = f"type {doctype.replace(' ', '')} implements BaseDocType {{"

    defined_fieldnames = [] + list(default_fields)

    for field in default_fields:
        if field in ("idx", "docstatus"):
            fieldtype = "Int"
        elif field in ("owner", "modified_by"):
            fieldtype = "User!"
        else:
            fieldtype = "String"
        sdl += f"\n  {field}: {fieldtype}"
    sdl += "\n  owner__name: String!"
    sdl += "\n  modified_by__name: String!"

    for field in meta.fields:
        if field.fieldtype in display_fieldtypes:
            continue
        if field.fieldname in defined_fieldnames:
            continue
        defined_fieldnames.append(field.fieldname)
        sdl += f"\n  {get_field_sdl(field)}"
        if field.fieldtype == "Link":
            sdl += f"\n  {get_link_field_name_sdl(field)}"

    sdl += "\n}"

    # Extend QueryType
    sdl += "\n\nextend type Query {"
    sdl += f"\n  {doctype.replace(' ', '')}"
    sdl += "(name: String"

    # if doctype in ("User", "Workflow"):
    for field in meta.get("fields", {"in_standard_filter": 1}):
        if field.fieldtype in table_fields:
            continue
        sdl += f", {field.fieldname}: {get_graphql_type(field, for_filter=True)}"

    sdl += ", filters: String"
    sdl += ", limit_start: Int = 0, limit_page_length: Int = 20"

    sdl += f"): [{doctype.replace(' ', '')}!]!"

    sdl += "\n}\n"

    return sdl


def get_field_sdl(docfield):
    return f"{docfield.fieldname}: {get_graphql_type(docfield)}"


def get_link_field_name_sdl(docfield):
    return f"{docfield.fieldname}__name: String"


def get_graphql_type(docfield, for_filter=False):
    string_fieldtypes = [
        "Small Text", "Long Text", "Code", "Text Editor", "Markdown Editor",
        "HTML Editor", "Date", "Datetime", "Time", "Text", "Data",
        "Dynamic Link", "Password", "Select", "Rating", "Read Only",
        "Attach", "Attach Image", "Signature", "Color", "Barcode", "Geolocation", "Duration"
    ]
    int_fieldtypes = ["Int", "Long Int", "Check"]
    float_fieldtypes = ["Currency", "Float", "Percent"]

    graphql_type = None
    if docfield.fieldtype in string_fieldtypes:
        graphql_type = "String"
    elif docfield.fieldtype in int_fieldtypes:
        graphql_type = "Int"
    elif docfield.fieldtype in float_fieldtypes:
        graphql_type = "Float"
    elif docfield.fieldtype == "Link":
        graphql_type = "String" if for_filter else f"{docfield.options.replace(' ', '')}"
    elif docfield.fieldtype in table_fields:
        graphql_type = f"[{docfield.options.replace(' ', '')}!]!"
    else:
        frappe.throw(f"Invalid fieldtype: {docfield.fieldtype}")

    if not for_filter and docfield.reqd and graphql_type[-1] != "!":
        graphql_type += "!"

    return graphql_type


MUTATIONS = """
type SET_VALUE_TYPE {
    doctype: String!
    name: String!
    fieldname: String!
    value: String!
    doc: BaseDocType!
}

type SAVE_DOC_TYPE {
    doctype: String!
    name: String!
    doc: BaseDocType!
}

type DELETE_DOC_TYPE {
    doctype: String!
    name: String!
    success: Boolean!
}

type Mutation {
    setValue(doctype: String!, name: String!, fieldname: String!, value: String): SET_VALUE_TYPE
    saveDoc(doctype: String!, doc: String!): SAVE_DOC_TYPE
    deleteDoc(doctype: String!, name: String!): DELETE_DOC_TYPE
}
"""
