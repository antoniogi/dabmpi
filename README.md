# dabmpi

`dabmpi` is a distributed optimization framework for solving large numerical problems using MPI and Python. It provides a command-line driver for running optimization solvers with configurable problem types, solver modes, and runtime options.

## Features

- MPI-based driver/worker and all-to-all communication modes
- Support for multiple problem types: `FUSION`, `CRISTINA`, `NONSEPARABLE`
- Support for solver types: `DAB`, `SA`
- Configurable runtime behavior via INI configuration files
- Centralized package metadata using `pyproject.toml`

## Requirements

- Python 3.10
- `numpy`
- `mpi4py`
- MPI implementation (for example, MPICH or OpenMPI)

## Installation

```bash
cd src/dabmpi
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

This installs the project in editable mode and installs development dependencies such as `pytest`, `ruff`, and `mypy`.

## Running the tool

From the project root, use `mpirun` with the desired process count:

```bash
mpirun -np 4 dabmpi \
  --problem FUSION \
  --solver DAB \
  --ifile data/input.xml \
  --cfile data/param_config.xml \
  --time 3600 \
  --verbose 2
```

## Command-line arguments

- `-p`, `--problem`
  - Problem type to solve.
  - Allowed values: `FUSION`, `CRISTINA`, `NONSEPARABLE`

- `-s`, `--solver`
  - Solver mode.
  - Allowed values: `DAB`, `SA`

- `-i`, `--ifile`
  - Path to the input parameter XML file.

- `-c`, `--cfile`
  - Path to the runtime INI configuration file.

- `-t`, `--time`
  - Maximum execution time in seconds.
  - Default: `3600`

- `-v`, `--verbose`
  - Verbosity level for logging.
  - Allowed values: `1`, `2`, `3`

- `-m`, `--mock`
  - Run in mock mode without executing the actual problem evaluation.

- `--version`
  - Print the installed package version.

## Configuration

The tool reads runtime options from the config file passed in `--cfile`.

Example INI file:

```ini
[General]
commModel = DRIVERWORKER

[Algorithm]
objective = MIN
```

Supported configuration values:

- `commModel`
  - `DRIVERWORKER` (default)
  - `ALL2ALL`

- `objective`
  - `MIN` (default)
  - `MAX`

If the configuration file cannot be found or parsed, defaults are used.

## Sample data and configuration

The `data/` directory includes sample input files and configuration templates such as:

- `data/input.xml`
- `data/param_config.xml`
- `data/param_config_w7x.xml`
- `data/param_config_pressure.xml`

Use these as starting points for your own optimization runs.

## Testing

Run the repository test suite with:

```bash
python -m pytest tests --maxfail=1 -q
```

## CI

A GitHub Actions workflow is defined in `.github/workflows/python-tests.yml` to install dependencies via `pyproject.toml` and run unit tests.

## License

This project is licensed under the Apache License 2.0. See `LICENSE`.

## Changelog

See `CHANGELOG.md` for version history and release notes.
