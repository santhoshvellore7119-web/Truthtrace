p = "api/main.py"
s = open(p, encoding="utf-8").read()

# Fix 1: remove literal backslashes before quotes (from the broken patch)
s = s.replace(chr(92) + chr(34), chr(34))

# Fix 2: fix the mangled import lines
s = s.replace(
    "from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware, HTTPException",
    "from fastapi import FastAPI, HTTPException\nfrom fastapi.middleware.cors import CORSMiddleware"
)

open(p, "w", encoding="utf-8").write(s)
print("fixed")
