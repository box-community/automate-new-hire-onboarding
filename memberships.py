"""Optional helpers from the tutorial's Scaling to production section.

Add the new hire into enterprise groups so they inherit collaborations
those groups already hold across Box.
"""

from box_sdk_gen import (
    BoxClient,
    CreateGroupMembershipUser,
    CreateGroupMembershipGroup,
)


def add_user_to_group(client: BoxClient, user_id: str, group_id: str):
    client.memberships.create_group_membership(
        CreateGroupMembershipUser(id=user_id),
        CreateGroupMembershipGroup(id=group_id),
    )
    print(f"Added user {user_id} to group {group_id}")
