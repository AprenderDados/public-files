# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC <div style="background:linear-gradient(135deg,#0077B6 0%,#2A9D8F 100%);color:#fff;padding:44px 38px;border-radius:14px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;box-shadow:0 6px 24px rgba(0,119,182,.25)">
# MAGIC   <div style="font-size:.85em;text-transform:uppercase;letter-spacing:.12em;opacity:.85;margin-bottom:8px">Azure Databricks DP-750 · bootstrap · ~2 min</div>
# MAGIC   <h1 style="font-size:2.4em;margin:0 0 14px;line-height:1.15;font-weight:700">Download the full course (EN)</h1>
# MAGIC   <p style="margin:0;font-size:1.1em;opacity:.95;line-height:1.55">This notebook is the entry point. Paste your <strong>access key</strong> and run every cell — the course's <strong>13 notebooks</strong> in English will appear in your workspace.</p>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="background:#fff;border:2px solid #0077B6;border-radius:10px;padding:24px 28px;font-family:-apple-system,sans-serif;margin:18px 0">
# MAGIC   <h3 style="margin:0 0 12px;color:#0077B6;font-size:1.2em">📋 What this notebook does</h3>
# MAGIC   <ol style="margin:0;padding-left:22px;color:#1D1F23;line-height:1.7">
# MAGIC     <li>Downloads an <strong>encrypted payload</strong> from a public repository</li>
# MAGIC     <li>Asks for your <strong>access key</strong> (delivered after purchase)</li>
# MAGIC     <li>Decrypts it in memory — the key never leaves your workspace</li>
# MAGIC     <li>Materializes the 13 notebooks into <code>dp750/en/</code></li>
# MAGIC   </ol>
# MAGIC </div>
# MAGIC <div style="padding:14px 20px;border-radius:8px;border-left:5px solid #C73E1D;background:#FFF0EC;font-family:-apple-system,sans-serif;margin:12px 0">
# MAGIC   <div style="font-weight:700;font-size:.8em;letter-spacing:.1em;color:#C73E1D;margin-bottom:6px">⚠️ PASTE YOUR KEY IN THE NEXT CELL</div>
# MAGIC   <p style="margin:0;color:#1D1F23;line-height:1.55">Without a valid key, this notebook fails on purpose. If you lost yours, reach out through your purchase channel.</p>
# MAGIC </div>

# COMMAND ----------

# 👇 PASTE YOUR ACCESS KEY HERE (between the quotes) 👇
ACCESS_KEY = ""  # 👇 paste your key here (ask your instructor or see the Setup lesson)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

import base64
import hashlib
import hmac
import json
import os
import urllib.request

PAYLOAD_URLS = [
    "https://raw.githubusercontent.com/AprenderDados/public-files/main/public-files/courses/dp750_en/payload.private.json",
]

PBKDF2_ITERATIONS = 200_000
PAYLOAD_VERSION = 1


def _xor_stream(data: bytes, key: bytes) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < len(data):
        block = hashlib.sha256(key + counter.to_bytes(4, "big")).digest()
        output.extend(block)
        counter += 1
    return bytes(d ^ k for d, k in zip(data, output))


def _derive(key: str, salt: bytes) -> tuple[bytes, bytes]:
    raw = hashlib.pbkdf2_hmac("sha256", key.encode(), salt, PBKDF2_ITERATIONS, dklen=64)
    return raw[:32], raw[32:]


def decode_payload(payload: dict, key: str) -> str:
    if payload.get("version") != PAYLOAD_VERSION:
        raise ValueError(f"Unsupported payload version: {payload.get('version')}")
    salt = base64.b64decode(payload["salt"])
    ct = base64.b64decode(payload["ciphertext"])
    mac = base64.b64decode(payload["mac"])
    enc_key, mac_key = _derive(key, salt)
    if not hmac.compare_digest(hmac.new(mac_key, ct, hashlib.sha256).digest(), mac):
        raise ValueError("Invalid key or corrupted payload")
    return _xor_stream(ct, enc_key).decode("utf-8")


def fetch_payload(urls: list[str], timeout: int = 30) -> dict:
    last = None
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            print(f"  - failed at {url}: {exc}")
            last = exc
    raise RuntimeError(f"Could not download from any URL: {last}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Key validation

# COMMAND ----------

assert ACCESS_KEY.strip(), "Paste your access key in the cell above before continuing."

print(f"Fetching payload from {len(PAYLOAD_URLS)} URL(s)...")
payload = fetch_payload(PAYLOAD_URLS)
print(f"Payload downloaded ({len(json.dumps(payload)):,} bytes). Decrypting...")

try:
    plaintext = decode_payload(payload, ACCESS_KEY.strip())
except ValueError as exc:
    raise SystemExit(f"❌ Failed: {exc}")

bundle = json.loads(plaintext)
metadata = bundle.get("metadata", {})
print(f"\n✅ Valid key.")
print(f"   Course:      {metadata.get('course', '?')}")
print(f"   Languages:   {', '.join(metadata.get('languages', []))}")
print(f"   Notebooks:   {metadata.get('notebook_count', len(bundle.get('notebooks', {})))}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Persist the key (for the Athena AI assistant)

# COMMAND ----------

try:
    _current_user = spark.sql("SELECT current_user()").first()[0]
    _key_path = f"/Workspace/Users/{_current_user}/.dp750_en_key"
    with open(_key_path, "w") as _kf:
        _kf.write(ACCESS_KEY.strip())
    print(f"🔑 Key persisted at {_key_path} — the assistant notebook (Athena) will load it automatically.")
except Exception as exc:
    print(f"⚠️  Could not persist the key automatically ({exc}). "
          f"Set SKILL_ACCESS_KEY manually in the assistant notebook if needed.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Materialize the notebooks into the workspace

# COMMAND ----------

notebook_path = (
    dbutils.notebook.entry_point
    .getDbutils().notebook().getContext().notebookPath().get()
)
target_root = "/Workspace" + os.path.dirname(notebook_path) + "/dp750"
os.makedirs(target_root, exist_ok=True)

new_files = set(bundle["notebooks"].keys())
for root, dirs, files in os.walk(target_root):
    for fname in files:
        if not fname.endswith(".py"):
            continue
        full = os.path.join(root, fname)
        rel  = os.path.relpath(full, target_root)
        if rel not in new_files:
            os.remove(full)
            print(f"  🗑  removed obsolete: {rel}")

written = []
for rel_path, content in bundle["notebooks"].items():
    target = os.path.join(target_root, rel_path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content)
    written.append(rel_path)

print(f"✅ Wrote {len(written)} notebooks to {target_root}\n")

by_lang: dict[str, list[str]] = {}
for rel_path in written:
    lang, _, name = rel_path.partition("/")
    by_lang.setdefault(lang, []).append(name)

for lang, names in sorted(by_lang.items()):
    print(f"📂 {lang}/ ({len(names)} notebooks)")
    for name in sorted(names):
        print(f"   - {name}")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="background:linear-gradient(135deg,#0077B6,#2A9D8F);color:#fff;padding:28px 32px;border-radius:14px;font-family:-apple-system,sans-serif;margin:24px 0;text-align:center">
# MAGIC   <div style="font-size:2.4em;margin-bottom:8px">🎉</div>
# MAGIC   <h2 style="margin:0 0 12px;color:#fff;font-size:1.6em;border:none">All set!</h2>
# MAGIC   <p style="margin:0;font-size:1.05em;opacity:.95;line-height:1.55">Open the <strong>dp750/</strong> folder in your workspace.<br>Start with the first notebook in <code>en/</code> and follow the numeric order.</p>
# MAGIC </div>
