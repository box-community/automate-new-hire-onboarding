# Box new hire onboarding workspaces

A minimal, runnable middleware service that listens for HR `hired` events and
provisions a standardized, governed Box workspace for every new hire.

It utilizes [Users](https://developer.box.com/guides/users/),
[Groups](https://developer.box.com/guides/groups/),
[Folders](https://developer.box.com/guides/folders/), and
[Collaborations](https://developer.box.com/guides/collaborations/) so every
new hire gets the same folder tree and group access.

This is the companion repository to the tutorial
**[Automate new hire onboarding with Box APIs](https://developer.box.com/tutorials/onboarding-workspaces)**.

## What it does

| Capability | How |
| --- | --- |
| Receive an HR hire event | `POST /hire` (Flask webhook listener) |
| Resolve or create governance groups | `POST /2.0/groups`, `GET /2.0/groups` |
| Build a personal folder tree | `POST /2.0/folders` from `config.WORKSPACE_TEMPLATE` |
| Grant group access at the right levels | `POST /2.0/collaborations` |
| Optionally invite the new hire | Collaboration on the workspace root |
| Re-run safely | Idempotent folder create + collaborator checks |

## Project layout

```
automate-new-hire-onboarding/
├── app.py                  # Flask hire-event listener
├── box_client.py           # CCG Service Account auth
├── config.py               # Governance groups + workspace template
├── groups.py               # Get-or-create governance groups
├── workspace.py            # Recursive folder + collaboration builder
├── onboarding.py           # Orchestrates provisioning (+ optional invite)
├── verify_workspace.py     # List folders/collaborators for a workspace ID
├── memberships.py          # Optional: add hire to enterprise groups
├── sample_hire_event.json  # Example payload for local curl tests
├── requirements.txt
├── .env.example
└── .gitignore
```

## Prerequisites

- **Python 3.11+**
- A [free Box developer account](https://account.box.com/signup/n/developer),
  or a Box account with administrator access
- A **Client Credentials Grant (CCG)** Platform App with:
  - **App Access Level** set to **App + Enterprise Access**
  - Scopes: **Read and write all files and folders**, **Manage groups**,
    **Manage users**
  - The app **authorized** (and **re-authorized** after scope/access changes)
    in the Admin Console
- Your **enterprise ID** (Developer Console profile icon, or Admin Console →
  Account & Billing)

> Creating and managing groups and users requires admin privileges. With CCG
> and `enterprise_id`, the app acts as the enterprise Service Account. Those
> operations only work when **App + Enterprise Access** is enabled.

## Setup

1. **Clone and enter the project**

   ```bash
   git clone https://github.com/box-community/automate-new-hire-onboarding.git
   cd automate-new-hire-onboarding
   ```

2. **Create a virtual environment and install dependencies**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

3. **Configure credentials**

   ```bash
   cp .env.example .env
   ```

   Fill in `BOX_CLIENT_ID`, `BOX_CLIENT_SECRET`, and `BOX_ENTERPRISE_ID`.
   Leave `ONBOARDING_ROOT_FOLDER_ID=0` to create workspaces in the Service
   Account's root, or set a dedicated **New Hires** folder ID (invite the
   Service Account as **co-owner** on that folder first).

   > **Never commit `.env`.** It is already in `.gitignore`.

4. **(Optional) customize the template** in `config.py` - group names and the
   folder tree for every future hire.

## Run

```bash
python app.py
```

The server starts on `http://127.0.0.1:5000` (with auto-reload enabled).

> Do not use `debug=True` in production. Authenticate hire-event requests
> (signature or shared secret) before provisioning from a public endpoint.

You can also provision without Flask:

```bash
python onboarding.py
```

That creates `Jordan Rivera - Onboarding` with no email invite.

## Try it

You need **two terminals**: one running the Flask server, one sending a
simulated HR event.

1. **Start the server** (terminal 1):

   ```bash
   source .venv/bin/activate
   python app.py
   ```

2. **Send a hire event** (terminal 2):

   ```bash
   curl -X POST http://127.0.0.1:5000/hire \
     -H "Content-Type: application/json" \
     -d @sample_hire_event.json
   ```

   Or inline JSON (omit `work_email` to skip the invite):

   ```bash
   curl -X POST http://127.0.0.1:5000/hire \
     -H "Content-Type: application/json" \
     -d '{
       "event": "employee.hired",
       "employee": {
         "full_name": "Jordan Rivera",
         "work_email": "jordan.rivera@example.com"
       }
     }'
   ```

3. **Check the result.** Terminal 1 should print created/reused groups,
   shared subfolders, and the workspace ID. The JSON response includes
   `workspace_id`.

4. **Verify as the Service Account:**

   ```bash
   python verify_workspace.py <workspace_id>
   ```

   Workspaces are owned by the Service Account by default, so they do **not**
   appear under your personal **All Files** unless you were invited. That is
   expected. You can also check **Admin Console** > **Content** > **Content Manager**.

5. **Run the same curl again.** The service completes without creating
   duplicate folders, groups, or collaborations.

## How it works

1. `POST /hire` receives an `employee.hired` payload from your HR system (or
   a local curl simulation).
2. `groups.py` get-or-creates the governance groups from `config.py`.
3. `workspace.py` walks `WORKSPACE_TEMPLATE` recursively: create each folder,
   then share it with the groups defined on that node. Collaborations cascade
   to nested content.
4. `onboarding.py` optionally invites the hire to the workspace root
   (co-owner when the Service Account owns the folder; editor otherwise).
5. Idempotency: folder name conflicts reuse the existing ID; existing
   collaborators are skipped (`conflict` for groups,
   `user_already_collaborator` for users).

## Security notes

- Keep client secrets and tokens server-side.
- Require **App + Enterprise Access** only when you need enterprise group/user
  management; re-authorize after changing it.
- Authenticate hire webhooks in production.
- Prefer a dedicated **New Hires** parent folder with the Service Account as
  co-owner instead of leaving workspaces only in the Service Account root.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `invalid_client` | Check `BOX_CLIENT_ID` / `BOX_CLIENT_SECRET` / `BOX_ENTERPRISE_ID` in `.env`. |
| `unauthorized_client` / not authorized | Authorize the app (Developer Console > Authorization > Review and Submit). |
| `403` / insufficient permissions | Set **App + Enterprise Access**; enable Read/Write, Manage groups, Manage users; **re-authorize**. |
| Groups/users not created (`403`) | Same as above — App Access Only cannot manage enterprise groups/users. |
| Unhandled `409 Conflict` | Confirm `create_folder` and `is_already_collaborator` match this repo (group vs user conflict codes differ). |
| Invite pending | Email is not an existing Box user yet; collaboration stays pending until accepted. |
| Workspace not in All Files | Owned by the Service Account - use `verify_workspace.py` or Content Manager. |
| `ModuleNotFoundError` | Activate the venv: `source .venv/bin/activate`. |

## License

[MIT](./LICENSE)
