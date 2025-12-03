# Pipeline de Análise de Completude de Dados do SINAN

Este pipeline automatiza o download, processamento e análise de completude dos dados do Sistema de Informação de Agravos de Notificação (SINAN) do DATASUS.

## Funcionalidades

- ✅ **Download automático** de múltiplos agravos do SINAN
- ✅ **Filtragem por região** (UF) para trabalhar com amostras menores
- ✅ **Limitação de amostra** para processamento rápido
- ✅ **Análise de completude** individual por agravo
- ✅ **Relatório consolidado** com todos os agravos em uma única tabela
- ✅ **Múltiplos formatos** de saída (CSV, Excel, TXT)

## Requisitos

- Python 3.7+
- Bibliotecas Python (instaladas automaticamente):
  - `pandas`
  - `dbfread`
  - `datasus-fetcher`
  - `dbc-to-dbf`
  - `openpyxl` (opcional, para relatórios Excel)

## Instalação

1. Clone ou baixe este repositório
2. Instale as dependências:

```bash
pip install pandas dbfread datasus-fetcher dbc-to-dbf openpyxl
```

Ou simplesmente execute o pipeline, que instalará automaticamente as dependências necessárias.

## Uso

### Configuração Básica

Edite a função `main()` no arquivo `pipeline.py` para ajustar os parâmetros:

```python
ANO = 2022       # Ano dos dados
UF = "SP"        # Unidade Federativa (SP, RJ, MG, etc.)
SAMPLE_SIZE = 1000  # Tamanho da amostra por agravo
MAX_AGRAVOS = 10  # Limite de agravos (None para processar todos)
```

### Execução

```bash
python pipeline.py
```

### Parâmetros

- **ANO**: Ano dos dados a serem baixados (ex: 2022)
- **UF**: Código da Unidade Federativa (2 letras):
  - SP (São Paulo)
  - RJ (Rio de Janeiro)
  - MG (Minas Gerais)
  - RS (Rio Grande do Sul)
  - PR (Paraná)
  - etc.
- **SAMPLE_SIZE**: Número máximo de registros a processar por agravo (padrão: 1000)
- **MAX_AGRAVOS**: Limite de agravos para processar (útil para testes)

## Saídas

O pipeline gera os seguintes arquivos:

### Por Agravo
- `[agravo]_[ano].csv` - Dados convertidos em CSV
- `[agravo]_[ano]_relatorio_completude.txt` - Relatório detalhado de completude

### Consolidado
- `relatorio_consolidado_completude_[ano]_[uf].csv` - Tabela consolidada em CSV
- `relatorio_consolidado_completude_[ano]_[uf].xlsx` - Tabela consolidada em Excel (com abas)
- `relatorio_consolidado_completude_[ano]_[uf].txt` - Relatório consolidado em texto

### Estrutura do Relatório Consolidado

O relatório consolidado contém:

| Coluna | Descrição |
|--------|-----------|
| Agravo | Nome do agravo |
| Código | Código do agravo no DATASUS |
| Total_Registros | Número de registros processados |
| Total_Campos | Número de campos na base |
| Completude_Média_% | Percentual médio de preenchimento |
| Completude_Mediana_% | Percentual mediano de preenchimento |
| Campos_100% | Quantidade de campos 100% preenchidos |
| Campos_0% | Quantidade de campos 0% preenchidos |
| Status | Status do processamento |

## Mapeamento de Agravos

O pipeline extrai automaticamente os agravos do arquivo `tabela_agravos.md` e os mapeia para os códigos do DATASUS. Alguns agravos podem ter subcategorias (a., b., c., etc.) que são processadas separadamente quando disponíveis.

## Tratamento de Erros

O pipeline é robusto e continua processando mesmo quando alguns agravos falham:
- Agravos não disponíveis para o ano especificado são pulados
- Erros de conversão são registrados no relatório consolidado
- Status de cada agravo é indicado no relatório final

## Limitações

- O download de dados pode ser lento dependendo da conexão
- Alguns agravos podem não estar disponíveis para todos os anos
- A filtragem por UF pode não funcionar para todos os agravos (dependendo da estrutura dos dados)

## Exemplo de Saída

```
================================================================================
RELATÓRIO CONSOLIDADO DE COMPLETUDE - SINAN
Ano: 2022 | UF: SP
================================================================================

Agravo                        Código  Total_Registros  Completude_Média_%  Status
Dengue - Casos                deng    1000              87.5                ✓ Sucesso
Tuberculose                   tube    950               92.3                ✓ Sucesso
Hepatites virais              hepa    800               85.1                ✓ Sucesso
```

## Suporte

Para problemas ou dúvidas, verifique:
1. Se todas as dependências estão instaladas
2. Se o `datasus-fetcher` está funcionando corretamente
3. Se há espaço em disco suficiente
4. Se a conexão com a internet está ativa

## Notas

- Os dados são baixados diretamente do DATASUS
- O processamento pode levar algum tempo dependendo do número de agravos
- Recomenda-se começar com `MAX_AGRAVOS = 5` para testes

