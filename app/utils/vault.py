""" Vault Configuration """

import logging
import os
import sys

import hvac

logger = logging.getLogger(__name__)

# URL for Vault Staging
VAULT_ADDRESS = "https://vault-staging.w.wish.com"

# tokenPath holds the file path on the disk/docker volume of the vault token
TOKEN_PATH = "/root/.vault-token"

# localtokenPath holds the file path of vault token stored locally
LOCAL_TOKEN_PATH = os.path.expanduser("~/.vault-token")

# define global vault client
vault_client = hvac.v1.Client(None)


def init_vault() -> hvac.v1.Client:
    """
    initialize the vault client
    """
    global vault_client
    vault_client = hvac.Client(url=VAULT_ADDRESS)
    vault_client.token = read_vault_token()
    try:
        assert vault_client.is_authenticated()
    except Exception as error:
        logger.warning(
            "Failed to authenticate Vault, Vault is disabled. Error: %s ", error
        )
    return vault_client


def read_vault_token() -> str:
    """
    read vault token from either env vars or /root/.vault-token, return empty string if neither found.
    """
    # read token from ENV VAR first
    token = os.environ.get("VAULT_TOKEN")
    if token is not None:
        return token

    # read token from file on disk /root/.vault-token else read from HOME/.vault-token
    if os.path.isfile(TOKEN_PATH):
        token_file = open(TOKEN_PATH, "r")
    elif os.path.isfile(LOCAL_TOKEN_PATH):
        token_file = open(LOCAL_TOKEN_PATH, "r")
    else:
        logger.warning(
            "Error: No token not found in %s and %s", TOKEN_PATH, LOCAL_TOKEN_PATH
        )
        return ""

    token = token_file.read()
    return token


def get_secret(mount_path: str, secret_path: str, key: str) -> str:
    """
    given the path and key, read the secret from vault.
    """
    try:
        secret_result = vault_client.secrets.kv.v1.read_secret(
            mount_point=mount_path,
            path=secret_path,
        )
    except Exception:
        logger.error(
            "Could not retrieve secret from Vault. ERROR: %s", sys.exc_info()[0]
        )
        raise

    return secret_result["data"][key]
