import pathlib

from dotenv import dotenv_values, load_dotenv

dotenv_path = pathlib.Path(__file__).parent / ".env"

config = dotenv_values(dotenv_path)


def load_envs():
    load_dotenv(dotenv_path)
