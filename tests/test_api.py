import json
import requests

# 1) Carga tu JSON
with open("example_profile.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

# 2) POST para crear/actualizar
res = requests.post("http://127.0.0.1:8000/lawyers/", json=payload)
print("POST status:", res.status_code)
print(res.json())

# 3) GET para verificar
code = payload["code"]
res2 = requests.get(f"http://127.0.0.1:8000/lawyers/{code}")
print("GET status:", res2.status_code)
print(res2.json())
