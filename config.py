# Maps a logical role key to the actual Box group name.
# Edit the names to match the groups in your enterprise.
GOVERNANCE_GROUPS = {
    "IT": "IT Onboarding",
    "HR": "HR Onboarding",
    "All Employees": "All Employees",
}

# The standardized folder tree created for every new hire.
# `collaborators` grants a governance group access at that exact level.
# Because collaborations cascade, access granted on a folder also
# applies to everything nested inside it.
WORKSPACE_TEMPLATE = {
    "name": "Onboarding",
    "collaborators": [],
    "children": [
        {"name": "Personal", "collaborators": [], "children": []},
        {
            "name": "IT Setup",
            "collaborators": [{"group": "IT", "role": "editor"}],
            "children": [],
        },
        {
            "name": "HR Documents",
            "collaborators": [{"group": "HR", "role": "editor"}],
            "children": [],
        },
        {
            "name": "Policies & Templates",
            "collaborators": [{"group": "All Employees", "role": "viewer"}],
            "children": [],
        },
        {"name": "Team Resources", "collaborators": [], "children": []},
    ],
}
