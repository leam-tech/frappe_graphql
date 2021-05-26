from .error_coded_exceptions import *  # noqa


class GraphQLFileSyntaxError(Exception):
    def __init__(self, schema_file, message) -> None:
        super().__init__()
        self.message = self.format_message(schema_file, message)

    def format_message(self, schema_file, message):
        return f"Could not load {schema_file}:\n{message}"

    def __str__(self):
        return self.message
