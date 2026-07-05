# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC <div style="background:linear-gradient(135deg,#0077B6 0%,#2A9D8F 100%);color:#fff;padding:44px 38px;border-radius:14px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;box-shadow:0 6px 24px rgba(0,119,182,.25)">
# MAGIC   <div style="font-size:.85em;text-transform:uppercase;letter-spacing:.12em;opacity:.85;margin-bottom:8px">Azure Databricks DP-750 · bootstrap · ~2 min</div>
# MAGIC   <h1 style="font-size:2.4em;margin:0 0 14px;line-height:1.15;font-weight:700">Baixar curso completo (PT-BR)</h1>
# MAGIC   <p style="margin:0;font-size:1.1em;opacity:.95;line-height:1.55">Este notebook é a porta de entrada. Cole sua <strong>chave de acesso</strong> e rode todas as células — os <strong>13 notebooks</strong> do curso em português vão aparecer no seu workspace.</p>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="background:#fff;border:2px solid #0077B6;border-radius:10px;padding:24px 28px;font-family:-apple-system,sans-serif;margin:18px 0">
# MAGIC   <h3 style="margin:0 0 12px;color:#0077B6;font-size:1.2em">📋 O que este notebook faz</h3>
# MAGIC   <ol style="margin:0;padding-left:22px;color:#1D1F23;line-height:1.7">
# MAGIC     <li>Baixa um <strong>payload criptografado</strong> de um repositório público</li>
# MAGIC     <li>Pede sua <strong>chave de acesso</strong> (entregue após a compra)</li>
# MAGIC     <li>Descriptografa em memória — a chave nunca sai do seu workspace</li>
# MAGIC     <li>Materializa os 13 notebooks em <code>dp750/pt_br/</code></li>
# MAGIC   </ol>
# MAGIC </div>
# MAGIC <div style="padding:14px 20px;border-radius:8px;border-left:5px solid #C73E1D;background:#FFF0EC;font-family:-apple-system,sans-serif;margin:12px 0">
# MAGIC   <div style="font-weight:700;font-size:.8em;letter-spacing:.1em;color:#C73E1D;margin-bottom:6px">⚠️ COLE SUA CHAVE NA PRÓXIMA CÉLULA</div>
# MAGIC   <p style="margin:0;color:#1D1F23;line-height:1.55">Sem chave válida, este notebook falha de propósito. Se você perdeu a sua, entre em contato pelo canal da compra.</p>
# MAGIC </div>

# COMMAND ----------

# 👇 COLE SUA CHAVE DE ACESSO AQUI (entre as aspas) 👇
ACCESS_KEY = "DP750-PT-2026"  # ⚠️ modo teste — substituir por "" antes do lançamento

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
    "https://raw.githubusercontent.com/AprenderDados/public-files/main/public-files/courses/dp750_pt/payload.private.json",
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
        raise ValueError(f"Versão de payload não suportada: {payload.get('version')}")
    salt = base64.b64decode(payload["salt"])
    ct = base64.b64decode(payload["ciphertext"])
    mac = base64.b64decode(payload["mac"])
    enc_key, mac_key = _derive(key, salt)
    if not hmac.compare_digest(hmac.new(mac_key, ct, hashlib.sha256).digest(), mac):
        raise ValueError("Chave inválida ou payload corrompido")
    return _xor_stream(ct, enc_key).decode("utf-8")


def fetch_payload(urls: list[str], timeout: int = 30) -> dict:
    last = None
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            print(f"  - falha em {url}: {exc}")
            last = exc
    raise RuntimeError(f"Não consegui baixar de nenhuma URL: {last}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validação da chave

# COMMAND ----------

assert ACCESS_KEY.strip(), "Cole sua chave de acesso na célula acima antes de continuar."

print(f"Buscando payload em {len(PAYLOAD_URLS)} URL(s)...")
payload = fetch_payload(PAYLOAD_URLS)
print(f"Payload baixado ({len(json.dumps(payload)):,} bytes). Descriptografando...")

try:
    plaintext = decode_payload(payload, ACCESS_KEY.strip())
except ValueError as exc:
    raise SystemExit(f"❌ Falha: {exc}")

bundle = json.loads(plaintext)
metadata = bundle.get("metadata", {})
print(f"\n✅ Chave válida.")
print(f"   Curso:      {metadata.get('course', '?')}")
print(f"   Idiomas:    {', '.join(metadata.get('languages', []))}")
print(f"   Notebooks:  {metadata.get('notebook_count', len(bundle.get('notebooks', {})))}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Persistir a chave (para o assistente AI Athena)

# COMMAND ----------

try:
    _current_user = spark.sql("SELECT current_user()").first()[0]
    _key_path = f"/Workspace/Users/{_current_user}/.dp750_pt_key"
    with open(_key_path, "w") as _kf:
        _kf.write(ACCESS_KEY.strip())
    print(f"🔑 Chave persistida em {_key_path} — o notebook do assistente (Athena) vai carregá-la automaticamente.")
except Exception as exc:
    print(f"⚠️  Não foi possível persistir a chave automaticamente ({exc}). "
          f"Defina SKILL_ACCESS_KEY manualmente no notebook do assistente se precisar.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Materializar os notebooks no workspace

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
            print(f"  🗑  removido obsoleto: {rel}")

written = []
for rel_path, content in bundle["notebooks"].items():
    target = os.path.join(target_root, rel_path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content)
    written.append(rel_path)

print(f"✅ Gravados {len(written)} notebooks em {target_root}\n")

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
# MAGIC   <h2 style="margin:0 0 12px;color:#fff;font-size:1.6em;border:none">Tudo pronto!</h2>
# MAGIC   <p style="margin:0;font-size:1.05em;opacity:.95;line-height:1.55">Abra a pasta <strong>dp750/</strong> no seu workspace.<br>Comece pelo primeiro notebook em <code>pt_br/</code> e siga a ordem dos números.</p>
# MAGIC </div>
