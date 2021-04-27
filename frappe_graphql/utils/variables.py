from graphql import parse

import frappe


def get_masked_variables(query, variables):
    """
    Return the variables dict with password field set to "******"
    """
    if isinstance(variables, str):
        variables = frappe.parse_json(variables)

    variables = frappe._dict(variables)
    try:
        document = parse(query)
        for operation_definition in document.definitions:
            for variable in operation_definition.variable_definitions:
                variable_name = variable.variable.name.value
                variable_type = variable.type

                if variable_name not in variables:
                    continue

                if not isinstance(variables[variable_name], str):
                    continue

                # Password! NonNull
                if variable_type.kind == "non_null_type":
                    variable_type = variable_type.type

                # Password is a named_type
                if variable_type.kind != "named_type":
                    continue

                if variable_type.name.value != "Password":
                    continue

                variables[variable_name] = "*" * len(variables[variable_name])
    except BaseException:
        return frappe._dict(
            status="Error Processing Variable Definitions",
            traceback=frappe.get_traceback()
        )

    return variables
