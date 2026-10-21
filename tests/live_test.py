"""Live end-to-end test against a real Box enterprise.

Posts an employee.hired event to /hire, then checks the workspace matches
WORKSPACE_TEMPLATE in config.py: every folder exists and each governance group
is shared at the right level with the right role. Posts the event again to
check a re-run reuses the same workspace instead of creating a duplicate.

The event has no work email, so no invitation is sent. The governance groups
are long-lived and are reused, not deleted. The workspace is created under a
unique name and deleted at the end. Reads the same variables as .env.example,
from the environment or a local .env.
"""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app import app  # noqa: E402
from box_client import get_box_client  # noqa: E402
from config import GOVERNANCE_GROUPS, WORKSPACE_TEMPLATE  # noqa: E402

REQUIRED_ENV = [
    "BOX_CLIENT_ID",
    "BOX_CLIENT_SECRET",
    "BOX_ENTERPRISE_ID",
    "ONBOARDING_ROOT_FOLDER_ID",
]


def hire(test_client, name: str) -> str:
    response = test_client.post(
        "/hire",
        json={"event": "employee.hired", "employee": {"full_name": name}},
    )
    assert response.status_code == 200, f"/hire returned {response.status_code}"
    body = response.get_json()
    assert body.get("status") == "provisioned", body
    return body["workspace_id"]


def group_shares(client, folder_id: str) -> set:
    collaborations = client.list_collaborations.get_folder_collaborations(folder_id)
    return {
        (collaboration.accessible_by.name, collaboration.role.value)
        for collaboration in collaborations.entries
        if collaboration.accessible_by and collaboration.accessible_by.type == "group"
    }


def expected_shares(node: dict) -> set:
    return {
        (GOVERNANCE_GROUPS[collaborator["group"]], collaborator["role"])
        for collaborator in node["collaborators"]
    }


def check_workspace(client, workspace_id: str, name: str) -> None:
    workspace = client.folders.get_folder_by_id(workspace_id)
    assert workspace.name == f"{name} - Onboarding", f"Unexpected name {workspace.name}"

    children = {
        item.name: item.id
        for item in client.folders.get_folder_items(workspace_id).entries
        if item.type == "folder"
    }
    for node in WORKSPACE_TEMPLATE["children"]:
        assert node["name"] in children, f"Missing folder '{node['name']}'"
        shares = group_shares(client, children[node["name"]])
        assert shares == expected_shares(node), (
            f"'{node['name']}' shared with {shares}, expected {expected_shares(node)}"
        )
        print(f"'{node['name']}': {sorted(shares) or 'no group shares'}")


def main() -> None:
    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")

    client = get_box_client()
    test_client = app.test_client()
    run_id = os.getenv("GITHUB_RUN_ID") or f"local-{int(time.time())}"
    name = f"CI run {run_id}"

    ignored = test_client.post("/hire", json={"event": "employee.terminated"})
    assert ignored.get_json() == {"status": "ignored"}, ignored.get_json()

    workspace_id = hire(test_client, name)
    print(f"Provisioned workspace {workspace_id}")

    try:
        check_workspace(client, workspace_id, name)
        assert hire(test_client, name) == workspace_id, "Re-run created a new workspace"
        check_workspace(client, workspace_id, name)
        print("Re-run reused the existing workspace")
        print("Live test passed")
    finally:
        client.folders.delete_folder_by_id(workspace_id, recursive=True)
        print(f"Deleted workspace {workspace_id}")


if __name__ == "__main__":
    main()
