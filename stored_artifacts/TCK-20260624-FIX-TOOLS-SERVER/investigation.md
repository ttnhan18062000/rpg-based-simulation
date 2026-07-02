---
status: active
ticket_id: TCK-20260624-FIX-TOOLS-SERVER
artifact_type: investigation
---

# Investigation — TCK-20260624-FIX-TOOLS-SERVER

## Fix 1: Graceful Degradation Exit Codes

**File:** `tools/knowledge_search.py`

**`cmd_build` (line ~621-629):**
```python
except ImportError as exc:
    pkg = "sentence-transformers" if "sentence_transformers" in str(exc) else "sqlite-vec"
    print(f"Error: {pkg} not installed ...", file=sys.stderr)
    return 1  # BUG: AC7 requires exit 0
```

**`cmd_query` (line ~956-965):**
```python
except ImportError as exc:
    pkg = "sentence-transformers" if "sentence_transformers" in str(exc) else "sqlite-vec"
    print(f"Error: {pkg} not installed ...", file=sys.stderr)
    return 1  # BUG: AC7 requires exit 0
```

Fix: Change `"Error:"` → `"Warning:"` and `return 1` → `return 0` in both branches.
The AC7 graceful-degradation contract requires exit 0 when optional deps are missing.

## Fix 2: .mcp.json Absolute Venv Path

**File:** `.mcp.json`

```json
"command": "/home/vboxuser/Work/venv/bin/python3"
```

This is machine-specific. The portability contract and `test_command_is_python3` assert
`"command": "python3"`. The venv is made accessible by adding it to PATH via `"env"`.

Fix: Change command to `"python3"`, add `"env": {"PATH": "/home/vboxuser/Work/venv/bin:..."}`.

## Fix 3: TestClient Lifespan Timing

**File:** `tests/tools/test_search_server.py`

**Root cause:** The `knowledge-index/` directory exists on the dev machine with a real DB.
The FastAPI lifespan startup in `tools/search_server.py` (line 55) checks:
```python
if not _INDEX_DIR.exists() or not _DB_PATH.exists():
    yield  # degraded mode
    return
import sentence_transformers
_APP_STATE.model = sentence_transformers.SentenceTransformer(_MODEL_NAME)  # LOADS MODEL
```

When `_INDEX_DIR` exists, the lifespan bypasses degraded mode and tries to load
`SentenceTransformer`. This happens inside `TestClient.__enter__()`. The `monkeypatch`
for `_APP_STATE` was correctly placed before `TestClient`, but `_DB_PATH` / `_INDEX_DIR`
were not patched, so the lifespan saw the real paths and proceeded to load the model.

Fix: Also patch `_DB_PATH` and `_INDEX_DIR` to nonexistent paths before opening TestClient,
so the lifespan takes the degraded-mode branch (yields without loading model).
The endpoint check `if not _APP_STATE.ready:` then returns 503 as expected.
