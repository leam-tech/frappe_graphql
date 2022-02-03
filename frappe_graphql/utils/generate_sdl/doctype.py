import re
import inflect

import frappe
from frappe.utils import cint
from frappe.model import default_fields, display_fieldtypes, table_fields
from frappe.model.meta import Meta


def get_doctype_sdl(doctype, options):
    """
    options = dict(
        disable_enum_select_fields=False,
        ignore_custom_fields=False
    )
    """
    generated_enums = frappe._dict()

    meta = frappe.get_meta(doctype)
    sdl, defined_fieldnames = get_basic_doctype_sdl(meta, options=options, generated_enums=generated_enums)

    # Extend Doctype with Custom Fields
    if not options.ignore_custom_fields and len(meta.get_custom_fields()):
        sdl += get_custom_field_sdl(meta, defined_fieldnames, options=options)

    if not options.disable_enum_select_fields:
        sdl += get_select_docfield_enums(meta=meta, options=options, generated_enums=generated_enums)

    # DocTypeSortingInput
    if not meta.issingle:
        sdl += get_sorting_input(meta)
        sdl += get_connection_type(meta)

    # Extend QueryType
    sdl += get_query_type_extension(meta)

    return sdl


def get_basic_doctype_sdl(meta: Meta, options: dict, generated_enums=None):
    dt = format_doctype(meta.name)
    sdl = f"type {dt} implements BaseDocType {{"

    defined_fieldnames = [] + list(default_fields)

    for field in default_fields:
        if field in ("idx", "docstatus"):
            fieldtype = "Int"
        elif field in ("owner", "modified_by"):
            fieldtype = "User!"
        elif field == "parent":
            fieldtype = "BaseDocType"
        else:
            fieldtype = "String"
        sdl += f"\n  {field}: {fieldtype}"
    sdl += "\n  owner__name: String!"
    sdl += "\n  modified_by__name: String!"
    sdl += "\n  parent__name: String"

    for field in meta.fields:
        if field.fieldtype in display_fieldtypes:
            continue
        if field.fieldname in defined_fieldnames:
            continue
        if cint(field.get("is_custom_field")):
            continue
        defined_fieldnames.append(field.fieldname)
        sdl += f"\n  {get_field_sdl(meta, field, options=options, generated_enums=generated_enums)}"
        if field.fieldtype in ("Link", "Dynamic Link"):
            sdl += f"\n  {get_link_field_name_sdl(field)}"

    sdl += "\n}"

    return sdl, defined_fieldnames


def get_custom_field_sdl(meta, defined_fieldnames, options):
    sdl = f"\n\nextend type {format_doctype(meta.name)} {{"
    for field in meta.get_custom_fields():
        if field.fieldtype in display_fieldtypes:
            continue
        if field.fieldname in defined_fieldnames:
            continue
        defined_fieldnames.append(field.fieldname)
        sdl += f"\n  {get_field_sdl(meta, field, options=options)}"
        if field.fieldtype in ("Link", "Dynamic Link"):
            sdl += f"\n  {get_link_field_name_sdl(field)}"
    sdl += "\n}"

    return sdl


def get_select_docfield_enums(meta, options, generated_enums=None):
    sdl = ""
    for field in meta.get("fields", {"fieldtype": "Select"}):

        has_no_options = all([len(x or "") == 0 for x in (field.options or "").split("\n")])

        has_invalid_options = False
        if any([
            contains_reserved_characters(option)
            for option in (field.options or "").split("\n")
        ]):
            has_invalid_options = True

        if (options.ignore_custom_fields and cint(field.get("is_custom_field"))) \
                or has_no_options \
                or has_invalid_options:
            continue

        sdl += "\n\n"
        sdl += f"enum {get_select_docfield_enum_name(meta.name, field, generated_enums)} {{"
        for option in (field.get("options") or "").split("\n"):
            if not option or not len(option):
                continue
            sdl += f"\n  {frappe.scrub(option).upper()}"

        sdl += "\n}"

    return sdl


def get_sorting_input(meta):
    dt = format_doctype(meta.name)

    sdl = f"\n\nenum {dt}SortField {{"
    sdl += "\n  NAME"
    sdl += "\n  CREATION"
    sdl += "\n  MODIFIED"
    for field in meta.fields:
        if not field.search_index and not field.unique:
            continue
        sdl += f"\n  {field.fieldname.upper()}"
    sdl += "\n}"

    sdl += f"\n\ninput {dt}SortingInput {{"
    sdl += "\n  direction: SortDirection!"
    sdl += f"\n  field: {dt}SortField!"
    sdl += "\n}"
    return sdl


def get_connection_type(meta):
    dt = format_doctype(meta.name)
    sdl = f"\n\ntype {dt}CountableEdge {{"
    sdl += "\n  cursor: String!"
    sdl += f"\n  node: {dt}!"
    sdl += "\n}"

    sdl += f"\n\ntype {dt}CountableConnection {{"
    sdl += "\n  pageInfo: PageInfo!"
    sdl += "\n  totalCount: Int"
    sdl += f"\n  edges: [{dt}CountableEdge!]!"
    sdl += "\n}"

    return sdl


def get_query_type_extension(meta: Meta):
    dt = format_doctype(meta.name)
    sdl = "\n\nextend type Query {"
    if meta.issingle:
        sdl += f"\n  {dt}: {dt}!"
    else:
        plural = get_plural(meta.name)
        if plural == meta.name:
            prefix = "A"
            if dt[0].lower() in ("a", "e", "i", "o", "u"):
                prefix = "An"

            sdl += f"\n  {prefix}{dt}(name: String!): {dt}!"
        else:
            sdl += f"\n  {dt}(name: String!): {dt}!"

        plural_dt = format_doctype(plural)
        sdl += f"\n  {plural_dt}(filter: [DBFilterInput], sortBy: {dt}SortingInput, "
        sdl += "before: String, after: String, "
        sdl += f"first: Int, last: Int): {dt}CountableConnection!"

    sdl += "\n}\n"
    return sdl


def get_field_sdl(meta, docfield, options: dict, generated_enums: list = None):
    return f"{docfield.fieldname}: {get_graphql_type(meta, docfield, options=options, generated_enums=generated_enums)}"


def get_link_field_name_sdl(docfield):
    return f"{docfield.fieldname}__name: String"


def get_graphql_type(meta, docfield, options: dict, generated_enums=None):
    string_fieldtypes = [
        "Small Text", "Long Text", "Code", "Text Editor", "Markdown Editor", "HTML Editor",
        "Date", "Datetime", "Time", "Text", "Data", "Rating", "Read Only",
        "Attach", "Attach Image", "Signature", "Color", "Barcode", "Geolocation", "Duration"
    ]
    int_fieldtypes = ["Int", "Long Int", "Check"]
    float_fieldtypes = ["Currency", "Float", "Percent"]

    if options.disable_enum_select_fields:
        string_fieldtypes.append("Select")

    graphql_type = None
    if docfield.fieldtype in string_fieldtypes:
        graphql_type = "String"
    elif docfield.fieldtype in int_fieldtypes:
        graphql_type = "Int"
    elif docfield.fieldtype in float_fieldtypes:
        graphql_type = "Float"
    elif docfield.fieldtype == "Link":
        graphql_type = f"{format_doctype(docfield.options)}"
    elif docfield.fieldtype == "Dynamic Link":
        graphql_type = "BaseDocType"
    elif docfield.fieldtype in table_fields:
        graphql_type = f"[{format_doctype(docfield.options)}!]!"
    elif docfield.fieldtype == "Password":
        graphql_type = "Password"
    elif docfield.fieldtype == "Select":
        graphql_type = get_select_docfield_enum_name(meta.name, docfield, generated_enums)

        # Mark NonNull if there is no empty option and is required
        has_empty_option = all([len(x or "") == 0 for x in (docfield.options or "").split("\n")])

        has_invalid_options = False
        if any([
            contains_reserved_characters(option)
            for option in (docfield.options or "").split("\n")
        ]):
            has_invalid_options = True

        if has_empty_option or has_invalid_options:
            graphql_type = "String"
        if docfield.reqd:
            graphql_type += "!"
    else:
        frappe.throw(f"Invalid fieldtype: {docfield.fieldtype}")

    if docfield.reqd and graphql_type[-1] != "!":
        graphql_type += "!"

    return graphql_type


def get_plural(doctype):
    p = inflect.engine()
    return p.plural(doctype)


def format_doctype(doctype):
    return remove_reserved_characters(doctype.replace(" ", "").replace("-", "_"))


def get_select_docfield_enum_name(doctype, docfield, generated_enums=None):

    name = remove_reserved_characters(
        f"{doctype}{(docfield.label or docfield.fieldname).title()}SelectOptions"
        .replace(" ", ""))

    if name in generated_enums.values():
        name = remove_reserved_characters(
            f"{doctype}{(docfield.fieldname).title()}SelectOptions"
            .replace(" ", ""))

    if generated_enums is not None:
        if docfield in generated_enums:
            name = generated_enums[docfield]
        else:
            generated_enums[docfield] = name

    return name


def remove_reserved_characters(string):
    return re.sub(r"[^A-Za-z0-9_ ]", "", string)


def contains_reserved_characters(string):
    if not string:
        return False

    matches = re.match(r"^[A-Za-z_ ][A-Za-z0-9_ ]*$", string)
    if matches:
        return False
    else:
        return True
