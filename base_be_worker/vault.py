""" Vault Configuration """

import logging
import os
import sys

import hvac

logger = logging.getLogger(__name__)


class VaultClient:
    """
    a light abstraction of vault client
    """

    # defines the vault client
    client = hvac.v1.Client(None)

    # localtokenPath holds the file path of vault token stored locally
    LOCAL_TOKEN_PATH = os.path.expanduser("~/.vault-token")

    # URL for Vault Staging
    VAULT_ADDRESS = "https://vault-staging.w.wish.com"

    # tokenPath holds the file path on the disk/docker volume of the vault token
    TOKEN_PATH = "/root/.vault-token"

    @classmethod
    def init(cls, **kwargs: dict) -> hvac.v1.Client:
        """
        initialize the vault client.
        keyword args: vault_address, token_path, local_token_path
        """
        cls.VAULT_ADDRESS = kwargs.get(
            "vault_address", cls.VAULT_ADDRESS  # type: ignore[assignment]
        )
        cls.TOKEN_PATH = kwargs.get(
            "token_path", cls.TOKEN_PATH  # type: ignore[assignment]
        )
        cls.LOCAL_TOKEN_PATH = kwargs.get(
            "local_token_path", cls.LOCAL_TOKEN_PATH  # type: ignore[assignment]
        )

        cls.client = hvac.Client(url=cls.VAULT_ADDRESS)
        cls.client.token = cls.read_vault_token()
        try:
            assert cls.client.is_authenticated()
        except AssertionError as err:
            logger.critical(
                "Failed to authenticate Vault, Vault is disabled. Error: %s ", err
            )

    @classmethod
    def read_vault_token(cls) -> str:
        """
        read vault token from either env vars or /root/.vault-token,
        return empty string if neither found.
        """
        # read token from ENV VAR first
        token = os.environ.get("VAULT_TOKEN")
        if token is not None:
            return token

        # read token from file on disk /root/.vault-token else read from HOME/.vault-token
        if os.path.isfile(cls.TOKEN_PATH):
            token_file = open(cls.TOKEN_PATH, "r")
        elif os.path.isfile(cls.LOCAL_TOKEN_PATH):
            token_file = open(cls.LOCAL_TOKEN_PATH, "r")
        else:
            logger.warning(
                "Error: No token not found in %s and %s",
                cls.TOKEN_PATH,
                cls.LOCAL_TOKEN_PATH,
            )
            return ""

        token = token_file.read()
        return token

    @classmethod
    def get_secret(cls, mount_path: str, secret_path: str, key: str) -> str:
        """
        given the path and key, read the secret from vault.
        """
        try:
            secret_result = cls.client.secrets.kv.v1.read_secret(
                mount_point=mount_path,
                path=secret_path,
            )
        except Exception:
            logger.error(
                "Could not retrieve secret from Vault. ERROR: %s", sys.exc_info()[0]
            )
            raise

        return secret_result["data"][key]
