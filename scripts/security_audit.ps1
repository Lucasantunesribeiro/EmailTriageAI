python -m pip install -r requirements-dev.txt
pip-audit
bandit -r app
ruff check app tests
black --check app tests
