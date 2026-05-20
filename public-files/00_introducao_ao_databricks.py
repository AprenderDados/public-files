# Databricks notebook source
# MAGIC %md
# MAGIC ![Aprenda com Databricks Free Edition](https://raw.githubusercontent.com/AprenderDados/public-files/main/public-files/aulas/novo-associate/capas/aprenda_com_databricks_free_edition.png)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC # Módulo 00
# MAGIC ## Introdução ao Databricks
# MAGIC
# MAGIC Este caderno é a primeira prática do curso **Novo Associate**.
# MAGIC
# MAGIC A proposta é criar um modelo mental completo da plataforma Databricks usando uma demonstração pequena, executável e reproduzível.

# COMMAND ----------

# MAGIC %md
# MAGIC ## O que você vai praticar
# MAGIC
# MAGIC Ao longo deste notebook, você vai ver como as principais peças do Databricks se conectam:
# MAGIC
# MAGIC | Peça | Papel no Databricks | Como aparece neste notebook |
# MAGIC |---|---|---|
# MAGIC | Workspace | lugar onde você organiza notebooks e ativos | este próprio caderno |
# MAGIC | Compute | recurso que executa código e consultas | sessão Spark usada nas células |
# MAGIC | Storage | local onde arquivos e tabelas ficam persistidos | Volume criado automaticamente |
# MAGIC | Spark | motor de processamento distribuído | DataFrames, SQL e transformações |
# MAGIC | Delta Lake | camada transacional para tabelas confiáveis | tabelas Bronze, Prata e Ouro |
# MAGIC | Unity Catalog | governança e organização de objetos | `catalog.schema.table` e Volume |
# MAGIC | Lakeflow Jobs | orquestração de tarefas | plano de tarefas ao final |
# MAGIC | Spark Declarative Pipelines | pipelines declarativos | funções de transformação reutilizáveis |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pré-requisitos
# MAGIC
# MAGIC Este notebook foi desenhado para Databricks Free Edition ou workspace Databricks com Unity Catalog.
# MAGIC
# MAGIC Ele tenta criar automaticamente:
# MAGIC
# MAGIC - um schema de apoio
# MAGIC - um Volume de apoio
# MAGIC - arquivos sintéticos de entrada
# MAGIC - tabelas Delta governadas pelo catálogo
# MAGIC
# MAGIC Se o seu workspace não permitir criação de schema, volume ou tabela, o erro vai indicar qual permissão está faltando.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Entendendo a sessão atual
# MAGIC
# MAGIC Antes de criar dados, vamos observar em qual contexto o notebook está rodando.
# MAGIC
# MAGIC Isso reforça uma ideia central: código Databricks não roda “solto”. Ele sempre executa dentro de uma sessão, com usuário, catálogo, schema e compute associado.

# COMMAND ----------

import re

from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType
from pyspark.sql.window import Window

session_context_df = spark.sql(
    """
    SELECT
      current_user() AS usuario_atual,
      current_catalog() AS catalogo_atual,
      current_schema() AS schema_atual,
      current_timestamp() AS timestamp_execucao
    """
)

display(session_context_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.1. Como trabalhar com este caderno
# MAGIC
# MAGIC Databricks notebooks são instrumentos de aprendizado, exploração e operação.
# MAGIC
# MAGIC Neste curso, use o notebook de cima para baixo. Isso reduz erros causados por células executadas fora de ordem.
# MAGIC
# MAGIC Pontos importantes:
# MAGIC
# MAGIC - células `%md` explicam o conceito;
# MAGIC - células Python executam lógica com Spark;
# MAGIC - células `%sql` executam consultas SQL no mesmo contexto;
# MAGIC - `display()` deve ser usado para visualizar DataFrames e resultados tabulares;
# MAGIC - variáveis criadas em Python podem ser usadas por outras células Python posteriores;
# MAGIC - views temporárias criadas no notebook podem ser consultadas por células SQL posteriores;
# MAGIC - em produção, o notebook normalmente vira uma tarefa em Lakeflow Jobs ou chama código versionado em um projeto.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Preparando um ambiente reproduzível
# MAGIC
# MAGIC O curso assume que você pode começar em um ambiente praticamente zerado.
# MAGIC
# MAGIC Por isso, este notebook cria um Volume e tabelas próprias para a aula.
# MAGIC
# MAGIC O Volume será usado para simular uma área de arquivos de entrada. As tabelas Delta serão usadas para demonstrar a arquitetura Lakehouse.
# MAGIC
# MAGIC Para evitar colisão entre pessoas no mesmo workspace, o notebook isola os objetos por usuário usando schema e caminhos próprios.

# COMMAND ----------

def ensure_course_volume(volume_name: str, preferred_schema: str):
    current_catalog = spark.sql("SELECT current_catalog()").first()[0]
    current_schema = spark.sql("SELECT current_schema()").first()[0]

    candidates = []
    for catalog in [current_catalog, "workspace", "main"]:
        for schema in [preferred_schema, "aprender_dados", current_schema, "default"]:
            candidate = (catalog, schema, volume_name)
            if candidate not in candidates:
                candidates.append(candidate)

    errors = []
    for catalog, schema, volume in candidates:
        try:
            spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
            spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.{volume}")
            return catalog, schema, volume, f"/Volumes/{catalog}/{schema}/{volume}"
        except Exception as exc:
            errors.append(f"{catalog}.{schema}.{volume}: {str(exc).splitlines()[0]}")

    raise RuntimeError(
        "Não foi possível criar ou reutilizar um Volume para a aula de introdução.\n"
        f"Catálogo atual detectado: {current_catalog}\n"
        f"Schema atual detectado: {current_schema}\n"
        + "\n".join(errors)
    )


def reset_path(path: str) -> None:
    try:
        dbutils.fs.rm(path, True)
    except Exception:
        pass


def safe_identifier(value: str, max_length: int = 40) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_]", "_", value.lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        normalized = "student"
    if normalized[0].isdigit():
        normalized = f"u_{normalized}"
    return normalized[:max_length]


CURRENT_USER = spark.sql("SELECT current_user()").first()[0]
USER_PREFIX = safe_identifier(CURRENT_USER)
USER_SCHEMA = f"aprender_dados_{USER_PREFIX}"

CATALOG, SCHEMA, VOLUME, SHARED_BASE_PATH = ensure_course_volume(
    "novo_associate_intro",
    USER_SCHEMA,
)
BASE_PATH = f"{SHARED_BASE_PATH}/users/{USER_PREFIX}"

RAW_PATH = f"{BASE_PATH}/raw"

BRONZE_TABLE = f"{CATALOG}.{SCHEMA}.intro_bronze_pedidos"
SILVER_TABLE = f"{CATALOG}.{SCHEMA}.intro_silver_pedidos"
GOLD_TABLE = f"{CATALOG}.{SCHEMA}.intro_gold_receita_diaria"
DML_TABLE = f"{CATALOG}.{SCHEMA}.intro_delta_dml_demo"
GOLD_VIEW = f"{CATALOG}.{SCHEMA}.intro_vw_receita_diaria"

reset_path(RAW_PATH)

spark.sql(f"DROP VIEW IF EXISTS {GOLD_VIEW}")

for table_name in [BRONZE_TABLE, SILVER_TABLE, GOLD_TABLE, DML_TABLE]:
    spark.sql(f"DROP TABLE IF EXISTS {table_name}")

dbutils.fs.mkdirs(RAW_PATH)

setup_variables = {
    "CURRENT_USER": CURRENT_USER,
    "USER_PREFIX": USER_PREFIX,
    "USER_SCHEMA": USER_SCHEMA,
    "CATALOG": CATALOG,
    "SCHEMA": SCHEMA,
    "VOLUME": VOLUME,
    "BASE_PATH": BASE_PATH,
    "RAW_PATH": RAW_PATH,
    "BRONZE_TABLE": BRONZE_TABLE,
    "SILVER_TABLE": SILVER_TABLE,
    "GOLD_TABLE": GOLD_TABLE,
    "DML_TABLE": DML_TABLE,
    "GOLD_VIEW": GOLD_VIEW,
}

course_objects_df = spark.createDataFrame(
    [
        ("path", "raw_files", RAW_PATH),
        ("table", "bronze", BRONZE_TABLE),
        ("table", "silver", SILVER_TABLE),
        ("table", "gold", GOLD_TABLE),
        ("table", "delta_dml_demo", DML_TABLE),
        ("view", "gold_view", GOLD_VIEW),
    ],
    "object_type STRING, logical_name STRING, object_reference STRING",
)

display(course_objects_df)

# COMMAND ----------

print("Variáveis principais do módulo:")
for variable_name, variable_value in setup_variables.items():
    print(f"- {variable_name}: {variable_value}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Criando dados de entrada
# MAGIC
# MAGIC Para a aula ficar executável sem upload manual, vamos criar um pequeno dataset de pedidos.
# MAGIC
# MAGIC O arquivo contém problemas comuns de dados:
# MAGIC
# MAGIC - valores numéricos como texto
# MAGIC - status com variação de caixa
# MAGIC - registros duplicados
# MAGIC - valores nulos
# MAGIC - canais diferentes de venda
# MAGIC
# MAGIC Esses problemas são intencionais. Eles permitem mostrar por que uma arquitetura em camadas faz sentido.

# COMMAND ----------

orders_schema = StructType(
    [
        StructField("order_id", StringType(), False),
        StructField("customer_id", StringType(), False),
        StructField("order_ts", StringType(), True),
        StructField("channel", StringType(), True),
        StructField("amount", StringType(), True),
        StructField("status", StringType(), True),
        StructField("country", StringType(), True),
    ]
)

raw_orders_data = [
    ("O-001", "C-001", "2026-04-01 09:05:00", "web", "120.50", "paid", "BR"),
    ("O-002", "C-002", "2026-04-01 09:15:00", "mobile", "89.90", "PAID", "BR"),
    ("O-003", "C-003", "2026-04-01 10:10:00", "store", "45.00", "created", "PT"),
    ("O-004", "C-004", "2026-04-02 11:40:00", "web", "310.00", "paid", "US"),
    ("O-005", "C-005", "2026-04-02 12:10:00", "mobile", None, "cancelled", "BR"),
    ("O-006", "C-006", "2026-04-03 08:00:00", "web", "700.00", "paid", "NL"),
    ("O-006", "C-006", "2026-04-03 08:00:00", "web", "700.00", "paid", "NL"),
    ("O-007", "C-007", None, "mobile", "15.00", "paid", "BR"),
]

raw_orders_df = spark.createDataFrame(raw_orders_data, orders_schema)

display(raw_orders_df)

# COMMAND ----------

raw_orders_df.coalesce(1).write.mode("overwrite").option("header", True).csv(RAW_PATH)

print("Arquivo de entrada criado em:", RAW_PATH)
display(dbutils.fs.ls(RAW_PATH))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Lendo arquivos com Spark
# MAGIC
# MAGIC Agora vamos ler a pasta criada no Volume.
# MAGIC
# MAGIC Aqui aparece a primeira ideia prática de Spark: em vez de trabalhar com um arquivo local único, lemos um diretório de dados como um DataFrame distribuído.

# COMMAND ----------

source_df = (
    spark.read.option("header", True)
    .schema(orders_schema)
    .csv(RAW_PATH)
)

display(source_df)

# COMMAND ----------

source_df.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4.1. Inspecionando o dado antes de transformar
# MAGIC
# MAGIC Um bom pipeline começa com leitura crítica do dado.
# MAGIC
# MAGIC Antes de criar camadas, verifique:
# MAGIC
# MAGIC - quantidade total de linhas;
# MAGIC - quantidade de chaves distintas;
# MAGIC - valores nulos em campos importantes;
# MAGIC - possíveis duplicidades;
# MAGIC - campos que chegaram como texto, mas deveriam virar tipos fortes.

# COMMAND ----------

source_profile_df = source_df.agg(
    F.count("*").alias("total_linhas"),
    F.count("order_id").alias("linhas_com_order_id"),
    F.countDistinct("order_id").alias("pedidos_distintos"),
    F.sum(F.when(F.col("order_ts").isNull(), 1).otherwise(0)).alias("order_ts_nulos"),
    F.sum(F.when(F.col("amount").isNull(), 1).otherwise(0)).alias("amount_nulos"),
    F.sum(F.when(F.col("status").isNull(), 1).otherwise(0)).alias("status_nulos"),
)

display(source_profile_df)

# COMMAND ----------

duplicate_order_candidates_df = (
    source_df
    .groupBy("order_id")
    .agg(F.count("*").alias("quantidade"))
    .filter(F.col("quantidade") > 1)
    .orderBy("order_id")
)

display(duplicate_order_candidates_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Criando a camada Bronze
# MAGIC
# MAGIC Bronze é a camada de entrada.
# MAGIC
# MAGIC Nesta camada, o objetivo não é deixar tudo perfeito. O objetivo é preservar a chegada dos dados com rastreabilidade.
# MAGIC
# MAGIC Vamos adicionar metadados simples:
# MAGIC
# MAGIC - data e hora de ingestão
# MAGIC - caminho de origem do arquivo
# MAGIC - nome do módulo que gerou a ingestão

# COMMAND ----------

bronze_df = (
    source_df
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.col("_metadata.file_path"))
    .withColumn("_source_system", F.lit("intro_databricks_demo"))
)

display(bronze_df)

# COMMAND ----------

(
    bronze_df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", True)
    .saveAsTable(BRONZE_TABLE)
)

spark.sql(f"COMMENT ON TABLE {BRONZE_TABLE} IS 'Camada Bronze da aula de introdução ao Databricks'")

display(spark.table(BRONZE_TABLE))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5.1. Tabela gerenciada e metadados
# MAGIC
# MAGIC `saveAsTable()` registra uma tabela no catálogo.
# MAGIC
# MAGIC Neste notebook estamos criando tabelas gerenciadas. Isso significa que o Databricks controla os arquivos físicos por trás da tabela, enquanto você trabalha com o nome lógico `catalog.schema.table`.
# MAGIC
# MAGIC Essa separação é importante:
# MAGIC
# MAGIC - para o analista, a tabela é um objeto SQL;
# MAGIC - para o engenheiro, a tabela também é um conjunto de arquivos Delta;
# MAGIC - para a plataforma, a tabela é um ativo governado pelo Unity Catalog.

# COMMAND ----------

bronze_detail_df = spark.sql(f"DESCRIBE DETAIL {BRONZE_TABLE}").select(
    "format",
    "numFiles",
    "sizeInBytes",
    "location",
)

display(bronze_detail_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Entendendo Delta Lake
# MAGIC
# MAGIC A tabela Bronze foi gravada em Delta.
# MAGIC
# MAGIC Delta Lake adiciona confiabilidade sobre arquivos em storage. Na prática, isso significa:
# MAGIC
# MAGIC - histórico de operações
# MAGIC - schema da tabela
# MAGIC - suporte a DML
# MAGIC - melhor base para pipelines incrementais e reprocessamentos

# COMMAND ----------

display(spark.sql(f"DESCRIBE HISTORY {BRONZE_TABLE}"))

# COMMAND ----------

display(spark.sql(f"DESCRIBE TABLE EXTENDED {BRONZE_TABLE}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6.1. DDL e DML com Delta Lake
# MAGIC
# MAGIC Delta Lake permite trabalhar com tabelas usando comandos familiares de SQL.
# MAGIC
# MAGIC Dois grupos aparecem muito em engenharia de dados e na certificação:
# MAGIC
# MAGIC | Grupo | Exemplos | Para que serve |
# MAGIC |---|---|---|
# MAGIC | DDL | `CREATE TABLE`, `DROP TABLE`, `DESCRIBE` | definir e inspecionar objetos |
# MAGIC | DML | `INSERT`, `UPDATE`, `DELETE`, `MERGE` | modificar dados dentro das tabelas |
# MAGIC
# MAGIC O exemplo abaixo usa uma tabela pequena e separada apenas para demonstrar transações Delta. A tabela principal Bronze/Prata/Ouro não será alterada.

# COMMAND ----------

spark.sql(
    f"""
    CREATE OR REPLACE TABLE {DML_TABLE}
    (id INT, name STRING, score DOUBLE)
    """
)

spark.sql(
    f"""
    INSERT INTO {DML_TABLE}
    VALUES
      (1, 'Ana', 8.5),
      (2, 'Bruno', 7.0),
      (3, 'Carla', 9.2)
    """
)

display(spark.table(DML_TABLE).orderBy("id"))

# COMMAND ----------

spark.sql(
    """
    CREATE OR REPLACE TEMP VIEW intro_delta_updates(id, name, score, change_type) AS VALUES
      (2, 'Bruno', 8.0, 'update'),
      (3, 'Carla', NULL, 'delete'),
      (4, 'Diego', 7.8, 'insert')
    """
)

display(spark.table("intro_delta_updates").orderBy("id"))

# COMMAND ----------

spark.sql(
    f"""
    MERGE INTO {DML_TABLE} AS target
    USING intro_delta_updates AS source
    ON target.id = source.id
    WHEN MATCHED AND source.change_type = 'update'
      THEN UPDATE SET target.name = source.name, target.score = source.score
    WHEN MATCHED AND source.change_type = 'delete'
      THEN DELETE
    WHEN NOT MATCHED AND source.change_type = 'insert'
      THEN INSERT (id, name, score) VALUES (source.id, source.name, source.score)
    """
)

display(spark.table(DML_TABLE).orderBy("id"))

# COMMAND ----------

display(
    spark.sql(f"DESCRIBE HISTORY {DML_TABLE}")
    .select("version", "timestamp", "operation", "operationMetrics")
    .orderBy(F.desc("version"))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Criando a camada Prata
# MAGIC
# MAGIC Prata é a camada de qualidade operacional.
# MAGIC
# MAGIC Vamos resolver problemas comuns:
# MAGIC
# MAGIC - converter `amount` para número
# MAGIC - converter `order_ts` para timestamp
# MAGIC - padronizar `status`
# MAGIC - remover duplicidades
# MAGIC - criar flags de qualidade
# MAGIC
# MAGIC Esta etapa mostra por que PySpark é importante no dia a dia de engenharia de dados.

# COMMAND ----------

silver_df = (
    spark.table(BRONZE_TABLE)
    .withColumn("amount_decimal", F.col("amount").cast(DoubleType()))
    .withColumn("order_timestamp", F.to_timestamp("order_ts"))
    .withColumn("order_date", F.to_date("order_timestamp"))
    .withColumn("status_normalized", F.lower(F.trim("status")))
    .withColumn("channel_normalized", F.lower(F.trim("channel")))
    .withColumn("country", F.upper(F.trim("country")))
    .withColumn(
        "is_valid_order",
        F.col("order_id").isNotNull()
        & F.col("customer_id").isNotNull()
        & F.col("order_timestamp").isNotNull()
        & F.col("amount_decimal").isNotNull()
        & F.col("status_normalized").isin("created", "paid", "cancelled"),
    )
    .dropDuplicates(["order_id"])
)

display(silver_df)

# COMMAND ----------

(
    silver_df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", True)
    .saveAsTable(SILVER_TABLE)
)

spark.sql(f"COMMENT ON TABLE {SILVER_TABLE} IS 'Camada Prata da aula de introdução ao Databricks'")

display(spark.table(SILVER_TABLE))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Verificando qualidade dos dados
# MAGIC
# MAGIC Antes de criar uma camada Gold, vale medir a qualidade.
# MAGIC
# MAGIC Aqui não estamos usando uma ferramenta avançada de data quality. Estamos apenas criando checks simples para desenvolver o raciocínio.

# COMMAND ----------

quality_summary_df = (
    spark.table(SILVER_TABLE)
    .groupBy("is_valid_order")
    .agg(
        F.count("*").alias("quantidade_registros"),
        F.countDistinct("order_id").alias("pedidos_distintos"),
        F.sum(F.coalesce("amount_decimal", F.lit(0.0))).alias("valor_total_observado"),
    )
    .orderBy(F.desc("is_valid_order"))
)

display(quality_summary_df)

# COMMAND ----------

invalid_orders_df = (
    spark.table(SILVER_TABLE)
    .filter(~F.col("is_valid_order"))
    .select(
        "order_id",
        "customer_id",
        "order_ts",
        "amount",
        "status",
        "order_timestamp",
        "amount_decimal",
        "is_valid_order",
    )
)

display(invalid_orders_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Criando a camada Ouro
# MAGIC
# MAGIC Ouro é a camada de consumo.
# MAGIC
# MAGIC Aqui vamos criar uma tabela de receita diária por canal, pronta para dashboard ou análise SQL.
# MAGIC
# MAGIC Regras:
# MAGIC
# MAGIC - considerar apenas pedidos válidos
# MAGIC - considerar apenas pedidos pagos
# MAGIC - agregar por data e canal
# MAGIC - calcular quantidade de pedidos e receita total

# COMMAND ----------

gold_df = (
    spark.table(SILVER_TABLE)
    .filter(F.col("is_valid_order"))
    .filter(F.col("status_normalized") == "paid")
    .groupBy("order_date", "channel_normalized")
    .agg(
        F.countDistinct("order_id").alias("pedidos_pagos"),
        F.round(F.sum("amount_decimal"), 2).alias("receita_total"),
        F.round(F.avg("amount_decimal"), 2).alias("ticket_medio"),
    )
    .orderBy("order_date", "channel_normalized")
)

display(gold_df)

# COMMAND ----------

(
    gold_df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", True)
    .saveAsTable(GOLD_TABLE)
)

spark.sql(f"COMMENT ON TABLE {GOLD_TABLE} IS 'Camada Ouro da aula de introdução ao Databricks'")

display(spark.table(GOLD_TABLE))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9.1. Métrica pronta para análise
# MAGIC
# MAGIC A camada Ouro normalmente alimenta dashboards, alertas e consultas de negócio.
# MAGIC
# MAGIC Abaixo, usamos uma janela analítica para ranquear os canais por receita dentro de cada dia. Esse tipo de transformação aparece bastante em análises finais, porque preserva o detalhe agregado e adiciona uma leitura comparativa.

# COMMAND ----------

daily_channel_rank_df = (
    spark.table(GOLD_TABLE)
    .withColumn(
        "ranking_receita_no_dia",
        F.dense_rank().over(
            Window.partitionBy("order_date").orderBy(F.desc("receita_total"))
        ),
    )
    .orderBy("order_date", "ranking_receita_no_dia", "channel_normalized")
)

display(daily_channel_rank_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Usando Spark SQL
# MAGIC
# MAGIC Databricks permite alternar entre PySpark e SQL.
# MAGIC
# MAGIC Para facilitar uma consulta SQL no notebook, vamos criar views temporárias com nomes simples.

# COMMAND ----------

spark.table(BRONZE_TABLE).createOrReplaceTempView("intro_bronze_pedidos")
spark.table(SILVER_TABLE).createOrReplaceTempView("intro_silver_pedidos")
spark.table(GOLD_TABLE).createOrReplaceTempView("intro_gold_receita_diaria")

print("Views temporárias criadas: intro_bronze_pedidos, intro_silver_pedidos, intro_gold_receita_diaria")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   order_date,
# MAGIC   channel_normalized,
# MAGIC   pedidos_pagos,
# MAGIC   receita_total,
# MAGIC   ticket_medio
# MAGIC FROM intro_gold_receita_diaria
# MAGIC ORDER BY order_date, channel_normalized

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   country,
# MAGIC   status_normalized,
# MAGIC   COUNT(*) AS total_registros,
# MAGIC   ROUND(SUM(COALESCE(amount_decimal, 0)), 2) AS valor_observado
# MAGIC FROM intro_silver_pedidos
# MAGIC GROUP BY country, status_normalized
# MAGIC ORDER BY country, status_normalized

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10.1. Criando uma view para consumo
# MAGIC
# MAGIC Nem todo objeto de consumo precisa ser uma tabela física.
# MAGIC
# MAGIC Views são úteis quando você quer oferecer uma leitura controlada sobre uma tabela, sem duplicar dados.
# MAGIC
# MAGIC Nesta introdução, a view abaixo representa uma camada de acesso para BI: ela seleciona os campos principais da tabela Ouro e deixa explícita a regra de consumo.

# COMMAND ----------

spark.sql(
    f"""
    CREATE OR REPLACE VIEW {GOLD_VIEW} AS
    SELECT
      order_date,
      channel_normalized,
      pedidos_pagos,
      receita_total,
      ticket_medio
    FROM {GOLD_TABLE}
    WHERE receita_total > 0
    """
)

display(spark.table(GOLD_VIEW).orderBy("order_date", "channel_normalized"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Conhecendo objetos no Unity Catalog
# MAGIC
# MAGIC O namespace completo de uma tabela no Databricks segue a forma:
# MAGIC
# MAGIC | Parte | Exemplo neste notebook | Papel |
# MAGIC |---|---|---|
# MAGIC | Catalog | valor de `CATALOG` | camada mais alta de organização |
# MAGIC | Schema | valor de `SCHEMA` | agrupamento lógico de objetos |
# MAGIC | Table | `intro_silver_pedidos` | tabela governada |
# MAGIC
# MAGIC Vamos listar os objetos criados.

# COMMAND ----------

display(
    spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}")
    .filter(F.col("tableName").startswith("intro_"))
    .orderBy("tableName")
)

# COMMAND ----------

try:
    catalog_tables_df = spark.sql(
        f"""
        SELECT
          table_catalog,
          table_schema,
          table_name,
          table_type
        FROM {CATALOG}.information_schema.tables
        WHERE table_schema = '{SCHEMA}'
          AND table_name LIKE 'intro_%'
        ORDER BY table_name
        """
    )
except Exception as exc:
    catalog_tables_df = spark.createDataFrame(
        [(str(exc).splitlines()[0],)],
        "observacao STRING",
    )

display(catalog_tables_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11.1. Leitura de governança
# MAGIC
# MAGIC Unity Catalog organiza governança em uma hierarquia.
# MAGIC
# MAGIC | Nível | Exemplo | Pergunta que responde |
# MAGIC |---|---|---|
# MAGIC | Catalog | `CATALOG` | qual domínio maior de dados estou usando? |
# MAGIC | Schema | `SCHEMA` | qual agrupamento lógico contém meus objetos? |
# MAGIC | Table/View | Bronze, Prata, Ouro e view | qual dado será lido ou escrito? |
# MAGIC | Volume | `BASE_PATH` | onde arquivos governados ficam armazenados? |
# MAGIC
# MAGIC Em ambientes reais, permissões são concedidas para usuários, grupos ou service principals.
# MAGIC
# MAGIC Comandos comuns que aparecerão em módulos posteriores:
# MAGIC
# MAGIC - `GRANT USE CATALOG ON CATALOG ...`
# MAGIC - `GRANT USE SCHEMA ON SCHEMA ...`
# MAGIC - `GRANT SELECT ON TABLE ...`
# MAGIC - `GRANT READ VOLUME ON VOLUME ...`
# MAGIC
# MAGIC Nesta aula, não vamos executar grants, porque permissões dependem da configuração administrativa do workspace.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Pensando em produção com Lakeflow Jobs
# MAGIC
# MAGIC Em um notebook de estudo, você pode executar as células manualmente.
# MAGIC
# MAGIC Em produção, a lógica deve virar um fluxo orquestrado.
# MAGIC
# MAGIC Um desenho simples para Lakeflow Jobs seria:
# MAGIC
# MAGIC | Ordem | Tarefa | O que executaria |
# MAGIC |---|---|---|
# MAGIC | 1 | ingestao_bronze | leitura de arquivos e gravação Bronze |
# MAGIC | 2 | transformacao_prata | limpeza, cast, deduplicação e validação |
# MAGIC | 3 | publicacao_ouro | agregações para BI e analytics |
# MAGIC | 4 | validacao_final | checks simples de quantidade e qualidade |
# MAGIC
# MAGIC O ponto principal: Lakeflow Jobs organiza tarefas, dependências, retries, triggers e histórico de execução.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12.1. Quando a ingestão deixa de ser manual
# MAGIC
# MAGIC Neste notebook, nós criamos e lemos arquivos de forma controlada para fins didáticos.
# MAGIC
# MAGIC Em produção, ingestão de arquivos normalmente precisa lidar com chegada contínua de novos dados. O padrão moderno no Databricks é usar:
# MAGIC
# MAGIC - **Auto Loader** para arquivos em cloud object storage;
# MAGIC - **Lakeflow Connect** para conectores gerenciados e fontes empresariais;
# MAGIC - **COPY INTO** para cargas incrementais simples em lote;
# MAGIC - **Lakeflow Jobs** para agendar ou acionar o processamento.
# MAGIC
# MAGIC A ideia central é não reprocessar tudo a cada execução. A plataforma deve saber quais arquivos ou alterações já foram processados, usando metadados, checkpoints e histórico de execução.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 13. Pensando em pipelines declarativos
# MAGIC
# MAGIC Em um projeto mais avançado, parte da lógica Bronze, Prata e Ouro pode virar um pipeline declarativo.
# MAGIC
# MAGIC Aqui vamos apenas separar a regra de transformação em funções Python para mostrar a mudança de mentalidade: sair de células soltas e caminhar para código reutilizável.

# COMMAND ----------

def build_silver_orders(bronze_input_df):
    return (
        bronze_input_df
        .withColumn("amount_decimal", F.col("amount").cast(DoubleType()))
        .withColumn("order_timestamp", F.to_timestamp("order_ts"))
        .withColumn("order_date", F.to_date("order_timestamp"))
        .withColumn("status_normalized", F.lower(F.trim("status")))
        .withColumn("channel_normalized", F.lower(F.trim("channel")))
        .withColumn("country", F.upper(F.trim("country")))
        .withColumn(
            "is_valid_order",
            F.col("order_id").isNotNull()
            & F.col("customer_id").isNotNull()
            & F.col("order_timestamp").isNotNull()
            & F.col("amount_decimal").isNotNull()
            & F.col("status_normalized").isin("created", "paid", "cancelled"),
        )
        .dropDuplicates(["order_id"])
    )


def build_gold_revenue(silver_input_df):
    return (
        silver_input_df
        .filter(F.col("is_valid_order"))
        .filter(F.col("status_normalized") == "paid")
        .groupBy("order_date", "channel_normalized")
        .agg(
            F.countDistinct("order_id").alias("pedidos_pagos"),
            F.round(F.sum("amount_decimal"), 2).alias("receita_total"),
            F.round(F.avg("amount_decimal"), 2).alias("ticket_medio"),
        )
        .orderBy("order_date", "channel_normalized")
    )


silver_from_function_df = build_silver_orders(spark.table(BRONZE_TABLE))
gold_from_function_df = build_gold_revenue(silver_from_function_df)

display(gold_from_function_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 14. Mini-validações
# MAGIC
# MAGIC Validações simples ajudam a transformar código de aula em código mais confiável.
# MAGIC
# MAGIC Aqui vamos conferir se:
# MAGIC
# MAGIC - a camada Bronze tem registros
# MAGIC - a camada Prata reduziu duplicidades
# MAGIC - a camada Ouro tem receita positiva

# COMMAND ----------

bronze_count = spark.table(BRONZE_TABLE).count()
silver_distinct_orders = spark.table(SILVER_TABLE).select("order_id").distinct().count()
gold_total_revenue = spark.table(GOLD_TABLE).agg(F.sum("receita_total").alias("total")).first()["total"]

assert bronze_count > 0, "A camada Bronze deveria ter registros."
assert silver_distinct_orders > 0, "A camada Prata deveria ter pedidos distintos."
assert gold_total_revenue is not None and gold_total_revenue > 0, "A camada Ouro deveria ter receita positiva."

print("Validações concluídas com sucesso.")
print("Registros Bronze:", bronze_count)
print("Pedidos distintos na Prata:", silver_distinct_orders)
print("Receita total Gold:", gold_total_revenue)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 15. O que você construiu
# MAGIC
# MAGIC Neste notebook, você construiu um mini Lakehouse:
# MAGIC
# MAGIC | Camada | Objeto criado | Resultado |
# MAGIC |---|---|---|
# MAGIC | Arquivos | `RAW_PATH` | dados sintéticos em CSV dentro de um Volume |
# MAGIC | Bronze | `intro_bronze_pedidos` | dados de entrada com metadados de ingestão |
# MAGIC | Prata | `intro_silver_pedidos` | dados limpos, tipados, deduplicados e validados |
# MAGIC | Ouro | `intro_gold_receita_diaria` | métrica pronta para análise |
# MAGIC | DML | `intro_delta_dml_demo` | exemplo isolado de `INSERT` e `MERGE` |
# MAGIC | View | `intro_vw_receita_diaria` | objeto lógico para consumo analítico |
# MAGIC
# MAGIC Você também praticou:
# MAGIC
# MAGIC - leitura de arquivos com Spark
# MAGIC - escrita Delta
# MAGIC - criação de tabelas governadas
# MAGIC - comandos DDL e DML com Delta
# MAGIC - consultas SQL
# MAGIC - inspeção de histórico Delta
# MAGIC - criação de view
# MAGIC - validações simples
# MAGIC - separação de lógica em funções

# COMMAND ----------

# MAGIC %md
# MAGIC ## 16. Limpeza opcional
# MAGIC
# MAGIC Por padrão, este notebook mantém as tabelas e arquivos criados para você explorar depois.
# MAGIC
# MAGIC Se quiser remover tudo, altere `CLEANUP` para `True` e execute a célula abaixo.

# COMMAND ----------

CLEANUP = False

if CLEANUP:
    spark.sql(f"DROP VIEW IF EXISTS {GOLD_VIEW}")

    for table_name in [GOLD_TABLE, SILVER_TABLE, BRONZE_TABLE, DML_TABLE]:
        spark.sql(f"DROP TABLE IF EXISTS {table_name}")

    reset_path(BASE_PATH)
    print("Objetos e arquivos removidos.")
else:
    print("Limpeza não executada. Tabelas e arquivos foram mantidos para exploração.")
    print("Bronze:", BRONZE_TABLE)
    print("Prata:", SILVER_TABLE)
    print("Ouro:", GOLD_TABLE)
    print("DML demo:", DML_TABLE)
    print("View Gold:", GOLD_VIEW)
    print("Volume:", BASE_PATH)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Próximos passos
# MAGIC
# MAGIC Depois desta introdução, o caminho natural é:
# MAGIC
# MAGIC 1. estudar **Lakeflow Connect e Auto Loader** para entender ingestão;
# MAGIC 2. estudar **Lakeflow Jobs** para entender orquestração;
# MAGIC 3. estudar **Lakeflow Spark Declarative Pipelines** para entender pipelines declarativos;
# MAGIC 4. estudar **Unity Catalog** para entender governança;
# MAGIC 5. aprofundar PySpark e SQL para transformação e modelagem.
