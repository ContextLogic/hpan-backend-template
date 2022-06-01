""" Vault Client Example """
from app.utils.vault import init_vault, get_secret

# the following path combines to a full Vault API route of "v1/mount_point/secret_path"
MOUNT_POINT = "services/python3-api-server/"
SECRET_PATH = "dev/example_secret"


if __name__ == "__main__":
    vault_client = init_vault()
    secret = get_secret(MOUNT_POINT, SECRET_PATH, "topsecret")
    print(
        "The {key} key under the secret path {path} is: {value}".format(
            key="topsecret", path=MOUNT_POINT + SECRET_PATH, value=secret
        )
    )
