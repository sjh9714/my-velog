import sys
from pathlib import Path


def pytest_collect_file(file_path, parent):
    path = Path(str(file_path))

    if path.name != "test_solution.py":
        return None

    problem_dir = str(path.parent)

    if problem_dir in sys.path:
        sys.path.remove(problem_dir)

    sys.path.insert(0, problem_dir)
    sys.modules.pop("solution", None)
    return None
