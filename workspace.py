from box_sdk_gen import (
    BoxClient,
    BoxAPIError,
    CreateFolderParent,
    CreateCollaborationItem,
    CreateCollaborationItemTypeField,
    CreateCollaborationAccessibleBy,
    CreateCollaborationAccessibleByTypeField,
    CreateCollaborationRole,
)

ROLE_MAP = {
    "editor": CreateCollaborationRole.EDITOR,
    "viewer": CreateCollaborationRole.VIEWER,
    "uploader": CreateCollaborationRole.UPLOADER,
    "co-owner": CreateCollaborationRole.CO_OWNER,
}


def is_already_collaborator(error: BoxAPIError) -> bool:
    # Box reports an existing collaborator differently for groups and users:
    # a group returns 409 with code "conflict", while a user can return
    # "user_already_collaborator". Match on both so re-runs are safe.
    body = error.response_info.body
    message = body.get("message", "").lower()
    return (
        body.get("code") == "user_already_collaborator"
        or "already a collaborator" in message
    )


def create_folder(client: BoxClient, name: str, parent_id: str) -> str:
    try:
        folder = client.folders.create_folder(
            name, CreateFolderParent(id=parent_id)
        )
        return folder.id
    except BoxAPIError as error:
        # 409 means a folder with this name already exists under the parent.
        # Reuse it so re-running the service never creates duplicates.
        if error.response_info.status_code != 409:
            raise
        conflicts = error.response_info.body.get("context_info", {}).get(
            "conflicts", []
        )
        return conflicts[0]["id"]


def add_group_collaboration(
    client: BoxClient, folder_id: str, group_id: str, role: str
):
    try:
        client.user_collaborations.create_collaboration(
            item=CreateCollaborationItem(
                type=CreateCollaborationItemTypeField.FOLDER, id=folder_id
            ),
            accessible_by=CreateCollaborationAccessibleBy(
                type=CreateCollaborationAccessibleByTypeField.GROUP, id=group_id
            ),
            role=ROLE_MAP[role],
        )
    except BoxAPIError as error:
        # Ignore if the group is already a collaborator on this folder.
        if not is_already_collaborator(error):
            raise


def build_workspace(
    client: BoxClient, node: dict, parent_id: str, group_ids: dict
) -> str:
    folder_id = create_folder(client, node["name"], parent_id)

    for collaborator in node.get("collaborators", []):
        group_id = group_ids[collaborator["group"]]
        add_group_collaboration(
            client, folder_id, group_id, collaborator["role"]
        )
        print(
            f"  Shared '{node['name']}' with "
            f"{collaborator['group']} ({collaborator['role']})"
        )

    for child in node.get("children", []):
        build_workspace(client, child, folder_id, group_ids)

    return folder_id
