from box_sdk_gen import BoxClient, BoxAPIError

from config import GOVERNANCE_GROUPS


def get_or_create_group(client: BoxClient, name: str) -> str:
    """Create a governance group, or return the existing one on 409 Conflict."""
    try:
        group = client.groups.create_group(
            name,
            description="Governance group managed by onboarding automation.",
        )
        print(f"Created group '{group.name}' ({group.id})")
        return group.id
    except BoxAPIError as error:
        if error.response_info.status_code != 409:
            raise
        for group in client.groups.get_groups(filter_term=name).entries:
            if group.name == name:
                print(f"Using existing group '{group.name}' ({group.id})")
                return group.id
        raise


def resolve_governance_groups(client: BoxClient) -> dict:
    """Return a map of logical group key -> Box group ID."""
    return {
        key: get_or_create_group(client, name)
        for key, name in GOVERNANCE_GROUPS.items()
    }
