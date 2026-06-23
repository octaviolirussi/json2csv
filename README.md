# json2csv


## Estado

| Campo      | Valor              |
|------------|--------------------|
| Versión    | `1.0.0 build 000`  |
| Python     | `3.13`             |
| Licencia   | MIT                |
| CI         | GitHub Actions     |
| Cobertura  | ≥ 85 %             |




## Funciones disponibles

- Conversión de arrays JSON de objetos a CSV en memoria.
- Conversión de archivos `.json` a archivos `.csv`.
- Aplanamiento (*flatten*) opcional de objetos/arrays anidados con separador configurable.
- CLI separada de la lógica de dominio, con códigos de salida descriptivos.
- Validaciones robustas y excepciones tipadas para todas las condiciones de error.
- Tipado estático completo (MyPy + PyRight en modo `strict`).
- Pruebas con Pytest + Hypothesis (cobertura ≥ 85 %).
- Análisis de seguridad con Bandit.
- Documentación automática con pdoc, publicada en GitHub Pages.

---

## Estructura

```
src/json2csv/   paquete Python principal
  __init__.py   API pública
  converter.py  lógica de conversión (dominio)
  cli.py        interfaz de línea de comandos
  _version.py   VERSION y BUILD
tests/          pruebas automáticas (pytest + hypothesis)
docs/           documentación base y salida generada (pdoc)
ejemplos/       archivos de ejemplo (fuera del alcance del workflow)
script/         utilidades auxiliares (fuera del alcance del workflow)
.github/
  workflows/
    ci.yml      pipeline CI/CD completo
```

---

## Instalación rápida

```bash
python3.13 -m venv .venv313
source .venv313/bin/activate
pip install -r requirements.txt
pip install -e .
```

---

## Uso desde la CLI

```bash
# Conversión básica
json2csv data.json --output result.csv

# Con aplanamiento de estructuras anidadas
json2csv nested.json --output flat.csv --flatten

# Separador personalizado
json2csv nested.json --output flat.csv --flatten --sep __

# Ver ayuda
json2csv --help
```

**Códigos de salida:**

| Código | Significado                          |
|--------|--------------------------------------|
| `0`    | Éxito                                |
| `1`    | Error leyendo el archivo fuente      |
| `2`    | Error escribiendo el archivo destino |
| `3`    | Error en la estructura de los datos  |
| `4`    | Error genérico de conversión         |

---

## Uso desde Python

```python
from json2csv import convert_records, convert_string, convert_file

# Desde una lista de dicts
csv_text = convert_records([{"name": "Ana", "age": 30}])

# Desde un string JSON
csv_text = convert_string('[{"city": "MdP", "pop": 700000}]')

# Desde/hacia archivos
rows_written = convert_file("input.json", "output.csv", flatten=True)
```

---

## Calidad local

```bash
# Activar entorno
source .venv313/bin/activate

# Linting y formato
ruff check src tests
ruff format --check src tests
black --check src tests

# Tipado estático
mypy src tests
pyright src tests

# Tests con cobertura
pytest

# Seguridad
bandit -r src -c pyproject.toml
```

---

## Documentación

```bash
pdoc --output-directory docs/site src/json2csv
```

La documentación se genera y publica automáticamente en GitHub Pages con cada
PR exitoso fusionado a `main`.

---

## Licencia

MIT – ver archivo `LICENSE`.
