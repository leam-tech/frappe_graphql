from graphql import GraphQLResolveInfo


def get_info_path_key(info: GraphQLResolveInfo):
    return "-".join([p for p in info.path.as_list() if isinstance(p, str)])
