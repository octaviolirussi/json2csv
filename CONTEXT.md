# CONTEXT.md – json2csv

> Este archivo está diseñado para ser incluido como contexto al inicio de
> cualquier sesión de **Vibe Coding** (asistencia por IA).  Proporciona al
> modelo la información estructural, técnica y de convenciones del proyecto
> necesaria para generar código coherente con el resto de la base de código.

---

## Descripción del proyecto

**json2csv** es un paquete Python que convierte archivos JSON (arrays de
objetos) a formato CSV.  Es el proyecto inverso de `csv2json` del mismo
repositorio de referencia (UFASTA – Calidad de Software).

- **Versión actual:** `1.0.0 build 000`
- **Python:** `3.13` (no compatible con versiones anteriores)
- **Licencia:** MIT

---

## Estructura de directorios relevante

```
src/json2csv/
  __init__.py      # Exporta la API pública
  converter.py     # Lógica de dominio (sin efectos secundarios de I/O salvo convert_file)
  cli.py           # Capa CLI (argparse), delega todo a converter.py
  _version.py      # __version__ y __build__
tests/
  test_converter.py
  test_cli.py
docs/site/         # Generado por pdoc (no editar manualmente)
ejemplos/          # Datos de ejemplo (excluidos del workflow)
script/            # Utilidades auxiliares (excluidas del workflow)
.github/workflows/ci.yml
```

---

## API pública

```python
from json2csv import convert_records, convert_string, convert_file
from json2csv import (
    Json2CsvError, EmptyDataError, InvalidJsonStructureError,
    FileReadError, FileWriteError,
)
```

### `convert_records(records, *, flatten, sep, dialect, extrasaction) -> str`
Convierte una lista de `dict` a texto CSV.  Lanza `EmptyDataError` si la lista
está vacía e `InvalidJsonStructureError` si algún elemento no es `dict`.

### `convert_string(json_string, *, flatten, sep, dialect) -> str`
Parsea un string JSON y delega a `convert_records`.  Lanza `FileReadError` si
el JSON es inválido.

### `convert_file(source, destination, *, flatten, sep, dialect, encoding) -> int`
Lee `source`, escribe `destination`, devuelve cantidad de filas de datos.
Lanza `FileReadError` o `FileWriteError` según corresponda.

---

## Excepciones

| Excepción                  | Cuándo se lanza                                        |
|----------------------------|--------------------------------------------------------|
| `Json2CsvError`            | Clase base; captura cualquier error del paquete.       |
| `EmptyDataError`           | El array JSON no contiene elementos.                   |
| `InvalidJsonStructureError`| La raíz JSON no es un array, o contiene no-dicts.      |
| `FileReadError`            | El archivo fuente no existe, no se puede leer, o JSON inválido. |
| `FileWriteError`           | El archivo destino no se puede escribir.               |

---

## Convenciones de código

- **PEP 8** estricto; línea máxima 88 caracteres (`black` + `ruff`).
- **PEP 257** para docstrings; convención `pep257`; se ignoran D203 y D213.
- **Anotaciones de tipo** en todas las funciones y variables públicas.
- `from __future__ import annotations` al inicio de cada módulo.
- `str | Path` para parámetros de ruta.
- Nada de `Any` en la API pública si se puede evitar.
- Uso de `logger = logging.getLogger(__name__)` (no `print` en módulos de dominio).

---

## Herramientas de calidad

| Herramienta | Uso                              | Comando                               |
|-------------|----------------------------------|---------------------------------------|
| `ruff`      | Lint + formato                   | `ruff check src tests`                |
| `black`     | Formato consistente              | `black --check src tests`             |
| `mypy`      | Tipado estático                  | `mypy src tests`                      |
| `pyright`   | Tipado estático (strict)         | `pyright src tests`                   |
| `pytest`    | Tests unitarios (≥85 % cov.)     | `pytest`                              |
| `bandit`    | Seguridad                        | `bandit -r src -c pyproject.toml`     |
| `pdoc`      | Documentación                    | `pdoc --output-directory docs/site src/json2csv` |

**Regla de oro:** todo PR debe pasar los siete controles sin errores ni
advertencias.

---

## CI/CD (GitHub Actions)

Pipeline en `.github/workflows/ci.yml` con tres jobs encadenados:

1. **quality** → ruff lint, ruff format, black, mypy, pyright, bandit
2. **test** → pytest + cobertura ≥ 85 %
3. **docs** → pdoc + deploy a GitHub Pages (solo en `push` a `main`)

---

## Notas para el modelo de IA

- No generar código con `print()` dentro de `converter.py`; usar `logger`.
- No agregar dependencias de terceros en tiempo de ejecución; el paquete
  usa únicamente stdlib (`csv`, `json`, `pathlib`, `logging`, `io`).
- Al agregar tests, usar `tmp_path` (fixture de pytest) para archivos temporales.
- Usar `hypothesis` para casos con múltiples entradas; estrategias en
  `st.fixed_dictionaries` o `st.dictionaries`.
- Cualquier nueva función pública debe tener docstring PEP 257 con `Args`,
  `Returns` y `Raises`.
- Actualizar `CHANGELOG.md` con cada cambio significativo.
- Incrementar `__version__` y `__build__` en `_version.py` al hacer release.
