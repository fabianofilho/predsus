# PredSUS: Pipeline e Repositório de Dados de Saúde Pública do Brasil

> [!IMPORTANT]
> **Repositório arquivado.** Não recebe mais correções nem atualizações. O que tinha uso foi migrado para repositórios ativos do lab; o restante fica aqui só como registro.
>
> - **Tabela de agravos** (`tabela_agravos.md`): passou para [`docs/agravos.md`](https://github.com/labdaps/datasus-core/blob/main/docs/agravos.md) no [labdaps/datasus-core](https://github.com/labdaps/datasus-core).
> - **Diretório de bases de dados** (seção mais abaixo neste README): passou para [`docs/fontes.md`](https://github.com/labdaps/datasus-core/blob/main/docs/fontes.md) no labdaps/datasus-core.
> - **Análise de completude** (`analyze_completeness` no `pipeline.py`): reimplementada no módulo [`datasus_core.quality`](https://github.com/labdaps/datasus-core/blob/main/src/datasus_core/quality.py) do labdaps/datasus-core, que conta o código de ignorado como ausente e não tira média entre agravos.
> - **Restante do `pipeline.py`** (download, filtro de UF, conversão DBC e relatórios): não foi migrado, porque se sobrepõe ao app canônico [fabianofilho/lab-ai-prediction](https://github.com/fabianofilho/lab-ai-prediction). Para baixar e ler o SINAN, use o app ou o `datasus_core.io`, que saiu dele.
>
> `INSTRUCOES_INSTALACAO.md` e `instalar_ferramentas.md` também ficam só como registro: não baixe o conversor DBC pelo link de compartilhamento de arquivos citado ali. O datasus-core lê DBC com o pacote `datasus-dbc`, instalado pelo pip.

Este repositório contém um pipeline automatizado para análise de completude de dados do SINAN (DATASUS) e um diretório abrangente das principais bases de dados abertas de saúde pública do Brasil e do mundo, focadas em epidemiologia, machine learning e predição.

## 🚀 Pipeline de Análise de Completude (SINAN)

O pipeline automatiza o download, processamento e análise de completude dos dados do Sistema de Informação de Agravos de Notificação (SINAN) do DATASUS.

### Funcionalidades do Pipeline
- ✅ **Download automático** de múltiplos agravos do SINAN via FTP
- ✅ **Filtragem por região** (UF) para trabalhar com amostras menores
- ✅ **Limitação de amostra** para processamento rápido
- ✅ **Análise de completude** individual por agravo
- ✅ **Relatório consolidado** com todos os agravos em uma única tabela
- ✅ **Múltiplos formatos** de saída (CSV, Excel, TXT)

### Como usar o Pipeline

1. Instale as dependências:
```bash
pip install pandas dbfread datasus-fetcher dbc-to-dbf openpyxl
```

2. Edite a função `main()` no arquivo `pipeline.py` para ajustar os parâmetros (Ano, UF, Tamanho da Amostra).

3. Execute:
```bash
python pipeline.py
```

*Nota: A conversão de arquivos DBC para CSV pode exigir a instalação do Microsoft Visual C++ Build Tools no Windows. Veja o arquivo `INSTRUCOES_INSTALACAO.md` para mais detalhes.*

---

## 📊 Diretório de Bases de Dados de Saúde Pública

Abaixo está um mapeamento abrangente das principais bases de dados de saúde pública disponíveis para pesquisa, análise epidemiológica e desenvolvimento de modelos preditivos (Machine Learning/IA).

### 🇧🇷 Bases de Dados Nacionais (Brasil)

#### Sistemas do DATASUS (Ministério da Saúde)
- **[SINAN (Sistema de Informação de Agravos de Notificação)](https://datasus.saude.gov.br/transferencia-de-arquivos/)**: Dados sobre doenças de notificação compulsória (Dengue, Tuberculose, HIV, Sífilis, etc.).
- **[SIM (Sistema de Informações sobre Mortalidade)](https://datasus.saude.gov.br/transferencia-de-arquivos/)**: Registros de declarações de óbito em todo o território nacional.
- **[SINASC (Sistema de Informações sobre Nascidos Vivos)](https://datasus.saude.gov.br/transferencia-de-arquivos/)**: Dados epidemiológicos sobre nascimentos.
- **[SIH/SUS (Sistema de Informações Hospitalares)](https://datasus.saude.gov.br/transferencia-de-arquivos/)**: Dados de internações hospitalares financiadas pelo SUS (AIH).
- **[SIA/SUS (Sistema de Informações Ambulatoriais)](https://datasus.saude.gov.br/transferencia-de-arquivos/)**: Dados de atendimentos ambulatoriais no SUS.
- **[CNES (Cadastro Nacional de Estabelecimentos de Saúde)](https://cnes.datasus.gov.br/)**: Informações sobre infraestrutura, leitos e profissionais de saúde.

#### Atenção Primária e Vigilância
- **[SISAB / e-SUS APS](https://sisab.saude.gov.br/)**: Sistema de Informação em Saúde para a Atenção Básica. Contém dados de atendimentos, vacinação e acompanhamento de condições crônicas.
- **[SIVEP-Gripe](https://dados.gov.br/dados/conjuntos-dados/srag-2021-e-2022)**: Sistema de Informação da Vigilância Epidemiológica da Gripe. Base fundamental para dados de SRAG (Síndrome Respiratória Aguda Grave) e COVID-19.
- **[VIGITEL](https://www.gov.br/saude/pt-br/composicao/svsa/inqueritos-de-saude/vigitel)**: Vigilância de Fatores de Risco e Proteção para Doenças Crônicas por Inquérito Telefônico.
- **[SISPRENATAL](http://siab.datasus.gov.br/DATASUS/index.php?area=060305)**: Sistema de Acompanhamento da Gestante.
- **[HIPERDIA](http://siab.datasus.gov.br/DATASUS/index.php?area=060304)**: Sistema de Cadastramento e Acompanhamento de Hipertensos e Diabéticos.

#### Oncologia e Doenças Crônicas
- **[RCBP (Registros de Câncer de Base Populacional) - INCA](https://www.gov.br/inca/pt-br/assuntos/cancer/numeros/registros/base-populacional)**: Incidência de câncer, distribuição e tendência temporal no Brasil.
- **[Painel de Oncologia (Brasil)](https://datasus.saude.gov.br/transferencia-de-arquivos/)**: Dados sobre o tempo de início do tratamento oncológico no SUS.

#### Saúde Suplementar e Orçamento
- **[Dados Abertos ANS](https://dados.gov.br/dados/conjuntos-dados/informacoes-consolidadas-de-beneficiarios)**: Informações consolidadas de beneficiários de planos de saúde no Brasil.
- **[SIOPS](https://www.gov.br/saude/pt-br/acesso-a-informacao/siops)**: Sistema de Informações sobre Orçamentos Públicos em Saúde.

#### Inquéritos Populacionais (IBGE)
- **[PNS (Pesquisa Nacional de Saúde)](https://www.ibge.gov.br/estatisticas/sociais/saude/9160-pesquisa-nacional-de-saude.html)**: Amplo inquérito domiciliar sobre situação de saúde, estilos de vida e acesso a serviços.
- **[Estatísticas do Registro Civil (Mortalidade e Natalidade)](https://www.ibge.gov.br/estatisticas/sociais/populacao/9127-estatisticas-do-registro-civil.html)**: Dados complementares ao SIM e SINASC.

### 🌎 Bases de Dados Internacionais (Epidemiologia e Saúde Global)

- **[Global Burden of Disease (GBD) - IHME](https://www.healthdata.org/research-analysis/gbd)**: A mais abrangente pesquisa epidemiológica observacional mundial. Quantifica a perda de saúde por centenas de doenças, lesões e fatores de risco.
- **[Global Health Observatory (GHO) - WHO](https://www.who.int/data/gho)**: Repositório de dados da Organização Mundial da Saúde com estatísticas de 194 países.
- **[PAHO Open Data (OPAS)](https://opendata.paho.org/en)**: Portal interativo com mais de 140 indicadores de saúde focados na América Latina e Caribe.
- **[MIMIC-IV (Medical Information Mart for Intensive Care)](https://physionet.org/content/mimiciv/)**: Base de dados de UTI amplamente utilizada para modelos preditivos clínicos.

---

## 🛠️ Ferramentas e Bibliotecas Úteis para Dados do SUS

- **[PySUS](https://github.com/danicat/pysus)**: Biblioteca Python para download e processamento de dados do DATASUS (arquivos DBC).
- **[datasus-fetcher](https://pypi.org/project/datasus-fetcher/)**: Ferramenta para download automatizado de arquivos FTP do DATASUS.
- **[Base dos Dados](https://basedosdados.org/)**: Plataforma que disponibiliza dados públicos brasileiros (incluindo saúde) já limpos e prontos para uso via SQL, Python ou R.
- **[Painéis CONASEMS](https://paineis.conasems.org.br/)**: Painéis interativos com indicadores de saúde municipais.

## 📜 Licença

Este projeto está licenciado sob a licença MIT. Sinta-se à vontade para contribuir com novas bases de dados ou melhorias no pipeline!
