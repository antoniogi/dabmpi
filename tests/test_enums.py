import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import (
    ProblemType,
    SolutionType,
    SolverType,
    CommModelType,
    Tags,
    ObjectiveType,
)


def test_problem_type_values():
    assert ProblemType.NONE == 0
    assert ProblemType.FUSION == 1
    assert ProblemType.NONSEPARABLE == 2
    assert ProblemType.CRISTINA == 3


def test_solution_type_values():
    assert SolutionType.FUSION == 1
    assert SolutionType.NONSEPARABLE == 2
    assert SolutionType.CRISTINA == 3


def test_solver_type_values():
    assert SolverType.NONE == 0
    assert SolverType.DAB == 1
    assert SolverType.SA == 2


def test_comm_model_values():
    assert CommModelType.DRIVERWORKER == 0
    assert CommModelType.ALL2ALL == 1


def test_tags_values():
    assert Tags.RECVFROMDRIVER == 1
    assert Tags.RECVFROMWORKER == 2
    assert Tags.COMMSOLUTION == 3
    assert Tags.REQSENDINPUT == 4
    assert Tags.REQINPUT == 5
    assert Tags.ENDSIM == 6


def test_objective_type_values():
    assert ObjectiveType.MINIMIZE == 1
    assert ObjectiveType.MAXIMIZE == 2


def test_enums_are_ints():
    assert isinstance(ProblemType.FUSION, int)
    assert isinstance(ObjectiveType.MINIMIZE, int)
