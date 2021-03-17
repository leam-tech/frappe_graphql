import os
import frappe
from frappe.model import display_fieldtypes, table_fields, default_fields


def make_doctype_sdl_files(target_dir, doctypes=[]):

    write_root = len(doctypes or []) == 0
    if doctypes:
        for dt in doctypes:
            if not frappe.db.exists("DocType", dt):
                raise Exception("Invalid DocType: " + dt)
    else:
        doctypes = [x.name for x in frappe.get_all("DocType")]

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    def write_file(filename, contents):
        target_file = os.path.join(target_dir, f"{frappe.scrub(filename)}.graphql")
        with open(target_file, "w") as f:
            f.write(contents)

    if write_root:
        write_file("root", get_root_sdl())

    for doctype in doctypes:
        sdl = get_doctype_sdl(doctype)
        write_file(doctype, sdl)


def get_root_sdl():
    sdl = "schema {\n\tquery: Query\n\tmutation: Mutation\n}"

    sdl += "\n\ninterface BaseDocType {"
    for field in default_fields:
        if field in ("idx", "docstatus"):
            fieldtype = "Int"
        else:
            fieldtype = "String"
        sdl += f"\n  {field}: {fieldtype}"
    sdl += "\n  owner__doc: User"
    sdl += "\n  modified_by__doc: User"
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
        else:
            fieldtype = "String"
        sdl += f"\n  {field}: {fieldtype}"
    sdl += "\n  owner__doc: User"
    sdl += "\n  modified_by__doc: User"

    for field in meta.fields:
        if field.fieldtype in display_fieldtypes:
            continue
        if field.fieldname in defined_fieldnames:
            continue
        defined_fieldnames.append(field.fieldname)
        sdl += f"\n  {get_field_sdl(field)}"
        if field.fieldtype == "Link":
            sdl += f"\n  {get_link_field_doc_sdl(field)}"

    sdl += "\n}"

    # Extend QueryType
    sdl += "\n\nextend type Query {"
    sdl += f"\n  {doctype.replace(' ', '')}"
    sdl += "(name: String"

    # if doctype in ("User", "Workflow"):
    for field in meta.get("fields", {"in_standard_filter": 1}):
        if field.fieldtype in table_fields:
            continue
        sdl += f", {field.fieldname}: {get_graphql_type(field, ignore_reqd=True)}"

    sdl += ", filters: String"
    sdl += ", limit_start: Int = 0, limit_page_length: Int = 20"

    sdl += f"): [{doctype.replace(' ', '')}!]!"

    sdl += "\n}\n"

    return sdl


def get_field_sdl(docfield):
    return f"{docfield.fieldname}: {get_graphql_type(docfield)}"


def get_link_field_doc_sdl(docfield):
    return f"{docfield.fieldname}__doc: {docfield.options.replace(' ', '')}"


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

type Mutation {
    setValue(doctype: String!, name: String!, fieldname: String!, value: String): SET_VALUE_TYPE
    saveDoc(doctype: String!, doc: String!): SAVE_DOC_TYPE
}
"""
