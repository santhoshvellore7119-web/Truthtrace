import re
p = "api/main.py"
s = open(p, encoding="utf-8").read()
if "CORSMiddleware" not in s:
    s = s.replace("from fastapi import FastAPI", "from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware", 1)
    s = re.sub(r"(app\s*=\s*FastAPI\([^)]*\))", r"\1\n\napp.add_middleware(\n    CORSMiddleware,\n    allow_origins=[\"http://localhost:3000\"],\n    allow_methods=[\"*\"],\n    allow_headers=[\"*\"],\n)", s, count=1)
    open(p, "w", encoding="utf-8").write(s)
    print("CORS patched")
else:
    print("CORS already present")
