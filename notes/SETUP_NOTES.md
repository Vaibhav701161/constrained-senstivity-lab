# Setup Notes

OS: Linux
Python version: Python 3.12.3
pip version: pip 26.2 in `.venv`
Install command: `python3 -m venv .venv && .venv/bin/python -m pip install --upgrade pip && .venv/bin/pip install -r requirements.txt`
Did torch install? yes
Did transformers import? yes
Errors:
- System Python does not have the dependencies. Activate `.venv` first.
- CUDA is not available: the NVIDIA driver is older than the CUDA runtime in the installed torch wheel. CPU works.
