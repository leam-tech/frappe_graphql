from typing import (
    Any,
    AsyncIterable,
    Dict,
    Iterable,
    List,
    Optional,
    Union,
    Tuple,
    cast,
)

from graphql.execution.execute import ExecutionContext
from graphql.execution.collect_fields import collect_fields
from graphql.error import GraphQLError, located_error
from graphql.type import (
    GraphQLAbstractType,
    GraphQLLeafType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLResolveInfo,
    is_abstract_type,
    is_leaf_type,
    is_list_type,
    is_non_null_type,
    is_object_type,
)
from graphql.language import (
    FieldNode,
    OperationDefinitionNode,
    OperationType,
)
from graphql.pyutils import (
    inspect,
    is_iterable,
    AwaitableOrValue,
    Path,
    Undefined,
)

from .deferred_value import DeferredValue, deferred_dict, deferred_list
from .dataloader import DataLoader


class DeferredExecutionContext(ExecutionContext):
    def __init__(self, *args, **kwargs):
        self._deferred_values: List[Tuple[DeferredValue, Any]] = []

        return super().__init__(*args, **kwargs)

    def is_lazy(self, value: Any) -> bool:
        return isinstance(value, DataLoader.LazyValue)

    def execute_operation(
        self, operation: OperationDefinitionNode, root_value: Any
    ) -> Optional[AwaitableOrValue[Any]]:
        """Execute an operation.

        Implements the "Executing operations" section of the spec.
        """
        root_type = self.schema.get_root_type(operation.operation)
        if root_type is None:
            raise GraphQLError(
                "Schema is not configured to execute"
                f" {operation.operation.value} operation.",
                operation,
            )

        root_fields = collect_fields(
            self.schema,
            self.fragments,
            self.variable_values,
            root_type,
            operation.selection_set,
        )

        path = None

        result = (
            self.execute_fields_serially
            if operation.operation == OperationType.MUTATION
            else self.execute_fields
        )(root_type, root_value, path, root_fields)

        while len(self._deferred_values) > 0:
            for d in list(self._deferred_values):
                self._deferred_values.remove(d)
                res = d[1].get()
                d[0].resolve(res)

        if isinstance(result, DeferredValue):
            if result.is_rejected:
                raise cast(Exception, result.reason)
            return result.value

        return result

    def execute_fields(
        self,
        parent_type: GraphQLObjectType,
        source_value: Any,
        path: Optional[Path],
        fields: Dict[str, List[FieldNode]],
    ) -> AwaitableOrValue[Dict[str, Any]]:
        """Execute the given fields concurrently.

        Implements the "Executing selection sets" section of the spec
        for fields that may be executed in parallel.
        """
        results = {}
        is_awaitable = self.is_awaitable
        awaitable_fields: List[str] = []
        append_awaitable = awaitable_fields.append
        contains_deferred = False
        for response_name, field_nodes in fields.items():
            field_path = Path(path, response_name, parent_type.name)
            result = self.execute_field(
                parent_type, source_value, field_nodes, field_path
            )
            if result is not Undefined:
                results[response_name] = result
                if is_awaitable(result):
                    append_awaitable(response_name)
                if isinstance(result, DeferredValue):
                    contains_deferred = True

        if contains_deferred:
            return deferred_dict(results)

        #  If there are no coroutines, we can just return the object
        if not awaitable_fields:
            return results

        # Otherwise, results is a map from field name to the result of resolving that
        # field, which is possibly a coroutine object. Return a coroutine object that
        # will yield this same map, but with any coroutines awaited in parallel and
        # replaced with the values they yielded.
        async def get_results() -> Dict[str, Any]:
            from asyncio import gather
            results.update(
                zip(
                    awaitable_fields,
                    await gather(*(results[field] for field in awaitable_fields)),
                )
            )
            return results

        return get_results()

    def complete_value(
        self,
        return_type: GraphQLOutputType,
        field_nodes: List[FieldNode],
        info: GraphQLResolveInfo,
        path: Path,
        result: Any,
    ) -> AwaitableOrValue[Any]:
        """Complete a value.

        Implements the instructions for completeValue as defined in the
        "Value completion" section of the spec.

        If the field type is Non-Null, then this recursively completes the value
        for the inner type. It throws a field error if that completion returns null,
        as per the "Nullability" section of the spec.

        If the field type is a List, then this recursively completes the value
        for the inner type on each item in the list.

        If the field type is a Scalar or Enum, ensures the completed value is a legal
        value of the type by calling the ``serialize`` method of GraphQL type
        definition.

        If the field is an abstract type, determine the runtime type of the value and
        then complete based on that type.

        Otherwise, the field type expects a sub-selection set, and will complete the
        value by evaluating all sub-selections.
        """
        # If result is an Exception, throw a located error.
        if isinstance(result, Exception):
            raise result

        # If field type is NonNull, complete for inner type, and throw field error if
        # result is null.
        if is_non_null_type(return_type):
            completed = self.complete_value(
                cast(GraphQLNonNull, return_type).of_type,
                field_nodes,
                info,
                path,
                result,
            )
            if completed is None:
                raise TypeError(
                    "Cannot return null for non-nullable field"
                    f" {info.parent_type.name}.{info.field_name}."
                )
            return completed

        # If result value is null or undefined then return null.
        if result is None or result is Undefined:
            return None

        if self.is_lazy(result):
            def handle_resolve(resolved: Any) -> Any:
                return self.complete_value(
                    return_type, field_nodes, info, path, resolved
                )

            def handle_error(raw_error: Exception) -> None:
                raise raw_error

            deferred = DeferredValue()
            self._deferred_values.append((
                deferred, result
            ))

            completed = deferred.then(handle_resolve, handle_error)
            return completed

        # If field type is List, complete each item in the list with inner type
        if is_list_type(return_type):
            return self.complete_list_value(
                cast(GraphQLList, return_type), field_nodes, info, path, result
            )

        # If field type is a leaf type, Scalar or Enum, serialize to a valid value,
        # returning null if serialization is not possible.
        if is_leaf_type(return_type):
            return self.complete_leaf_value(cast(GraphQLLeafType, return_type), result)

        # If field type is an abstract type, Interface or Union, determine the runtime
        # Object type and complete for that type.
        if is_abstract_type(return_type):
            return self.complete_abstract_value(
                cast(GraphQLAbstractType, return_type), field_nodes, info, path, result
            )

        # If field type is Object, execute and complete all sub-selections.
        if is_object_type(return_type):
            return self.complete_object_value(
                cast(GraphQLObjectType, return_type), field_nodes, info, path, result
            )

        # Not reachable. All possible output types have been considered.
        raise TypeError(  # pragma: no cover
            "Cannot complete value of unexpected output type:"
            f" '{inspect(return_type)}'."
        )

    def complete_list_value(
        self,
        return_type: GraphQLList[GraphQLOutputType],
        field_nodes: List[FieldNode],
        info: GraphQLResolveInfo,
        path: Path,
        result: Union[AsyncIterable[Any], Iterable[Any]],
    ) -> AwaitableOrValue[List[Any]]:
        """Complete a list value.

        Complete a list value by completing each item in the list with the inner type.
        """
        if not is_iterable(result):
            # experimental: allow async iterables
            if isinstance(result, AsyncIterable):
                # noinspection PyShadowingNames
                async def async_iterable_to_list(
                    async_result: AsyncIterable[Any],
                ) -> Any:
                    sync_result = [item async for item in async_result]
                    return self.complete_list_value(
                        return_type, field_nodes, info, path, sync_result
                    )

                return async_iterable_to_list(result)

            raise GraphQLError(
                "Expected Iterable, but did not find one for field"
                f" '{info.parent_type.name}.{info.field_name}'."
            )
        result = cast(Iterable[Any], result)

        # This is specified as a simple map, however we're optimizing the path where
        # the list contains no coroutine objects by avoiding creating another coroutine
        # object.
        item_type = return_type.of_type
        is_awaitable = self.is_awaitable
        awaitable_indices: List[int] = []
        append_awaitable = awaitable_indices.append
        completed_results: List[Any] = []
        append_result = completed_results.append
        contains_deferred = False
        for index, item in enumerate(result):
            # No need to modify the info object containing the path, since from here on
            # it is not ever accessed by resolver functions.
            item_path = path.add_key(index, None)
            completed_item: AwaitableOrValue[Any]
            if is_awaitable(item):
                # noinspection PyShadowingNames
                async def await_completed(item: Any, item_path: Path) -> Any:
                    try:
                        completed = self.complete_value(
                            item_type, field_nodes, info, item_path, await item
                        )
                        if is_awaitable(completed):
                            return await completed
                        return completed
                    except Exception as raw_error:
                        error = located_error(
                            raw_error, field_nodes, item_path.as_list()
                        )
                        self.handle_field_error(error, item_type)
                        return None

                completed_item = await_completed(item, item_path)
            else:
                try:
                    completed_item = self.complete_value(
                        item_type, field_nodes, info, item_path, item
                    )
                    if is_awaitable(completed_item):
                        # noinspection PyShadowingNames
                        async def await_completed(item: Any, item_path: Path) -> Any:
                            try:
                                return await item
                            except Exception as raw_error:
                                error = located_error(
                                    raw_error, field_nodes, item_path.as_list()
                                )
                                self.handle_field_error(error, item_type)
                                return None

                        completed_item = await_completed(completed_item, item_path)
                    if isinstance(completed_item, DeferredValue):
                        contains_deferred = True

                except Exception as raw_error:
                    error = located_error(raw_error, field_nodes, item_path.as_list())
                    self.handle_field_error(error, item_type)
                    completed_item = None

            if is_awaitable(completed_item):
                append_awaitable(index)
            append_result(completed_item)

        if contains_deferred is True:
            return deferred_list(completed_results)

        if not awaitable_indices:
            return completed_results

        # noinspection PyShadowingNames
        async def get_completed_results() -> List[Any]:
            from asyncio import gather
            for index, result in zip(
                awaitable_indices,
                await gather(
                    *(completed_results[index] for index in awaitable_indices)
                ),
            ):
                completed_results[index] = result
            return completed_results

        return get_completed_results()
