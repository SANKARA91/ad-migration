from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient

def get_graph_client(tenant_id: str, client_id: str, client_secret: str) -> GraphServiceClient:
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    scopes = ["https://graph.microsoft.com/.default"]
    return GraphServiceClient(credentials=credential, scopes=scopes)