# scripts/export_openapi.py
import yaml
from physense_api.main import app

openapi = app.openapi()

with open("openapi.yaml", "w") as f:
    yaml.dump(openapi, f, allow_unicode=True, sort_keys=False)

print("openapi.yaml exported")