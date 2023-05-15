import os.path
import pathlib

from dotenv import dotenv_values

config = dotenv_values(pathlib.Path(__file__).parent / ".env")
