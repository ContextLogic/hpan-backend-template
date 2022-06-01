from argparse import ArgumentParser, SUPPRESS

from app.config.config import Config


def load_options_from_cli() -> None:
    """
    calls at app startup phase, loads the configuration file,
    parse the cli arguments and overwrite the config if specified.
    return app config and celery config.
    """
    parser = ArgumentParser()
    print("parser")
    parser.add_argument(
        "-l", "--log_level", type=str, default=SUPPRESS, help="log level"
    )
    parser.add_argument("-e", "--env", type=str, default=SUPPRESS, help="environment")
    parser.add_argument("-p", "--port", type=int, default=SUPPRESS, help="server port")

    args = parser.parse_args()

    # override the default configuration using the value passed from cli arguments
    for key in args.__dict__:
        setattr(Config, key, args.__dict__.get(key))
