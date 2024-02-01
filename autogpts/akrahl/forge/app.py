import os

from forge.agent import ForgeAgent

from forge.db import ForgeDatabase
from forge.sdk.workspace import GCSWorkspace

dbString = os.getenv("DATABASE_STRING")
bucket_name = os.getenv("BUCKET_NAME")

if not dbString:
    raise Exception("Missing DATABASE_STRING")

if not bucket_name:
    raise Exception("Missing BUCKET_NAME")


database_name = dbString
workspace = GCSWorkspace(bucket_name, base_path="workspace")
database = ForgeDatabase(database_name, debug_enabled=False)
agent = ForgeAgent(database=database, workspace=workspace)

app = agent.get_agent_app()
