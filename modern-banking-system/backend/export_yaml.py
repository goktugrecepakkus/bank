import yaml
from main import app

openapi_schema = app.openapi()

with open("api.yaml", "w") as file:
    yaml.dump(openapi_schema, file, sort_keys=False)
