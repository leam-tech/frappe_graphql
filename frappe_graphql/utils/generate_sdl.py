import os
import frappe
from frappe.model import display_fieldtypes, table_fields, default_fields


def make_doctype_sdl_files(target_dir):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    def write_file(filename, contents):
        target_file = os.path.join(target_dir, f"{frappe.scrub(filename)}.graphql")
        with open(target_file, "w") as f:
            f.write(contents)

    write_file("root", get_root_sdl())

    for doctype in frappe.get_all("DocType"):
        doctype = doctype.name
        sdl = get_doctype_sdl(doctype)
        write_file(doctype, sdl)


def get_root_sdl():
    sdl = "schema {\n\tquery: Query\n}"

    sdl += "\n\ninterface BaseDocType {"
    for field in default_fields:
        if field in ("idx", "docstatus"):
            fieldtype = "Int"
        else:
            fieldtype = "String"
        sdl += f"\n  {field}: {fieldtype}"
    sdl += "}"

    sdl += "\n\ntype Query {"
    for doctype in frappe.get_all("DocType"):
        doctype = doctype.name
        sdl += f"\n  {doctype.replace(' ', '')}"
        sdl += "(name: String, filters: String"

        # if doctype in ("User", "Workflow"):
        for field in frappe.get_meta(doctype).get("fields", {"in_standard_filter": 1}):
            if field.fieldtype in table_fields:
                continue
            sdl += f", {field.fieldname}: {get_graphql_type(field, ignore_reqd=True)}"

        sdl += f"): [{doctype.replace(' ', '')}!]!"
    sdl += "\n}"

    return sdl


def get_doctype_sdl(doctype):
    meta = frappe.get_meta(doctype)
    sdl = f"type {doctype.replace(' ', '')} implements BaseDocType {{"

    defined_fieldnames = [] + list(default_fields)

    for field in default_fields:
        if field in ("idx", "docstatus"):
            fieldtype = "Int"
        else:
            fieldtype = "String"
        sdl += f"\n  {field}: {fieldtype}"

    for field in meta.fields:
        if field.fieldtype in display_fieldtypes:
            continue
        if field.fieldname in defined_fieldnames:
            continue
        defined_fieldnames.append(field.fieldname)
        sdl += f"\n  {get_field_sdl(field)}"

    sdl += "\n}"
    return sdl


def get_field_sdl(docfield):
    return f"{docfield.fieldname}: {get_graphql_type(docfield)}"


def get_graphql_type(docfield, ignore_reqd=False):
    string_fieldtypes = [
        "Small Text", "Long Text", "Code", "Text Editor", "Markdown Editor",
        "HTML Editor", "Date", "Datetime", "Time", "Text", "Data", "Link",
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
        graphql_type = "String"
    elif docfield.fieldtype in table_fields:
        graphql_type = f"[{docfield.options.replace(' ', '')}!]!"
    else:
        frappe.throw(f"Invalid fieldtype: {docfield.fieldtype}")

    if not ignore_reqd and docfield.reqd and graphql_type[-1] != "!":
        graphql_type += "!"

    return graphql_type
