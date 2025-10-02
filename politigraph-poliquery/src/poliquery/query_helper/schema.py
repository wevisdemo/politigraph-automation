from typing import Set
from gql import gql, Client
from aiocache import cached, Cache

@cached(cache=Cache.MEMORY)
async def get_allowed_fields_for_type(client: Client, type_name: str):
    """
    Introspects the client's schema to get all available fields for a given type.
    While cache the data for repeating call.

    Args:
        client: The GQL client with a fetched schema.
        type_name: The name of the node type

    Returns:
        A set of field names for that type.
    """
    async with client as session:
        schema = client.schema
        
    if not schema:
        raise RuntimeError("Schema has not been fetched. Please initialize the client properly.")

    schema_type = schema.get_type(type_name)

    if not schema_type:
        raise ValueError(f"Type '{type_name}' not found in the schema.")

    return set(schema_type.fields.keys()) # type: ignore