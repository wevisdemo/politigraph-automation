from typing import Set
from gql import gql, Client
from aiocache import cached, Cache

TYPE_QUERY = gql("""
    query GetTypeFields($typeName: String!) {
        __type(name: $typeName) {
            name
            fields {
                name
            }
        }
    }
""")

@cached(cache=Cache.MEMORY)
async def get_allowed_fields_for_type(client: Client, type_name: str) -> set[str]:
    async with client as session:
        result = await session.execute(
            TYPE_QUERY,
            variable_values={"typeName": type_name}
        )

    type_data = result.get("__type")
    if not type_data:
        raise ValueError(f"Type '{type_name}' not found in the schema.")

    fields = type_data.get("fields")
    if fields is None:
        raise ValueError(f"Type '{type_name}' has no fields or is not an Object/Interface type.")

    return {f["name"] for f in fields}