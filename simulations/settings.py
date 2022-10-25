import pathlib

# PROJECT_PATH = pathlib.Path().absolute() # this gets the cwd
PROJECT_PATH = pathlib.Path(__file__).resolve().parent.parent
SIMULATIONS_PATH = PROJECT_PATH / "simulations"
DATA_PATH = PROJECT_PATH / "data"
