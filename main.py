import os
from pathlib import Path

import yaml
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE = Path(__file__).parent
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

DEFAULTS = {"port": 8000, "workers": 1, "debug": False,
            "log_level": "info", "api_key": "default-secret-000"}
ALIASES = {"num_workers": "workers"}


def norm(key):
    key = key.strip().lower()
    return ALIASES.get(key, key)


def load_yaml():
    path = BASE / "config.development.yaml"
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return {norm(k): v for k, v in data.items()}
    return {}


def load_dotenv():
    out = {}
    path = BASE / ".env"
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        if k.upper().startswith("APP_"):
            k = k[4:]
        out[norm(k)] = v.strip().strip('"').strip("'")
    return out


def load_os_env():
    return {norm(k[4:]): v for k, v in os.environ.items()
            if k.startswith("APP_")}


def coerce(cfg):
    for key in ("port", "workers"):
        try:
            cfg[key] = int(str(cfg[key]).strip())
        except (ValueError, KeyError):
            pass
    cfg["debug"] = str(cfg.get("debug", False)).strip().lower() in {"true", "1", "yes", "on"}
    for key in cfg:
        if key not in ("port", "workers", "debug"):
            cfg[key] = str(cfg[key])
    return cfg


@app.get("/effective-config")
def effective_config(overrides: list[str] = Query(default=[], alias="set")):
    cfg = dict(DEFAULTS)
    cfg.update(load_yaml())
    cfg.update(load_dotenv())
    cfg.update(load_os_env())
    for item in overrides:
        if "=" in item:
            k, v = item.split("=", 1)
            cfg[norm(k)] = v
    cfg = coerce(cfg)
    cfg["api_key"] = "****"
    return cfg
