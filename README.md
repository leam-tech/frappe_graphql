# Frappe Graphql

GraphQL API Layer for Frappe Framework based on [graphql-core](https://github.com/graphql-python/graphql-core)

## Getting Started

Generate the SDLs first

```bash
$ bench --site test_site graphql generate_sdl
```

and start making your graphql requests against:

```
/api/method/graphql
```

# Features

- [Default GetDoc & GetList](./docs/default_get_doc_get_list.md)
- [Get Nested Link Field Documents](./docs/link_fields_nested.md)
- [Cursor Based Pagination](./docs/cursor_pagination.md)
- [Extending with Custom SDL & Resolvers](./docs/extending_schema.md)
- [File Uploads](./docs/file_uploads.md)
- [Custom Middleware](./docs/middleware.md)
- [GraphQL Subscriptions](./docs/subscriptions.md)
- [Restrict Query/Mutation Depth](./docs/restrict_depth.md)
- Role Permissions are verified for `read` access
- Introspection Queries are disabled in Production. You can enable it using `site_config.enable_introspection_in_production`
- Standard Mutations
  - [SET_VALUE Mutation](./docs/SET_VALUE.md)
  - [SAVE_DOC Mutation](./docs/SAVE_DOC.md)
  - [DELETE_DOC Mutation](./docs/DELETE_DOC.md)
- Helper Wrappers
  - [Resolver Exception Handlers](./docs/resolvers_and_exceptions.md)
  - [Role Permissions for Resolvers](./docs/resolver_role_permissions.md)

## Examples

- [Add new DocType](./docs/examples/add_new_doctype.md)
- [Introduce new Custom Field](./docs/examples/add_new_custom_field.md)
- [Add Hello World Query](./docs/examples/add_hello_world_query.md)
- [Add a New Mutation](./docs/examples/add_new_mutation.md)
- [Add Document Count per DocType Query](./docs/examples/add_document_count_query.md)

## License

MIT
