# Manifesto de assets renomeados

## Saidas geradas

- `pdf/apresentacao_databricks_lakeflow_jobs.pdf`
- `apresentacao_databricks_lakeflow_jobs_png/`
- `capas/`

## Estado atual da pasta

- Os arquivos de `capas/` foram renomeados no lugar.
- A pasta `capas_renomeadas/` foi mantida como cópia de segurança dos mesmos PNGs com nomes semânticos.

## Mapeamento

| origem | pagina | arquivo_original | arquivo_novo | descricao | observacoes |
|--------|--------|------------------|--------------|-----------|-------------|
| pdf | 1 | Apresentação - Databricks Lakeflow Jobs.pdf (página 1) | 01_capa_databricks_lakeflow_jobs.png | slide de abertura com o título Databricks Lakeflow Jobs | nome direto a partir do título principal |
| pdf | 2 | Apresentação - Databricks Lakeflow Jobs.pdf (página 2) | 02_introducao_ao_lakeflow_jobs.png | introdução ao papel do Lakeflow Jobs na orquestração de cargas no Databricks | sem incerteza relevante |
| pdf | 3 | Apresentação - Databricks Lakeflow Jobs.pdf (página 3) | 03_engenharia_de_dados_com_databricks.png | capa de seção de engenharia de dados com Databricks | slide de seção |
| pdf | 4 | Apresentação - Databricks Lakeflow Jobs.pdf (página 4) | 04_visao_geral_databricks_lakeflow.png | visão geral dos componentes Lakeflow Declarative Pipelines, Connect e Jobs | nome inferido a partir da estrutura do slide |
| pdf | 5 | Apresentação - Databricks Lakeflow Jobs.pdf (página 5) | 05_o_que_sao_lakeflow_jobs.png | capa de seção perguntando o que são Lakeflow Jobs | slide de seção |
| pdf | 6 | Apresentação - Databricks Lakeflow Jobs.pdf (página 6) | 06_formas_de_orquestrar_suas_cargas.png | comparação visual entre orquestradores externos e a plataforma Databricks | título claro, mas o conteúdo visual é comparativo |
| pdf | 7 | Apresentação - Databricks Lakeflow Jobs.pdf (página 7) | 07_desafios_de_orquestradores_externos.png | desafios de orquestradores externos fora da lakehouse | sem incerteza relevante |
| pdf | 8 | Apresentação - Databricks Lakeflow Jobs.pdf (página 8) | 08_lakeflow_jobs_nativo_da_plataforma.png | benefícios do Lakeflow Jobs como orquestrador nativo da plataforma | sem incerteza relevante |
| pdf | 9 | Apresentação - Databricks Lakeflow Jobs.pdf (página 9) | 09_componentes_do_lakeflow_jobs.png | explicação dos componentes triggers, control flow, observability e compute | sem incerteza relevante |
| pdf | 10 | Apresentação - Databricks Lakeflow Jobs.pdf (página 10) | 10_arquitetura_lakeflow_jobs.png | diagrama de arquitetura do Lakeflow Jobs com workflow, triggers e workloads | slide sem bloco textual extraído; nome baseado no diagrama |
| pdf | 11 | Apresentação - Databricks Lakeflow Jobs.pdf (página 11) | 11_conceitos_de_orquestracao.png | capa de seção de conceitos de orquestração | slide de seção |
| pdf | 12 | Apresentação - Databricks Lakeflow Jobs.pdf (página 12) | 12_o_que_e_uma_dag.png | definição de DAG com os conceitos directed, acyclic e graph | sem incerteza relevante |
| pdf | 13 | Apresentação - Databricks Lakeflow Jobs.pdf (página 13) | 13_orquestracao_de_tarefas_com_dag.png | visão de task orchestration com dependências em DAG | nome baseado no diagrama e no texto explicativo |
| pdf | 14 | Apresentação - Databricks Lakeflow Jobs.pdf (página 14) | 14_padroes_comuns_de_cargas_de_trabalho.png | padrões sequence, funnel e fan-out para cargas de trabalho | o texto cita difusão ou estrela, mas o visual usa fan-out |
| pdf | 15 | Apresentação - Databricks Lakeflow Jobs.pdf (página 15) | 15_construindo_blocos_de_trabalho.png | capa de seção sobre construção de blocos de trabalho | slide de seção |
| pdf | 16 | Apresentação - Databricks Lakeflow Jobs.pdf (página 16) | 16_job_vs_task.png | comparação entre job e task como unidades de trabalho | título não explícito; nome baseado no conteúdo |
| pdf | 17 | Apresentação - Databricks Lakeflow Jobs.pdf (página 17) | 17_tipos_de_tarefas_suportadas.png | lista de tipos de tarefas suportadas em Lakeflow Jobs | sem incerteza relevante |
| pdf | 18 | Apresentação - Databricks Lakeflow Jobs.pdf (página 18) | 18_metricas_essenciais_do_lakeflow_jobs.png | cards com 3 componentes, 99% de confiabilidade e 5 mil análises por minuto | sem título único dominante; nome baseado nos cards |
| pdf | 19 | Apresentação - Databricks Lakeflow Jobs.pdf (página 19) | 19_criando_jobs_no_lakeflow.png | resumo das etapas para criar um Lakeflow Job | sem incerteza relevante |
| pdf | 20 | Apresentação - Databricks Lakeflow Jobs.pdf (página 20) | 20_monitoramento_de_lakeflow_jobs.png | slide de monitoramento com dashboards e alertas personalizados | sem incerteza relevante |
| pdf | 21 | Apresentação - Databricks Lakeflow Jobs.pdf (página 21) | 21_melhores_praticas_lakeflow_jobs.png | melhores práticas de otimização, erros, versionamento, monitoramento e automação | usei o termo do próprio slide, não a variante boas práticas |
| pdf | 22 | Apresentação - Databricks Lakeflow Jobs.pdf (página 22) | 22_integracoes_com_delta_lake_spark_e_mlflow.png | integrações com Delta Lake, Spark e MLflow | sem incerteza relevante |
| pdf | 23 | Apresentação - Databricks Lakeflow Jobs.pdf (página 23) | 23_seguranca_e_compliance.png | segurança e compliance com acesso, criptografia e auditoria | sem incerteza relevante |
| pdf | 24 | Apresentação - Databricks Lakeflow Jobs.pdf (página 24) | 24_historias_de_sucesso.png | histórias de sucesso com logos de clientes e texto de resultados | texto contém placeholders de clientes |
| pdf | 25 | Apresentação - Databricks Lakeflow Jobs.pdf (página 25) | 25_contato.png | slide final de contato com email, redes sociais e telefone | dados de contato parecem genéricos |
| capas | - | Databricks Free Edition (1).png | entenda_delta_sharing_na_pratica.png | capa com destaque para Delta Sharing na prática e card Databricks | distinção guiada pelo texto principal do layout |
| capas | - | Databricks Free Edition (2).png | entenda_lakehouse_federation_delta_lake.png | capa com destaque para Lakehouse Federation e logo Delta Lake | distinção guiada pelo logo Delta Lake |
| capas | - | Databricks Free Edition (3).png | lakehouse_federation_na_pratica.png | capa com destaque para Lakehouse Federation na prática e card Databricks | sem incerteza relevante |
| capas | - | Databricks Free Edition (4).png | entenda_databricks_asset_bundles_delta_lake.png | capa com destaque para Databricks Asset Bundles e logo Delta Lake | distinção guiada pelo logo Delta Lake |
| capas | - | Databricks Free Edition (5).png | databricks_asset_bundles_na_pratica.png | capa com destaque para Databricks Asset Bundles na prática e card Databricks | sem incerteza relevante |
| capas | - | Databricks Free Edition (6).png | aprenda_com_databricks_free_edition.png | capa com chamada Aprenda com Databricks Free Edition | sem incerteza relevante |
| capas | - | Databricks Free Edition.png | entenda_delta_sharing_delta_lake.png | capa com destaque para Delta Sharing e logo Delta Lake | nome conservador para diferenciar da versão na prática |
