from frappe import _
from graphql import (ValidationRule, ValidationContext, DefinitionNode, FragmentDefinitionNode, OperationDefinitionNode,
                     Node, GraphQLError, FieldNode, InlineFragmentNode, FragmentSpreadNode)
from typing import Optional, Union, Callable, Pattern, List, Dict

IgnoreType = Union[Callable[[str], bool], Pattern, str]

"""
Copied from 
https://github.com/graphql-python/graphene/blob/a61f0a214d4087acac097ab05f3969d77d0754b5/graphene/validation/depth_limit.py#L108
"""


def depth_limit_validator(
    max_depth: int,
    ignore: Optional[List[IgnoreType]] = None,
    callback: Callable[[Dict[str, int]], None] = None,
):
    class DepthLimitValidator(ValidationRule):
        def __init__(self, validation_context: ValidationContext):
            document = validation_context.document
            definitions = document.definitions

            fragments = get_fragments(definitions)
            queries = get_queries_and_mutations(definitions)
            query_depths = {}

            for name in queries:
                query_depths[name] = determine_depth(
                    node=queries[name],
                    fragments=fragments,
                    depth_so_far=0,
                    max_depth=max_depth,
                    context=validation_context,
                    operation_name=name,
                    ignore=ignore,
                )
            if callable(callback):
                callback(query_depths)
            super().__init__(validation_context)

    return DepthLimitValidator


def get_fragments(
    definitions: List[DefinitionNode],
) -> Dict[str, FragmentDefinitionNode]:
    fragments = {}
    for definition in definitions:
        if isinstance(definition, FragmentDefinitionNode):
            fragments[definition.name.value] = definition
    return fragments


# This will actually get both queries and mutations.
# We can basically treat those the same
def get_queries_and_mutations(
    definitions: List[DefinitionNode],
) -> Dict[str, OperationDefinitionNode]:
    operations = {}

    for definition in definitions:
        if isinstance(definition, OperationDefinitionNode):
            operation = definition.name.value if definition.name else "anonymous"
            operations[operation] = definition
    return operations


def determine_depth(
    node: Node,
    fragments: Dict[str, FragmentDefinitionNode],
    depth_so_far: int,
    max_depth: int,
    context: ValidationContext,
    operation_name: str,
    ignore: Optional[List[IgnoreType]] = None,
) -> int:
    if depth_so_far > max_depth:
        context.report_error(
            GraphQLError(
                _("'{0}' exceeds maximum operation depth of {1}.").format(operation_name, max_depth),
                [node],
            )
        )
        return depth_so_far
    if isinstance(node, FieldNode):
        should_ignore = is_introspection_key(node.name.value) or is_ignored(
            node, ignore
        )

        if should_ignore or not node.selection_set:
            return 0
        return 1 + max(
            map(
                lambda selection: determine_depth(
                    node=selection,
                    fragments=fragments,
                    depth_so_far=depth_so_far + 1,
                    max_depth=max_depth,
                    context=context,
                    operation_name=operation_name,
                    ignore=ignore,
                ),
                node.selection_set.selections,
            )
        )
    elif isinstance(node, FragmentSpreadNode):
        return determine_depth(
            node=fragments[node.name.value],
            fragments=fragments,
            depth_so_far=depth_so_far,
            max_depth=max_depth,
            context=context,
            operation_name=operation_name,
            ignore=ignore,
        )
    elif isinstance(
        node, (InlineFragmentNode, FragmentDefinitionNode, OperationDefinitionNode)
    ):
        return max(
            map(
                lambda selection: determine_depth(
                    node=selection,
                    fragments=fragments,
                    depth_so_far=depth_so_far,
                    max_depth=max_depth,
                    context=context,
                    operation_name=operation_name,
                    ignore=ignore,
                ),
                node.selection_set.selections,
            )
        )
    else:
        raise Exception(
            _("Depth crawler cannot handle: {0}.").format(node.kind)
        )


def is_introspection_key(key):
    # from: https://spec.graphql.org/June2018/#sec-Schema
    # > All types and directives defined within a schema must not have a name which
    # > begins with "__" (two underscores), as this is used exclusively
    # > by GraphQL’s introspection system.
    return str(key).startswith("__")


def is_ignored(node: FieldNode, ignore: Optional[List[IgnoreType]] = None) -> bool:
    if ignore is None:
        return False
    for rule in ignore:
        field_name = node.name.value
        if isinstance(rule, str):
            if field_name == rule:
                return True
        elif isinstance(rule, Pattern):
            if rule.match(field_name):
                return True
        elif callable(rule):
            if rule(field_name):
                return True
        else:
            raise ValueError(_("Invalid ignore option: {0}.").format(rule))
    return False
