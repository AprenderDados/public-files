# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC <div style="background:linear-gradient(135deg,#E63946 0%,#F77F00 100%);color:#fff;padding:44px 38px;border-radius:14px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;box-shadow:0 6px 24px rgba(230,57,70,.25)">
# MAGIC   <div style="font-size:.85em;text-transform:uppercase;letter-spacing:.12em;opacity:.85;margin-bottom:8px">Novo Associate 2026 &middot; bootstrap &middot; ~2 min</div>
# MAGIC   <h1 style="font-size:2.4em;margin:0 0 14px;line-height:1.15;font-weight:700">Baixar curso completo (PT-BR)</h1>
# MAGIC   <p style="margin:0;font-size:1.1em;opacity:.95;line-height:1.55">Cole sua <strong>chave de acesso</strong> e rode todas as c&#xE9;lulas &mdash; os <strong>16 notebooks</strong> v&#xE3;o aparecer diretamente em <code>novo_associate/</code> no seu workspace.</p>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="background:#fff;border:2px solid #E63946;border-radius:10px;padding:24px 28px;font-family:-apple-system,sans-serif;margin:18px 0">
# MAGIC   <h3 style="margin:0 0 12px;color:#E63946;font-size:1.2em">&#x1F4CB; O que este notebook faz</h3>
# MAGIC   <ol style="margin:0;padding-left:22px;color:#1D1F23;line-height:1.7">
# MAGIC     <li>Baixa payload criptografado (~700 KB) do reposit&#xF3;rio p&#xFA;blico</li>
# MAGIC     <li>Descriptografa em mem&#xF3;ria com sua chave &mdash; nunca sai do workspace</li>
# MAGIC     <li>Materializa os 16 notebooks diretamente em <code>novo_associate/</code></li>
# MAGIC     <li>Persiste a chave para a Athena (notebook 15) encontrar automaticamente</li>
# MAGIC   </ol>
# MAGIC </div>
# MAGIC <div style="padding:14px 20px;border-radius:8px;border-left:5px solid #C73E1D;background:#FFF0EC;font-family:-apple-system,sans-serif;margin:12px 0">
# MAGIC   <div style="font-weight:700;font-size:.8em;letter-spacing:.1em;color:#C73E1D;margin-bottom:6px">&#x26A0;&#xFE0F; COLE SUA CHAVE NA PR&#xD3;XIMA C&#xC9;LULA</div>
# MAGIC   <p style="margin:0;color:#1D1F23;line-height:1.55">Sem chave v&#xE1;lida, o notebook falha de prop&#xF3;sito. Se perdeu a sua, entre em contato pelo canal da compra.</p>
# MAGIC </div>

# COMMAND ----------

# &#x1F447; COLE SUA CHAVE DE ACESSO AQUI &#x1F447;
ACCESS_KEY = "NOVO-ASSOCIATE-PT-2026"  # &#x26A0;&#xFE0F; modo teste

# COMMAND ----------

import base64
import hashlib
import hmac
import json
import os
import urllib.request

PAYLOAD_URLS = [
    "https://raw.githubusercontent.com/AprenderDados/public-files/main/public-files/courses/novo_associate_pt/payload.private.json",
]
PBKDF2_ITERATIONS = 200_000


def _xor_stream(data: bytes, key: bytes) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < len(data):
        block = hashlib.sha256(key + counter.to_bytes(4, "big")).digest()
        output.extend(block)
        counter += 1
    return bytes(d ^ k for d, k in zip(data, output))


def decode_payload(payload: dict, key: str) -> str:
    if payload.get("version") != 1:
        raise ValueError(f"Versao nao suportada: {payload.get('version')}")
    salt = base64.b64decode(payload["salt"])
    ct = base64.b64decode(payload["ciphertext"])
    mac = base64.b64decode(payload["mac"])
    raw = hashlib.pbkdf2_hmac("sha256", key.encode(), salt, PBKDF2_ITERATIONS, dklen=64)
    ek, mk = raw[:32], raw[32:]
    if not hmac.compare_digest(hmac.new(mk, ct, hashlib.sha256).digest(), mac):
        raise ValueError("Chave invalida ou payload corrompido")
    return _xor_stream(ct, ek).decode("utf-8")


def fetch_payload(urls: list, timeout: int = 30) -> dict:
    last = None
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            print(f"  - falha: {url}: {exc}")
            last = exc
    raise RuntimeError(f"Nao consegui baixar: {last}")

# COMMAND ----------

assert ACCESS_KEY.strip(), "Cole sua chave acima antes de continuar."
print(f"Buscando payload ({len(PAYLOAD_URLS)} URL)...")
payload = fetch_payload(PAYLOAD_URLS)
print(f"Baixado ({len(json.dumps(payload)):,} bytes). Descriptografando...")

try:
    plaintext = decode_payload(payload, ACCESS_KEY.strip())
except ValueError as exc:
    raise SystemExit(f"Falha: {exc}")

bundle = json.loads(plaintext)
meta   = bundle.get("metadata", {})
print(f"\nChave valida.")
print(f"   Curso:      {meta.get('course', '?')}")
print(f"   Notebooks:  {meta.get('notebook_count', len(bundle.get('notebooks', {})))}")

# COMMAND ----------

notebook_path = (
    dbutils.notebook.entry_point
    .getDbutils().notebook().getContext().notebookPath().get()
)
target_root = "/Workspace" + os.path.dirname(notebook_path) + "/novo_associate"
os.makedirs(target_root, exist_ok=True)

written = []
for rel_path, content in bundle["notebooks"].items():
    target = os.path.join(target_root, rel_path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content)
    written.append(rel_path)

print(f"Gravados {len(written)} notebooks em {target_root}\n")
for name in sorted(written):
    print(f"   - {name}")

# COMMAND ----------

# Persiste chave para a Athena encontrar automaticamente
try:
    _user = spark.sql("SELECT current_user()").first()[0]
    _kpath = f"/Workspace/Users/{_user}/.novo_associate_pt_key"
    with open(_kpath, "w") as kf:
        kf.write(ACCESS_KEY.strip())
    print(f"Chave persistida em {_kpath}")
    print("   A Athena (notebook 15) vai encontra-la automaticamente.")
except Exception as e:
    print(f"Nao foi possivel persistir a chave: {e}")
    print("   Defina SKILL_ACCESS_KEY manualmente no notebook 15.")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="background:linear-gradient(135deg,#E63946,#F77F00);color:#fff;padding:28px 32px;border-radius:14px;font-family:-apple-system,sans-serif;margin:24px 0;text-align:center">
# MAGIC   <div style="font-size:2.4em;margin-bottom:8px">&#x1F389;</div>
# MAGIC   <h2 style="margin:0 0 12px;color:#fff;font-size:1.6em;border:none">Tudo pronto!</h2>
# MAGIC   <p style="margin:0;font-size:1.05em;opacity:.95;line-height:1.55">Abra <strong>novo_associate/</strong> no seu workspace.<br>Comece pelo <code>00_introducao_ao_databricks.py</code> e siga a ordem dos n&#xFA;meros.<br>Use <code>15_assistente_ai_athena.py</code> para tirar d&#xFA;vidas com a Athena.</p>
# MAGIC </div>
