import os

from forge.agent import ForgeAgent
from forge.sdk import LocalWorkspace

from .db import ForgeDatabase

dbString = os.getenv("DATABASE_STRING")
workspace_dir = os.getenv("AGENT_WORKSPACE")

if not dbString:
    raise Exception("Missing DATABASE_STRING")

if not workspace_dir:
    raise Exception("Missing AGENT_WORKSPACE")


database_name = dbString
workspace = LocalWorkspace(workspace_dir)
database = ForgeDatabase(database_name, debug_enabled=False)
agent = ForgeAgent(database=database, workspace=workspace)

app = agent.get_agent_app()
