from graphql.pyutils import FrozenDict, FrozenList


def unfreeze(obj, ignore_types=None):
    """
    FrozenDicts and FrozenLists come up in graphql generated ast
    They raise errors while pickling.

    Recursive Approach was not taken since it is very easy to exceed the recursion limit
    """

    if not ignore_types:
        ignore_types = []

    if obj is None:
        return obj

    to_process = [obj]
    while len(to_process) > 0:
        _obj = to_process.pop()

        for attr in dir(_obj):
            if attr.startswith("__"):
                continue
            value = getattr(_obj, attr)
            if isinstance(value, FrozenDict):
                value = {k: v for k, v in value.items()}
                to_process.extend(value.values())
            elif isinstance(value, FrozenList):
                value = [x for x in value]
                to_process.extend(value)
            elif not callable(value) and not isinstance(value, tuple(ignore_types)):
                to_process.append(value)

            try:
                setattr(_obj, attr, value)
            except BaseException:
                pass

    return obj
