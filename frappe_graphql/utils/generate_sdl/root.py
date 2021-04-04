from frappe.model import default_fields


def get_root_sdl():
    sdl = get_root_object()
    sdl += get_base_doctype_interface()
    sdl += get_mutations()
    sdl += get_root_query()
    sdl += get_db_filter_type()
    sdl += get_sorting_types()
    sdl += get_pagination_types()
    sdl += "\n"

    return sdl


def get_root_object():
    return "schema {\n\tquery: Query\n\tmutation: Mutation\n}"


def get_root_query():
    sdl = "\ntype Query {"
    sdl += "\n\tping: String!"
    sdl += "\n}"
    return sdl


def get_base_doctype_interface():
    sdl = "\n\ninterface BaseDocType {"
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

    return sdl


def get_db_filter_type():
    sdl = "\n\nenum DBFilterOperator {"
    sdl += "\n  EQ"
    sdl += "\n  NEQ"
    sdl += "\n  LT"
    sdl += "\n  GT"
    sdl += "\n  LTE"
    sdl += "\n  GTE"
    sdl += "\n  LIKE"
    sdl += "\n  NOT_LIKE"
    sdl += "\n}"

    sdl += "\n\ninput DBFilterInput {"
    sdl += "\n  fieldname: String!"
    sdl += "\n  operator: DBFilterOperator"
    sdl += "\n  value: String!"
    sdl += "\n}"

    return sdl


def get_sorting_types():
    sdl = "\n\nenum SortDirection {"
    sdl += "\n  ASC"
    sdl += "\n  DESC"
    sdl += "\n}"
    return sdl


def get_pagination_types():
    sdl = "\n\ntype PageInfo {"
    sdl += "\n  hasNextPage: Boolean!"
    sdl += "\n  hasPreviousPage: Boolean!"
    sdl += "\n  startCursor: String"
    sdl += "\n  endCursor: String"
    sdl += "\n}"

    return sdl


def get_mutations():
    return """\n
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
