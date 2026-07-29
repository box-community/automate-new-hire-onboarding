import os

from dotenv import load_dotenv
from box_sdk_gen import (
    BoxClient,
    BoxCCGAuth,
    CCGConfig,
)

load_dotenv()


def get_box_client() -> BoxClient:
    """Authenticate as the application's Service Account using CCG.

    Requires App + Enterprise Access so the service account can create
    and manage enterprise groups (and optionally users).
    """
    config = CCGConfig(
        client_id=os.getenv("BOX_CLIENT_ID"),
        client_secret=os.getenv("BOX_CLIENT_SECRET"),
        enterprise_id=os.getenv("BOX_ENTERPRISE_ID"),
    )
    auth = BoxCCGAuth(config=config)
    return BoxClient(auth=auth)
