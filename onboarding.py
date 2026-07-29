import os

from dotenv import load_dotenv
from box_sdk_gen import (
    BoxClient,
    BoxAPIError,
    CreateCollaborationItem,
    CreateCollaborationItemTypeField,
    CreateCollaborationAccessibleBy,
    CreateCollaborationAccessibleByTypeField,
    CreateCollaborationRole,
)

from box_client import get_box_client
from config import WORKSPACE_TEMPLATE
from groups import resolve_governance_groups
from workspace import build_workspace, is_already_collaborator

load_dotenv()


def invite_new_hire(client: BoxClient, folder_id: str, login: str):
    """Give the new hire access to their workspace root.

    Co-owner is used when the service account owns the folder. Otherwise we
    fall back to editor, because only owners and co-owners can grant co-owner.
    """
    me = client.users.get_user_me()
    folder = client.folders.get_folder_by_id(folder_id, fields=["owned_by"])
    if folder.owned_by and folder.owned_by.id == me.id:
        role = CreateCollaborationRole.CO_OWNER
    else:
        role = CreateCollaborationRole.EDITOR

    try:
        client.user_collaborations.create_collaboration(
            item=CreateCollaborationItem(
                type=CreateCollaborationItemTypeField.FOLDER, id=folder_id
            ),
            accessible_by=CreateCollaborationAccessibleBy(
                type=CreateCollaborationAccessibleByTypeField.USER, login=login
            ),
            role=role,
        )
        print(f"Invited {login} to workspace {folder_id} as {role.value}")
    except BoxAPIError as error:
        if not is_already_collaborator(error):
            raise


def onboard_new_hire(hire: dict) -> str:
    client = get_box_client()

    group_ids = resolve_governance_groups(client)

    template = dict(WORKSPACE_TEMPLATE)
    template["name"] = f"{hire['name']} - Onboarding"

    parent_id = os.getenv("ONBOARDING_ROOT_FOLDER_ID", "0")
    workspace_id = build_workspace(client, template, parent_id, group_ids)

    if hire.get("email"):
        invite_new_hire(client, workspace_id, hire["email"])

    print(f"Workspace ready for {hire['name']} (ID: {workspace_id})")
    return workspace_id


if __name__ == "__main__":
    # Simulate a hire event for a quick local test (no email invite).
    onboard_new_hire({"name": "Jordan Rivera", "email": None})
