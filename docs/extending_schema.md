## Support Extensions via Hooks

You can extend the SDLs with additional query / mutations / subscriptions. Examples are provided for a specific set of Scenarios. Please read [GraphQL Spec](http://spec.graphql.org/June2018/#sec-Object-Extensions) regarding Extending types. There are mainly two hooks introduced:

- `graphql_sdl_dir`  
  Specify a list of directories containing `.graphql` files relative to the app's root directory.
  eg:

```py
# hooks.py
graphql_sdl_dir = [
    "./your-app/your-app/generated/sdl/dir1",
    "./your-app/your-app/generated/sdl/dir2",
]
```

The above will look for graphql files in `your-bench/apps/your-app/your-app/generated/sdl/dir1` & `./dir2` folders.

- `graphql_schema_processors`  
You can pass in a list of cmd that gets executed on schema creation. You are given `GraphQLSchema` object (please refer [graphql-core](https://github.com/graphql-python/graphql-core)) as the only parameter. You can modify it or extend it as per your requirements.
This is a good place to attach the resolvers for the custom SDLs defined via `graphql_sdl_dir`