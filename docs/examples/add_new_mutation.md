# Adding a new Mutation

There are two ways:

1. Write SDL and Attach Resolver to the Schema

   ```graphql
   # SDL for Mutation
   type MY_MUTATION_OUTPUT_TYPE {
       success: Boolean
   }

   extend type Mutation {
       myNewMutation(args): MY_MUTATION_OUTPUT_TYPE
   }
   ```

   ```py
   # Attach Resolver (Specify the cmd to this function in `graphql_schema_processors` hook)
   def myMutationResolver(schema: GraphQLSchema):
       def _myMutationResolver(obj: Any, info: GraphQLResolveInfo):
           # frappe.set_value(..)
           return {
               "success": True
           }

       mutation_type = schema.mutation_type
       mutation_type.fields["myNewMutation"].resolve = _myMutationResolver
   ```

2. Make use of `graphql-core` apis

   ```py
   # Specify the cmd to this function in `graphql_schema_processors` hook
   def bindMyNewMutation(schema):

       def _myMutationResolver(obj: Any, info: GraphQLResolveInfo):
           # frappe.set_value(..)
           return {
               "success": True
           }

       mutation_type = schema.mutation_type
       mutation_type.fields["myNewMutation"] = GraphQLField(
           GraphQLObjectType(
               name="MY_MUTATION_OUTPUT_TYPE",
               fields={
                   "success": GraphQLField(
                       GraphQLBoolean,
                       resolve=lambda obj, info: obj["success"]
                   )
               }
           ),
           resolve=_myMutationResolver
       )
   ```
