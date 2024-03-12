# Ufa University of Science and Technology Schedule

[![Main workflow](https://github.com/GuFFy12/UUST-Schedule/actions/workflows/main.yml/badge.svg)](https://github.com/GuFFy12/UUST-Schedule/actions)
[![codecov](https://codecov.io/gh/GuFFy12/UUST-Schedule/graph/badge.svg?token=X4V0UI1116)](https://codecov.io/gh/GuFFy12/UUST-Schedule)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![MyPy](https://img.shields.io/badge/%20type_checker-mypy-%231674b1?style=flat)](https://mypy-lang.org)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## 📅 Враппер для Расписания УУНИТ!

## Установка

```bash
pip install git+https://github.com/GuFFy12/UUST-Schedule.git@$(curl -s "https://api.github.com/repos/GuFFy12/UUST-Schedule/releases/latest" | grep -o '"tag_name": "\([^"]*\)"' | cut -d'"' -f4)
```

## Пример

```python
from uust_schedule import Schedule, ParticipantType, SemesterType

print(list(Schedule(ParticipantType.GROUP, 2575, 2023).get_events(SemesterType.AUTUMN)))
```