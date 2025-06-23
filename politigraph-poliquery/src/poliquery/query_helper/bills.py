from gql import gql
from gql import Client

def add_bill(client: Client, params: dict):
    query = gql(
    """
    mutation CreateBills($input: [BillCreateInput!]!) {
        createBills(input: $input) {
            info {
                nodesCreated
                relationshipsCreated
            }
        }
    }
    """
    )
    result = client.execute(query, variable_values=params)  
    return result  

def update_bill(client: Client, params: dict):
    query = gql(
    """
    mutation UpdateBills($where: BillWhere, $update: BillUpdateInput) {
        updateBills(where: $where, update: $update) {
            info {
                nodesCreated
                relationshipsCreated
            }
        }
    }
    """
    )
    result = client.execute(query, variable_values=params)  
    return result  