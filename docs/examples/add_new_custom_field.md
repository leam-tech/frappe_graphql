## Introducing a Custom Field to GraphQL

- Add the `Custom Field` in frappe
- Add the following to a `.graphql` file in your app and specify its directory via `graphql_sdl_dir`

```graphql
extend type User {
  is_super: Int!
}
```
