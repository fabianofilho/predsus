# Instruções para Converter Arquivos DBC

## Problema
Os arquivos DBC do DATASUS precisam ser convertidos para CSV, mas as bibliotecas Python disponíveis requerem compilação C++ (Microsoft Visual C++ Build Tools).

## Solução 1: Instalar Visual C++ Build Tools (Recomendado)

1. Baixe o Visual C++ Build Tools:
   - Acesse: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Baixe e instale o "Build Tools for Visual Studio"

2. Após instalar, reinstale as bibliotecas:
   ```bash
   pip uninstall readdbc
   pip install readdbc
   ```

## Solução 2: Usar Ferramenta Externa

### Opção A: Usar DBCtoDBF (Windows)
1. Baixe o DBCtoDBF em: https://www.4shared.com/get/8aZ8Qm1S/dbctodbf.html
2. Converta manualmente os arquivos ou integre no pipeline

### Opção B: Usar TabWin (Software do DATASUS)
1. Baixe o TabWin do DATASUS
2. Use para converter DBC para outros formatos

## Solução 3: Usar Ambiente com Compilação (Docker/Linux)
Execute o pipeline em um ambiente Linux ou Docker onde é mais fácil instalar as ferramentas de compilação.

