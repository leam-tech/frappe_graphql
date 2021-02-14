import os
import frappe
from typing import Generator

import graphql
from graphql import parse
from graphql.error import GraphQLSyntaxError

from .exceptions import GraphQLFileSyntaxError
from .resolver import bind_mutation_resolvers


def get_schema():
    schema = get_typedefs()

    ast_doc = graphql.parse(schema)
    schema = graphql.build_ast_schema(ast_doc)
    bind_mutation_resolvers(schema=schema)
    execute_schema_processors(schema=schema)
    return schema


def get_typedefs():
    target_dir = frappe.get_site_path("doctype_sdls")
    schema = load_schema_from_path(target_dir)

    for dir in frappe.get_hooks("graphql_sdl_dir"):
        dir = os.path.abspath(frappe.get_app_path("frappe", "../..", dir))

        schema += f"\n\n\n# {dir}\n\n"
        schema += load_schema_from_path(dir)

    return schema


def execute_schema_processors(schema):
    for cmd in frappe.get_hooks("graphql_schema_processors"):
        frappe.get_attr(cmd)(schema=schema)


def load_schema_from_path(path: str) -> str:
    if os.path.isdir(path):
        schema_list = [read_graphql_file(f) for f in sorted(walk_graphql_files(path))]
        return "\n".join(schema_list)
    return read_graphql_file(os.path.abspath(path))


def walk_graphql_files(path: str) -> Generator[str, None, None]:
    extension = ".graphql"
    for dirpath, _, files in os.walk(path):
        for name in files:
            if extension and name.lower().endswith(extension):
                yield os.path.join(dirpath, name)


def read_graphql_file(path: str) -> str:
    with open(path, "r") as graphql_file:
        schema = graphql_file.read()
    try:
        parse(schema)
    except GraphQLSyntaxError as e:
        raise GraphQLFileSyntaxError(path, str(e)) from e
    return schema
