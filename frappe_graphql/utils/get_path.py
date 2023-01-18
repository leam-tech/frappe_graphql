def path_key(info):
    return "-".join([p for p in info.path.as_list() if isinstance(p, str)])
