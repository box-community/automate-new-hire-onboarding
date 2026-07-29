"""List a provisioned workspace's folders and collaborators.

Usage:

    python verify_workspace.py <workspace_id>

Run this as the Service Account (same credentials as the app) after
POST /hire returns a workspace_id. Workspaces live in the Service Account's
content by default and may not show up under your personal All Files.
"""

import sys

from box_client import get_box_client


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python verify_workspace.py <workspace_id>")

    workspace_id = sys.argv[1]
    client = get_box_client()

    print(f"Workspace {workspace_id}:")
    for folder in client.folders.get_folder_items(workspace_id).entries:
        print(folder.type, folder.id, folder.name)
        collaborations = client.list_collaborations.get_folder_collaborations(
            folder.id
        )
        for collaboration in collaborations.entries:
            accessible = collaboration.accessible_by
            name = accessible.name if accessible else "(unknown)"
            print(f"  {name} - {collaboration.role.value}")


if __name__ == "__main__":
    main()
