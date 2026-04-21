import json
from pathlib import Path
from typing import Any, Dict, Tuple


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "configs" / "schemas"


class SchemaValidationError(ValueError):
    pass


def _load_schema(schema_name: str) -> Dict[str, Any]:
    schema_path = SCHEMA_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_payload(payload: Dict[str, Any], schema_name: str) -> Tuple[bool, str]:
    schema = _load_schema(schema_name)

    try:
        import jsonschema

        jsonschema.validate(instance=payload, schema=schema)
        return True, "ok"
    except ImportError:
        # Lightweight fallback: required-key check only.
        required = schema.get("required", [])
        missing = [key for key in required if key not in payload]
        if missing:
            return False, f"missing required fields: {missing}"
        return True, "ok (required-only fallback)"
    except Exception as exc:
        return False, str(exc)


def require_valid_payload(payload: Dict[str, Any], schema_name: str) -> None:
    valid, reason = validate_payload(payload, schema_name)
    if not valid:
        raise SchemaValidationError(f"Schema validation failed ({schema_name}): {reason}")
