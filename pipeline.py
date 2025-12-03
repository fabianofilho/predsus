import os
import re
import struct
import subprocess
import sys
import pandas as pd
from dbfread import DBF
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --- Mapeamento de Agravos para Códigos DATASUS ---

AGRAVOS_MAP = {
    # Acidentes
    "acidente-trabalho": "acbr",
    "acidente-trabalho-material-biologico": "acbi",
    "acidente-animal-peconhento": "anim",
    "acidente-animal-rabia": "rabr",
    
    # Doenças infecciosas
    "botulismo": "botu",
    "colera": "cole",
    "coqueluche": "coqu",
    "covid-19": "covi",
    "dengue": "deng",
    "dengue-obitos": "deng",
    "difteria": "dift",
    "chagas-aguda": "chag",
    "chagas-cronica": "chag",
    "doenca-haemophilus": "hinf",
    "meningite": "meni",
    "zika": "zika",
    "zika-gestante": "zika",
    "zika-obitos": "zika",
    "zika-congenita": "zika",
    "esporotricose": "espo",
    "esquistossomose": "esqu",
    "febre-amarela": "fama",
    "chikungunya": "chik",
    "chikungunya-sem-transmissao": "chik",
    "chikungunya-obitos": "chik",
    "febre-nilo-ocidental": "fmal",
    "febre-maculosa": "rmac",
    "febre-tifoide": "ftif",
    "hanseniase": "hans",
    "hantavirose": "hant",
    "hepatites-virais": "hepa",
    "hepatite-b-gestante": "hepb",
    "hiv-aids": "aids",
    "hiv-gestante": "hivg",
    "hiv": "hiv",
    "htlv": "htlv",
    "htlv-gestante": "htlv",
    "influenza-novo-subtipo": "grip",
    "intoxicacao-exogena": "into",
    "leishmaniose-tegumentar": "lta",
    "leishmaniose-visceral": "leiv",
    "leptospirose": "lept",
    "malaria-amazonica": "malar",
    "malaria-extra-amazonica": "malar",
    "monkeypox": "mpox",
    "peste": "pest",
    "poliomielite": "poli",
    "raiva-humana": "raiv",
    "rubeola-congenita": "rube",
    "sarampo": "sara",
    "rubeola": "rube",
    "sifilis": "sifi",
    "sifilis-congenita": "sifi",
    "sifilis-gestante": "sifi",
    "paralisia-flacida-aguda": "pfag",
    "sim-a-covid": "covi",
    "sim-p-covid": "covi",
    "srag": "srag",
    "sindrome-gripal-covid": "covi",
    "tetano-acidental": "teta",
    "tetano-neonatal": "teta",
    "toxoplasmose": "toxo",
    "tuberculose": "tube",
    "varicela": "vari",
    "violencia-domestica": "viol",
    "violencia-sexual": "viol",
    
    # Doenças ocupacionais
    "cancer-relacionado-trabalho": "cane",
    "dermatose-ocupacional": "derm",
    "disturbio-voz-trabalho": "dvon",
    "ler-dort": "lesr",
    "perda-auditiva-trabalho": "pdat",
    "pneumoconiose-trabalho": "pneu",
    "transtorno-mental-trabalho": "tmen",
    
    # Outros
    "doenca-creutzfeldt-jakob": "dcj",
    "doenca-falciforme": "dofc",
    "evento-saude-publica": "esp",
    "eventos-adversos-vacinacao": "eav",
    "obito-infantil": "obit",
    "obito-materno": "obit",
}

# --- Funções do Pipeline ---

def install_dependencies():
    """Instala as bibliotecas Python necessárias para o pipeline."""
    print("Verificando e instalando dependências...")
    required_packages = {
        "pandas": "pandas",
        "dbfread": "dbfread",
        "datasus-fetcher": "datasus-fetcher",
        "datasus_dbc": "datasus-dbc",  # Biblioteca Python pura para descomprimir DBC
        "dbc_reader": "dbc_reader"  # Biblioteca Python pura alternativa para ler DBC
    }
    
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name.replace("-", "_"))
            print(f"✓ {package_name} já está instalado.")
        except ImportError:
            print(f"Instalando {package_name}...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", package_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"✓ {package_name} instalado com sucesso.")
            except subprocess.CalledProcessError as e:
                print(f"✗ Falha ao instalar {package_name}. Erro: {e}")
                print(f"  Por favor, tente instalar manualmente: pip install {package_name}")
                sys.exit(1)
    print("Todas as dependências estão satisfeitas.\n")

def extract_agravos_from_table(md_file: str = "tabela_agravos.md") -> List[Dict[str, str]]:
    """Extrai a lista de agravos do arquivo markdown."""
    agravos = []
    
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_num = None
        current_agravo = None
        
        for line in lines:
            # Remove marcadores de tabela markdown
            line = line.strip().replace('|', '').replace('**', '').strip()
            
            # Pula linhas de cabeçalho ou separadores
            if not line or line.startswith('---') or 'Periodicidade' in line or 'Imediata' in line or 'MS' in line:
                continue
            
            # Tenta extrair número do agravo
            num_match = re.match(r'^(\d+)\s', line)
            if num_match:
                current_num = num_match.group(1)
                # Remove o número do início
                line = line[len(current_num):].strip()
            
            # Detecta sub-itens (a., b., c., etc.)
            sub_match = re.match(r'^([a-z]\.)\s+(.+)', line, re.IGNORECASE)
            if sub_match:
                sub_item = sub_match.group(1).strip('.').lower()
                agravo_name = sub_match.group(2).strip()
                
                # Normaliza o nome para chave do mapeamento
                key = normalize_agravo_name(agravo_name)
                code = AGRAVOS_MAP.get(key, None)
                
                if code:
                    agravos.append({
                        'numero': current_num or '',
                        'nome': agravo_name,
                        'codigo': code,
                        'chave': key
                    })
                continue
            
            # Detecta linha principal de agravo (sem sub-itens)
            if line and not line.startswith('a.') and not line.startswith('b.') and not line.startswith('c.') and not line.startswith('d.') and not line.startswith('e.'):
                if current_num and len(line) > 10:  # Filtra linhas muito curtas
                    # Normaliza o nome
                    key = normalize_agravo_name(line)
                    code = AGRAVOS_MAP.get(key, None)
                    
                    if code:
                        agravos.append({
                            'numero': current_num,
                            'nome': line,
                            'codigo': code,
                            'chave': key
                        })
    
    except FileNotFoundError:
        print(f"Arquivo {md_file} não encontrado. Usando lista padrão de agravos.")
        # Lista padrão com alguns agravos principais
        agravos = [
            {'numero': '9', 'nome': 'Dengue - Casos', 'codigo': 'deng', 'chave': 'dengue'},
            {'numero': '63', 'nome': 'Tuberculose', 'codigo': 'tube', 'chave': 'tuberculose'},
            {'numero': '31', 'nome': 'Hepatites virais', 'codigo': 'hepa', 'chave': 'hepatites-virais'},
            {'numero': '42', 'nome': 'Leptospirose', 'codigo': 'lept', 'chave': 'leptospirose'},
            {'numero': '25', 'nome': 'Febre de Chikungunya', 'codigo': 'chik', 'chave': 'chikungunya'},
        ]
    
    # Remove duplicatas mantendo o primeiro
    seen = set()
    unique_agravos = []
    for agravo in agravos:
        key_tuple = (agravo['codigo'], agravo['chave'])
        if key_tuple not in seen:
            seen.add(key_tuple)
            unique_agravos.append(agravo)
    
    return unique_agravos

def normalize_agravo_name(name: str) -> str:
    """Normaliza o nome do agravo para encontrar no mapeamento."""
    name = name.lower()
    # Remove acentos e caracteres especiais
    name = name.replace('ç', 'c').replace('á', 'a').replace('à', 'a').replace('â', 'a')
    name = name.replace('é', 'e').replace('ê', 'e').replace('í', 'i').replace('ó', 'o')
    name = name.replace('ô', 'o').replace('õ', 'o').replace('ú', 'u')
    
    # Mapeamentos específicos
    mappings = {
        'dengue - casos': 'dengue',
        'dengue - óbitos': 'dengue-obitos',
        'acidente de trabalho com exposição a material biológico': 'acidente-trabalho-material-biologico',
        'acidente de trabalho': 'acidente-trabalho',
        'acidente por animal peçonhento': 'acidente-animal-peconhento',
        'acidente por animal potencialmente transmissor da raiva': 'acidente-animal-rabia',
        'câncer relacionado ao trabalho': 'cancer-relacionado-trabalho',
        'dermatose ocupacionais': 'dermatose-ocupacional',
        'distúrbio de voz relacionado ao trabalho': 'disturbio-voz-trabalho',
        'doença de chagas aguda': 'chagas-aguda',
        'doença de chagas crônica': 'chagas-cronica',
        'doença invasiva por "haemophilus influenza"': 'doenca-haemophilus',
        'doença meningocócica e outras meningites': 'meningite',
        'doença aguda pelo vírus zika': 'zika',
        'doença aguda pelo vírus zika em gestante': 'zika-gestante',
        'óbito com suspeita de doença pelo vírus zika': 'zika-obitos',
        'síndrome congênita associada à infecção pelo vírus zika': 'zika-congenita',
        'febre de chikungunya': 'chikungunya',
        'febre de chikungunya em áreas sem transmissão': 'chikungunya-sem-transmissao',
        'óbito com suspeita de febre de chikungunya': 'chikungunya-obitos',
        'febre do nilo ocidental e outras arboviroses de importância em saúde pública': 'febre-nilo-ocidental',
        'febre maculosa e outras riquetisioses': 'febre-maculosa',
        'infecção pelo vírus da hepatite b em gestante, parturiente ou puérpera e criança exposta ao risco de transmissão vertical da hepatite b': 'hepatite-b-gestante',
        'hiv/aids - infecção pelo vírus da imunodeficiência humana ou síndrome da imunodeficiência adquirida': 'hiv-aids',
        'infecção pelo hiv em gestante, parturiente ou puérpera e criança exposta ao risco de transmissão vertical do hiv': 'hiv-gestante',
        'infecção pelo vírus da imunodeficiência humana (hiv)': 'hiv',
        'infecção pelo vírus linfotrópico de células t humanas (htlv)': 'htlv',
        'infecção pelo htlv em gestante, parturiente ou puérpera e criança exposta ao risco de transmissão vertical do htlv': 'htlv-gestante',
        'intoxicação exógena (por substâncias químicas, incluindo agrotóxicos, gases tóxicos e metais pesados)': 'intoxicacao-exogena',
        'leishmaniose tegumentar americana': 'leishmaniose-tegumentar',
        'lesões por esforços repetitivos/ distúrbios osteomusculares relacionados ao trabalho (ler/dort)': 'ler-dort',
        'malária na região amazônica': 'malaria-amazonica',
        'malária na região extra-amazônica': 'malaria-extra-amazonica',
        'monkeypox (varíola dos macacos)': 'monkeypox',
        'óbito:': 'obito-infantil',
        'óbito infantil': 'obito-infantil',
        'óbito materno': 'obito-materno',
        'perda auditiva relacionada ao trabalho': 'perda-auditiva-trabalho',
        'pneumoconioses relacionadas ao trabalho': 'pneumoconiose-trabalho',
        'poliomielite por poliovírus selvagem': 'poliomielite',
        'raiva humana': 'raiva-humana',
        'síndrome da rubéola congênita': 'rubeola-congenita',
        'doenças exantemáticas:': 'sarampo',
        'sarampo': 'sarampo',
        'rubéola': 'rubeola',
        'sífilis:': 'sifilis',
        'sífilis adquirida': 'sifilis',
        'sífilis congênita': 'sifilis-congenita',
        'sífilis em gestante': 'sifilis-gestante',
        'síndrome da paralisia flácida aguda': 'paralisia-flacida-aguda',
        'síndrome inflamatória multissistêmica em adultos (sim-a) associada à covid-19': 'sim-a-covid',
        'síndrome inflamatória multissitêmica pediátrica (sim-p) associada à covid-19': 'sim-p-covid',
        'síndrome respiratória aguda grave (srag) associada a coronavírus': 'srag',
        'síndrome gripal suspeita de covid-19': 'sindrome-gripal-covid',
        'tétano:': 'tetano-acidental',
        'tétano acidental': 'tetano-acidental',
        'tétano neonatal': 'tetano-neonatal',
        'toxoplasmose gestacional e congênita': 'toxoplasmose',
        'transtornos mentais relacionados ao trabalho': 'transtorno-mental-trabalho',
        'varicela - caso grave internado ou óbito': 'varicela',
        'violência doméstica e/ou outras violências': 'violencia-domestica',
        'violência sexual e tentativa de suicídio': 'violencia-sexual',
        'doença de creutzfeldt-jakob (dcj)': 'doenca-creutzfeldt-jakob',
        'doença falciforme': 'doenca-falciforme',
        'evento de saúde pública (esp) que se constitua ameaça à saúde pública': 'evento-saude-publica',
        'eventos adversos graves ou óbitos pós vacinação': 'eventos-adversos-vacinacao',
    }
    
    # Remove pontuação e espaços extras
    name_clean = ' '.join(name.split())
    
    # Verifica mapeamento direto
    if name_clean in mappings:
        return mappings[name_clean]
    
    # Tenta encontrar correspondência parcial
    for key, value in mappings.items():
        if key in name_clean or name_clean in key:
            return value
    
    # Converte para formato padrão (minúsculas, hífens)
    name = name.replace(' ', '-').replace('(', '').replace(')', '').replace(':', '')
    name = re.sub(r'[^a-z0-9\-]', '', name)
    return name

def download_data(agravo_code: str, ano: int, uf: str = "SP", 
                  output_dir: str = "./sinan_data", 
                  sample_size: int = 1000) -> Optional[str]:
    """
    Baixa os dados do SINAN para um agravo e ano específicos.
    Filtra por UF e limita a amostra.
    
    Args:
        agravo_code: Código do agravo no DATASUS (ex: 'deng', 'tube')
        ano: Ano dos dados
        uf: Unidade Federativa (código de 2 letras, ex: 'SP', 'RJ', 'MG')
        output_dir: Diretório de saída
        sample_size: Tamanho máximo da amostra a processar
    
    Returns:
        Caminho do arquivo .dbc baixado ou None em caso de erro
    """
    print(f"\n{'='*60}")
    print(f"Baixando dados para o agravo '{agravo_code}' do ano {ano} (UF: {uf})...")
    print(f"{'='*60}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        dataset_name = f"sinan-{agravo_code.lower()}"
        command = [
            "datasus-fetcher", "data", dataset_name,
            "--start", str(ano), "--end", str(ano),
            "--data-dir", output_dir
        ]
        
        print(f"Executando comando: {' '.join(command)}")
        
        result = subprocess.run(
            command, 
            check=False,  # Não falhar imediatamente, vamos verificar o resultado
            capture_output=True, 
            text=True,
            timeout=600  # 10 minutos de timeout (aumentado)
        )
        
        # Verifica se houve erro no comando
        if result.returncode != 0:
            print(f"⚠ Comando retornou código de erro: {result.returncode}")
            if result.stderr:
                error_msg = result.stderr[:500]
                print(f"  Mensagem de erro: {error_msg}")
                # Verifica se é erro de dataset não encontrado
                if "not found" in error_msg.lower() or "não encontrado" in error_msg.lower():
                    print(f"  Dataset '{dataset_name}' não encontrado. Verificando alternativas...")
                    # Tenta variações comuns
                    alternativas = [
                        f"sinan-{agravo_code.lower()}a",  # Adiciona 'a' no final
                        f"sinan-{agravo_code.lower()}c",  # Adiciona 'c' no final
                        f"sinan-{agravo_code.lower()}g",  # Adiciona 'g' no final
                    ]
                    for alt in alternativas:
                        print(f"  Tentando alternativa: {alt}")
                        alt_command = [
                            "datasus-fetcher", "data", alt,
                            "--start", str(ano), "--end", str(ano),
                            "--data-dir", output_dir
                        ]
                        alt_result = subprocess.run(
                            alt_command,
                            check=False,
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        if alt_result.returncode == 0:
                            print(f"  ✓ Alternativa '{alt}' funcionou!")
                            dataset_name = alt
                            break
                    else:
                        print(f"  ✗ Nenhuma alternativa funcionou")
                        return None
            else:
                print(f"✗ Falha ao baixar os dados do agravo '{agravo_code}'")
                return None
        
        print(f"✓ Download concluído. Dados salvos em: {output_dir}")
        
        # Encontrar o arquivo .dbc baixado - busca mais robusta
        agravo_dir = os.path.join(output_dir, dataset_name, str(ano))
        
        # Primeiro tenta o caminho esperado
        if os.path.exists(agravo_dir):
            dbc_files = [f for f in os.listdir(agravo_dir) if f.endswith(".dbc")]
            if dbc_files:
                dbc_path = os.path.join(agravo_dir, dbc_files[0])
                print(f"✓ Arquivo encontrado: {os.path.basename(dbc_path)}")
                return dbc_path
        
        # Se não encontrou, busca em todos os subdiretórios
        print(f"  Buscando arquivo .dbc em subdiretórios...")
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".dbc"):
                    # Verifica se o arquivo corresponde ao agravo
                    file_lower = file.lower()
                    if agravo_code.lower() in file_lower or dataset_name.lower() in file_lower:
                        dbc_path = os.path.join(root, file)
                        print(f"✓ Arquivo encontrado: {os.path.basename(dbc_path)}")
                        print(f"  Localização: {dbc_path}")
                        return dbc_path
        
        print(f"✗ Arquivo .dbc não encontrado para '{agravo_code}'")
        print(f"  Diretório esperado: {agravo_dir}")
        print(f"  Busque manualmente em: {output_dir}")
        return None

    except subprocess.TimeoutExpired:
        print(f"✗ Timeout ao baixar os dados do agravo '{agravo_code}' (limite de 10 minutos)")
        return None
    except FileNotFoundError:
        print("✗ Comando 'datasus-fetcher' não encontrado. Verifique se a instalação foi bem-sucedida.")
        print("  Instale com: pip install datasus-fetcher")
        return None
    except Exception as e:
        print(f"✗ Erro inesperado ao baixar dados: {e}")
        return None

def convert_dbc_to_csv(dbc_path: str, uf: str = "SP", sample_size: int = 1000) -> Optional[str]:
    """
    Converte um arquivo .dbc diretamente para .csv usando readdbc.
    Filtra por UF e limita a amostra.
    
    Args:
        dbc_path: Caminho do arquivo .dbc
        uf: Unidade Federativa para filtrar
        sample_size: Tamanho máximo da amostra
    
    Returns:
        Caminho do arquivo CSV ou None em caso de erro
    """
    if not dbc_path or not os.path.exists(dbc_path):
        return None

    csv_path = dbc_path.replace(".dbc", ".csv")
    
    # Método 1: Tenta usar datasus-dbc (descomprime DBC para DBF, depois lê com dbfread)
    try:
        import datasus_dbc
        print(f"\nConvertendo {os.path.basename(dbc_path)} para CSV usando datasus-dbc...")
        
        # Descomprime DBC para DBF temporário
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.dbf', delete=False) as tmp_dbf:
            tmp_dbf_path = tmp_dbf.name
        
        try:
            datasus_dbc.decompress(dbc_path, tmp_dbf_path)
            
            # Lê o DBF usando dbfread (com tratamento de erros de data)
            try:
                table = DBF(tmp_dbf_path, encoding='latin-1', ignore_missing_memofile=True)
            except Exception as dbf_error:
                # Se falhar, tenta sem tratamento de memofile
                try:
                    table = DBF(tmp_dbf_path, encoding='latin-1')
                except Exception:
                    # Tenta com codificação diferente
                    table = DBF(tmp_dbf_path, encoding='cp1252')
            records = []
            count = 0
            
            # Identifica campo de UF
            uf_field = None
            if len(table) > 0:
                first_record = next(iter(table))
                for field in table.field_names:
                    if 'uf' in field.lower() or field.lower() in ['uf', 'sg_uf', 'id_uf']:
                        uf_field = field
                        break
            
            # Lê registros com filtro por UF (trata erros de data inválida)
            for record in table:
                try:
                    # Tenta converter o registro para dict, ignorando erros de data
                    record_dict = dict(record)
                    
                    if uf_field and record_dict.get(uf_field, '').upper() == uf.upper():
                        records.append(record_dict)
                        count += 1
                        if count >= sample_size:
                            break
                    elif not uf_field:
                        records.append(record_dict)
                        count += 1
                        if count >= sample_size:
                            break
                except (ValueError, TypeError) as date_error:
                    # Ignora erros de data inválida e continua
                    continue
            
            if not records and uf_field:
                # Se não encontrou com filtro, pega amostra geral
                records = list(table)[:sample_size]
            
            df = pd.DataFrame(records)
            
            # Remove arquivo temporário
            os.unlink(tmp_dbf_path)
            
            print(f"  Lidos {len(df)} registros")
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"✓ Arquivo CSV salvo em: {csv_path} ({len(df)} registros)")
            return csv_path
        except Exception as e:
            if os.path.exists(tmp_dbf_path):
                os.unlink(tmp_dbf_path)
            raise e
    except ImportError:
        print("⚠ datasus-dbc não disponível. Tentando método alternativo...")
    except Exception as e:
        print(f"⚠ Erro ao usar datasus-dbc: {str(e)[:200]}. Tentando método alternativo...")
    
    # Método 2: Tenta usar dbc_reader (Python puro, sem compilação!)
    try:
        from dbc_reader import DbcReader
        print(f"\nConvertendo {os.path.basename(dbc_path)} para CSV usando dbc_reader...")
        
        # Lê o arquivo DBC diretamente (dbc_reader aceita apenas caminho de arquivo, não objeto)
        rows = []
        dbc_reader = DbcReader(dbc_path)
        for row in dbc_reader:
            rows.append(row)
        
        if not rows:
            print("⚠ Arquivo DBC vazio ou sem registros")
            return None
        
        print(f"  Lidos {len(rows)} registros do arquivo DBC")
        
        # Converte para DataFrame
        df = pd.DataFrame(rows)
        
        # Filtra por UF se o campo existir
        uf_field = None
        for col in df.columns:
            if 'uf' in col.lower() or col.lower() in ['uf', 'sg_uf', 'id_uf']:
                uf_field = col
                break
        
        if uf_field:
            df_filtered = df[df[uf_field].astype(str).str.upper() == uf.upper()]
            if len(df_filtered) > 0:
                df = df_filtered.head(sample_size)
                print(f"  Filtrado por UF {uf}: {len(df)} registros")
            else:
                print(f"⚠ Nenhum registro encontrado para UF {uf}. Usando amostra geral...")
                df = df.head(sample_size)
        else:
            df = df.head(sample_size)
        
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"✓ Arquivo CSV salvo em: {csv_path} ({len(df)} registros)")
        return csv_path
    except ImportError:
        print("⚠ dbc_reader não disponível. Tentando método alternativo...")
    except Exception as e:
        error_msg = str(e)
        if "struct.error" in error_msg or "unpack requires" in error_msg:
            print(f"⚠ dbc_reader encontrou problema no formato do arquivo. Tentando método alternativo...")
        else:
            print(f"⚠ Erro ao usar dbc_reader: {error_msg[:200]}. Tentando método alternativo...")
    
    # Método 2: Tenta usar readdbc diretamente (mais simples e confiável)
    try:
        import readdbc
        print(f"\nConvertendo {os.path.basename(dbc_path)} para CSV usando readdbc...")
        
        # Usa dbc2dbf para converter para DBF primeiro, depois lê com simpledbf
        from readdbc import simpledbf
        from readdbc import dbc2dbf
        
        # Converte DBC para DBF em arquivo temporário
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.dbf', delete=False) as tmp_dbf:
            tmp_dbf_path = tmp_dbf.name
        
        try:
            # Converte DBC para DBF (dbc2dbf é uma função)
            # Tenta com tratamento de erro específico para problemas de compilação
            try:
                dbc2dbf(dbc_path, tmp_dbf_path)
            except Exception as compile_error:
                if "Microsoft Visual C++" in str(compile_error) or "compiler" in str(compile_error).lower():
                    raise ImportError("Compilação C++ necessária. Use uma ferramenta externa ou instale Visual C++ Build Tools.")
                raise
            
            # Lê o DBF usando simpledbf (que já funciona)
            dbf = simpledbf.Dbf5(tmp_dbf_path, codec='latin-1')
            df = dbf.to_dataframe()
            
            # Remove arquivo temporário
            if os.path.exists(tmp_dbf_path):
                os.unlink(tmp_dbf_path)
            
            # Filtra por UF se o campo existir
            uf_field = None
            for col in df.columns:
                if 'uf' in col.lower() or col.lower() in ['uf', 'sg_uf', 'id_uf']:
                    uf_field = col
                    break
            
            if uf_field:
                df_filtered = df[df[uf_field].astype(str).str.upper() == uf.upper()]
                if len(df_filtered) > 0:
                    df = df_filtered.head(sample_size)
                else:
                    print(f"⚠ Nenhum registro encontrado para UF {uf}. Usando amostra geral...")
                    df = df.head(sample_size)
            else:
                df = df.head(sample_size)
            
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"✓ Arquivo CSV salvo em: {csv_path} ({len(df)} registros)")
            return csv_path
        except Exception as e:
            # Limpa arquivo temporário em caso de erro
            if os.path.exists(tmp_dbf_path):
                os.unlink(tmp_dbf_path)
            raise e
    except ImportError:
        print("⚠ readdbc não disponível. Tentando método alternativo...")
    except Exception as e:
        error_msg = str(e)
        if "Visual C++" in error_msg or "compiler" in error_msg.lower() or "compilação" in error_msg.lower():
            print(f"\n{'='*60}")
            print("⚠ ATENÇÃO: Compilação C++ Necessária")
            print(f"{'='*60}")
            print("Para converter arquivos DBC, é necessário instalar:")
            print("  Microsoft Visual C++ Build Tools")
            print("\n📥 Como instalar:")
            print("  1. Acesse: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
            print("  2. Baixe e instale 'Build Tools for Visual Studio'")
            print("  3. Após instalar, execute:")
            print("     pip install --force-reinstall readdbc")
            print("  4. Execute este pipeline novamente")
            print(f"{'='*60}\n")
            print("  Tentando métodos alternativos...")
        else:
            print(f"⚠ Erro ao usar readdbc: {error_msg[:100]}. Tentando método alternativo...")
    
    # Método alternativo 1: Tentar usar dbc2csv do readdbc diretamente
    try:
        from readdbc import dbc2csv
        print(f"\nTentando converter usando dbc2csv...")
        # dbc2csv converte diretamente para CSV
        try:
            dbc2csv(dbc_path, csv_path)
        except Exception as compile_err:
            if "Visual C++" in str(compile_err) or "compiler" in str(compile_err).lower():
                raise ImportError("Compilação C++ necessária para dbc2csv")
            raise
        
        if os.path.exists(csv_path):
            # Lê o CSV e aplica filtro por UF
            df = pd.read_csv(csv_path, low_memory=False)
            
            # Filtra por UF se o campo existir
            uf_field = None
            for col in df.columns:
                if 'uf' in col.lower() or col.lower() in ['uf', 'sg_uf', 'id_uf']:
                    uf_field = col
                    break
            
            if uf_field:
                df_filtered = df[df[uf_field].astype(str).str.upper() == uf.upper()]
                if len(df_filtered) > 0:
                    df = df_filtered.head(sample_size)
                else:
                    print(f"⚠ Nenhum registro encontrado para UF {uf}. Usando amostra geral...")
                    df = df.head(sample_size)
            else:
                df = df.head(sample_size)
            
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"✓ Arquivo CSV salvo em: {csv_path} ({len(df)} registros)")
            return csv_path
    except ImportError as e:
        if "Compilação C++" in str(e):
            print(f"\n⚠ dbc2csv também requer compilação C++")
            print("  Todos os métodos de conversão precisam das ferramentas instaladas.")
        else:
            print(f"⚠ dbc2csv não funcionou: {str(e)[:100]}")
    except Exception as e:
        print(f"⚠ dbc2csv não funcionou: {str(e)[:100]}")
    
    # Método alternativo 2: DBC -> DBF -> CSV (usando dbc_to_dbf)
    print(f"\n⚠ Todos os métodos de conversão automática falharam.")
    print(f"  Arquivo DBC salvo em: {dbc_path}")
    print(f"  Para converter manualmente, você pode:")
    print(f"    1. Instalar Visual C++ Build Tools e reinstalar readdbc")
    print(f"    2. Usar uma ferramenta externa como TabWin do DATASUS")
    print(f"    3. Processar os arquivos em um ambiente Linux/Docker")
    print(f"\n  Continuando sem converter este arquivo...")
    
    dbf_path = dbc_path.replace(".dbc", ".dbf")

    # 1. Converter DBC para DBF
    try:
        print(f"\nConvertendo {os.path.basename(dbc_path)} para DBF...")
        # Tenta múltiplas formas de importar e usar dbc_to_dbf
        conversion_success = False
        
        # Método 1: Tenta importar como módulo
        try:
            import dbc_to_dbf
            if hasattr(dbc_to_dbf, 'dbc_to_dbf'):
                dbc_to_dbf.dbc_to_dbf(dbc_path, dbf_path)
                conversion_success = True
            elif hasattr(dbc_to_dbf, 'convert'):
                dbc_to_dbf.convert(dbc_path, dbf_path)
                conversion_success = True
        except:
            pass
        
        # Método 2: Tenta importar função diretamente
        if not conversion_success:
            try:
                from dbc_to_dbf import dbc_to_dbf as convert_func
                convert_func(dbc_path, dbf_path)
                conversion_success = True
            except:
                pass
        
        # Método 3: Tenta usar subprocess com script Python
        if not conversion_success:
            try:
                # Procura por script de conversão no site-packages
                import site
                import glob
                for path in site.getsitepackages():
                    script_path = glob.glob(os.path.join(path, '*dbc*dbf*.py'))
                    if script_path:
                        result = subprocess.run(
                            [sys.executable, script_path[0], dbc_path, dbf_path],
                            capture_output=True,
                            timeout=300
                        )
                        if result.returncode == 0:
                            conversion_success = True
            except:
                pass
        
        if conversion_success:
            print(f"✓ Arquivo DBF salvo em: {dbf_path}")
        else:
            raise Exception("Não foi possível converter DBC para DBF com nenhum método disponível")
            
    except Exception as e:
        print(f"✗ Erro na conversão de DBC para DBF: {e}")
        print("  Tentando usar biblioteca alternativa...")
        # Tenta usar readdbc se disponível
        try:
            import readdbc
            df = readdbc.read_dbc(dbc_path)
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"✓ Arquivo CSV salvo diretamente de DBC em: {csv_path}")
            return csv_path
        except ImportError:
            print("  Instalando readdbc como alternativa...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "readdbc"], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                import readdbc
                df = readdbc.read_dbc(dbc_path)
                df.to_csv(csv_path, index=False, encoding='utf-8')
                print(f"✓ Arquivo CSV salvo diretamente de DBC em: {csv_path}")
                return csv_path
            except Exception as e3:
                print(f"  ✗ Não foi possível converter o arquivo: {e3}")
                return None

    # 2. Converter DBF para CSV com filtro por UF e amostragem
    try:
        print(f"Convertendo {os.path.basename(dbf_path)} para CSV...")
        table = DBF(dbf_path, encoding='latin-1')
        
        # Lê os dados e filtra por UF
        records = []
        uf_field = None
        
        # Identifica o campo de UF (pode variar: UF, ID_UF, etc.)
        if len(table) > 0:
            first_record = next(iter(table))
            for field in table.field_names:
                if 'uf' in field.lower() or field.lower() in ['uf', 'sg_uf', 'id_uf']:
                    uf_field = field
                    break
        
        count = 0
        for record in table:
            # Filtra por UF se o campo existir
            if uf_field and record.get(uf_field, '').upper() == uf.upper():
                records.append(record)
                count += 1
                if count >= sample_size:
                    break
            elif not uf_field:
                # Se não encontrar campo UF, pega apenas uma amostra
                records.append(record)
                count += 1
                if count >= sample_size:
                    break
        
        if not records:
            print(f"⚠ Nenhum registro encontrado para UF {uf}. Usando amostra geral...")
            # Se não encontrou registros da UF, pega uma amostra geral
            records = list(table)[:sample_size]
        
        df = pd.DataFrame(records)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"✓ Arquivo CSV salvo em: {csv_path} ({len(df)} registros)")
        return csv_path
        
    except Exception as e:
        print(f"✗ Erro na conversão de DBF para CSV: {e}")
        return None

def analyze_completeness(csv_path: str, agravo_name: str = "") -> Optional[Dict]:
    """
    Analisa a completude dos dados em um arquivo CSV.
    
    Returns:
        Dicionário com estatísticas de completude ou None
    """
    if not csv_path or not os.path.exists(csv_path):
        return None

    print(f"\nAnalisando a completude do arquivo {os.path.basename(csv_path)}...")
    
    try:
        df = pd.read_csv(csv_path, low_memory=False)
        
        total_records = len(df)
        total_fields = len(df.columns)
        
        if total_records == 0:
            print("⚠ Arquivo vazio. Nenhum registro para analisar.")
            return None
        
        # Calcula completude por campo
        completeness_report = []
        for column in df.columns:
            non_null_count = df[column].count()
            completeness_pct = (non_null_count / total_records) * 100 if total_records > 0 else 0
            completeness_report.append({
                "Campo": column,
                "Registros_Preenchidos": non_null_count,
                "Total_Registros": total_records,
                "Completude_%": round(completeness_pct, 2)
            })
        
        report_df = pd.DataFrame(completeness_report)
        report_df = report_df.sort_values(by="Completude_%", ascending=False)
        
        # Calcula estatísticas gerais
        avg_completeness = report_df["Completude_%"].mean()
        median_completeness = report_df["Completude_%"].median()
        fields_100 = len(report_df[report_df["Completude_%"] == 100])
        fields_0 = len(report_df[report_df["Completude_%"] == 0])
        
        # Salva relatório individual
        report_path = csv_path.replace(".csv", "_relatorio_completude.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"RELATÓRIO DE COMPLETUDE - {agravo_name}\n")
            f.write("="*80 + "\n\n")
            f.write(f"Total de Registros: {total_records}\n")
            f.write(f"Total de Campos: {total_fields}\n")
            f.write(f"Completude Média: {avg_completeness:.2f}%\n")
            f.write(f"Completude Mediana: {median_completeness:.2f}%\n")
            f.write(f"Campos 100% preenchidos: {fields_100}\n")
            f.write(f"Campos 0% preenchidos: {fields_0}\n\n")
            f.write("Detalhamento por Campo:\n")
            f.write("-"*80 + "\n")
            f.write(report_df.to_string(index=False))
        
        print(f"✓ Completude média: {avg_completeness:.2f}%")
        print(f"✓ Relatório salvo em: {report_path}")
        
        return {
            'agravo': agravo_name,
            'total_registros': total_records,
            'total_campos': total_fields,
            'completude_media': round(avg_completeness, 2),
            'completude_mediana': round(median_completeness, 2),
            'campos_100_pct': fields_100,
            'campos_0_pct': fields_0,
            'detalhes': report_df
        }
        
    except Exception as e:
        print(f"✗ Erro ao analisar completude: {e}")
        return None

def detect_agravos_with_data(output_dir: str = "./sinan_data", ano: int = 2022) -> List[Dict]:
    """
    Detecta automaticamente quais agravos já têm dados baixados (arquivos .dbc).
    
    Args:
        output_dir: Diretório onde os dados estão armazenados
        ano: Ano dos dados
    
    Returns:
        Lista de dicionários com informações dos agravos encontrados
    """
    agravos_encontrados = []
    
    if not os.path.exists(output_dir):
        return agravos_encontrados
    
    # Mapeamento específico de códigos para nomes legíveis
    code_to_display_name = {
        'deng': 'Dengue - Casos',
        'hiva': 'HIV/AIDS',
        'hiv': 'HIV/AIDS',
        'aids': 'HIV/AIDS',
        'lept': 'Leptospirose',
        'sifa': 'Sífilis (Adquirida)',
        'sifi': 'Sífilis',
        'tube': 'Tuberculose',
        'hepa': 'Hepatites Virais',
        'chik': 'Febre de Chikungunya',
        'zika': 'Zika',
        'hans': 'Hanseníase',
        'meni': 'Meningite',
        'fama': 'Febre Amarela',
        'sara': 'Sarampo',
        'rube': 'Rubéola',
        'coqu': 'Coqueluche',
        'dift': 'Difteria',
        'teta': 'Tétano',
        'poli': 'Poliomielite',
        'raiv': 'Raiva Humana',
        'vari': 'Varicela',
        'cole': 'Cólera',
        'botu': 'Botulismo',
        'pest': 'Peste',
        'hant': 'Hantavirose',
        'rmac': 'Febre Maculosa',
        'ftif': 'Febre Tifoide',
        'esqu': 'Esquistossomose',
        'espo': 'Esporotricose',
        'lta': 'Leishmaniose Tegumentar',
        'leiv': 'Leishmaniose Visceral',
        'malar': 'Malária',
        'into': 'Intoxicação Exógena',
        'viol': 'Violência',
        'acbr': 'Acidente de Trabalho',
        'acbi': 'Acidente de Trabalho com Material Biológico',
        'anim': 'Acidente por Animal Peçonhento',
        'rabr': 'Acidente por Animal com Raiva',
    }
    
    # Mapeamento reverso: código DATASUS -> chave do agravo
    code_to_key = {}
    for key, code in AGRAVOS_MAP.items():
        if code not in code_to_key:
            code_to_key[code] = key
    
    # Busca por diretórios sinan-*
    for item in os.listdir(output_dir):
        item_path = os.path.join(output_dir, item)
        if os.path.isdir(item_path) and item.startswith("sinan-"):
            # Extrai código do agravo do nome do diretório (ex: sinan-deng -> deng)
            code = item.replace("sinan-", "").lower()
            
            # Verifica se há arquivos .dbc no subdiretório do ano
            ano_dir = os.path.join(item_path, str(ano))
            if os.path.exists(ano_dir):
                dbc_files = [f for f in os.listdir(ano_dir) if f.endswith(".dbc")]
                if dbc_files:
                    # Tenta encontrar nome do agravo no mapeamento
                    nome = code_to_display_name.get(code, None)
                    
                    if not nome and code in code_to_key:
                        # Usa a chave do mapeamento e converte para nome legível
                        chave = code_to_key[code]
                        nome = chave.replace("-", " ").title()
                    
                    if not nome:
                        nome = code.upper()
                    
                    chave = code_to_key.get(code, code)
                    
                    agravos_encontrados.append({
                        'numero': '',
                        'nome': nome,
                        'codigo': code,
                        'chave': chave
                    })
    
    return agravos_encontrados

def process_multiple_agravos(agravos: List[Dict], ano: int, uf: str = "SP", 
                            sample_size: int = 1000, output_dir: str = "./sinan_data",
                            use_existing_dbc: bool = True) -> List[Dict]:
    """
    Processa múltiplos agravos e retorna estatísticas consolidadas.
    
    Args:
        agravos: Lista de dicionários com informações dos agravos
        ano: Ano dos dados
        uf: Unidade Federativa
        sample_size: Tamanho da amostra por agravo
        output_dir: Diretório de saída
        use_existing_dbc: Se True, tenta usar arquivos .dbc já baixados antes de baixar novos
    
    Returns:
        Lista de dicionários com estatísticas de completude
    """
    results = []
    total = len(agravos)
    
    print(f"\n{'='*80}")
    print(f"PROCESSANDO {total} AGRAVOS")
    print(f"Ano: {ano} | UF: {uf} | Amostra por agravo: {sample_size} registros")
    print(f"{'='*80}\n")
    
    for idx, agravo in enumerate(agravos, 1):
        print(f"\n[{idx}/{total}] Processando: {agravo['nome']} ({agravo['codigo']})")
        
        try:
            # 1. Tenta encontrar arquivo .dbc existente primeiro
            dbc_path = None
            if use_existing_dbc:
                dataset_name = f"sinan-{agravo['codigo'].lower()}"
                ano_dir = os.path.join(output_dir, dataset_name, str(ano))
                if os.path.exists(ano_dir):
                    dbc_files = [f for f in os.listdir(ano_dir) if f.endswith(".dbc")]
                    if dbc_files:
                        dbc_path = os.path.join(ano_dir, dbc_files[0])
                        print(f"  ✓ Usando arquivo DBC existente: {os.path.basename(dbc_path)}")
            
            # 2. Se não encontrou, tenta baixar
            if not dbc_path:
                dbc_path = download_data(agravo['codigo'], ano, uf, output_dir, sample_size)
                if not dbc_path:
                    print(f"⚠ Pulando {agravo['nome']} - dados não disponíveis")
                    results.append({
                        'agravo': agravo['nome'],
                        'codigo': agravo['codigo'],
                        'status': 'erro_download',
                        'completude_media': None
                    })
                    continue
            
            # 3. Verifica se já existe CSV convertido
            csv_path = None
            if dbc_path:
                csv_path = dbc_path.replace(".dbc", ".csv")
                if not os.path.exists(csv_path):
                    # 4. Conversão
                    csv_path = convert_dbc_to_csv(dbc_path, uf, sample_size)
                    if not csv_path:
                        print(f"⚠ Pulando {agravo['nome']} - erro na conversão")
                        results.append({
                            'agravo': agravo['nome'],
                            'codigo': agravo['codigo'],
                            'status': 'erro_conversao',
                            'completude_media': None
                        })
                        continue
                else:
                    print(f"  ✓ Usando arquivo CSV existente: {os.path.basename(csv_path)}")
            
            # 5. Análise
            stats = analyze_completeness(csv_path, agravo['nome'])
            if stats:
                stats['codigo'] = agravo['codigo']
                stats['status'] = 'sucesso'
                results.append(stats)
            else:
                results.append({
                    'agravo': agravo['nome'],
                    'codigo': agravo['codigo'],
                    'status': 'erro_analise',
                    'completude_media': None
                })
        
        except Exception as e:
            print(f"✗ Erro ao processar {agravo['nome']}: {e}")
            results.append({
                'agravo': agravo['nome'],
                'codigo': agravo['codigo'],
                'status': 'erro',
                'completude_media': None
            })
    
    return results

def generate_consolidated_report(results: List[Dict], output_dir: str = "./sinan_data", 
                                 ano: int = 2022, uf: str = "SP") -> str:
    """
    Gera relatório consolidado com todos os agravos.
    
    Returns:
        Caminho do arquivo de relatório consolidado
    """
    print(f"\n{'='*80}")
    print("GERANDO RELATÓRIO CONSOLIDADO")
    print(f"{'='*80}\n")
    
    # Prepara dados para tabela consolidada
    consolidated_data = []
    for result in results:
        if result.get('status') == 'sucesso' and result.get('completude_media') is not None:
            consolidated_data.append({
                'Agravo': result.get('agravo', 'N/A'),
                'Código': result.get('codigo', 'N/A'),
                'Total_Registros': result.get('total_registros', 0),
                'Total_Campos': result.get('total_campos', 0),
                'Completude_Média_%': result.get('completude_media', 0),
                'Completude_Mediana_%': result.get('completude_mediana', 0),
                'Campos_100%': result.get('campos_100_pct', 0),
                'Campos_0%': result.get('campos_0_pct', 0),
                'Status': '✓ Sucesso'
            })
        else:
            consolidated_data.append({
                'Agravo': result.get('agravo', 'N/A'),
                'Código': result.get('codigo', 'N/A'),
                'Total_Registros': 0,
                'Total_Campos': 0,
                'Completude_Média_%': None,
                'Completude_Mediana_%': None,
                'Campos_100%': 0,
                'Campos_0%': 0,
                'Status': f"✗ {result.get('status', 'erro')}"
            })
    
    if not consolidated_data:
        print("⚠ Nenhum dado disponível para gerar relatório consolidado.")
        return ""
    
    df_consolidated = pd.DataFrame(consolidated_data)
    df_consolidated = df_consolidated.sort_values(by='Completude_Média_%', ascending=False, na_position='last')
    
    # Salva em CSV
    csv_report_path = os.path.join(output_dir, f"relatorio_consolidado_completude_{ano}_{uf}.csv")
    df_consolidated.to_csv(csv_report_path, index=False, encoding='utf-8-sig')
    print(f"✓ Relatório CSV salvo em: {csv_report_path}")
    
    # Salva em TXT para visualização
    txt_report_path = os.path.join(output_dir, f"relatorio_consolidado_completude_{ano}_{uf}.txt")
    with open(txt_report_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write(f"RELATÓRIO CONSOLIDADO DE COMPLETUDE - SINAN\n")
        f.write(f"Ano: {ano} | UF: {uf}\n")
        f.write("="*80 + "\n\n")
        f.write(df_consolidated.to_string(index=False))
        f.write("\n\n" + "="*80 + "\n")
        f.write("RESUMO ESTATÍSTICO\n")
        f.write("="*80 + "\n")
        f.write(f"Total de Agravos Processados: {len(results)}\n")
        f.write(f"Agravos com Sucesso: {len([r for r in results if r.get('status') == 'sucesso'])}\n")
        f.write(f"Agravos com Erro: {len([r for r in results if r.get('status') != 'sucesso'])}\n")
        if not df_consolidated['Completude_Média_%'].isna().all():
            f.write(f"Completude Média Geral: {df_consolidated['Completude_Média_%'].mean():.2f}%\n")
    
    print(f"✓ Relatório TXT salvo em: {txt_report_path}")
    
    # Salva em Excel (se possível)
    excel_report_path = None
    try:
        excel_report_path = os.path.join(output_dir, f"relatorio_consolidado_completude_{ano}_{uf}.xlsx")
        with pd.ExcelWriter(excel_report_path, engine='openpyxl') as writer:
            df_consolidated.to_excel(writer, sheet_name='Completude por Agravo', index=False)
            
            # Adiciona estatísticas gerais em outra aba
            stats_summary = {
                'Métrica': [
                    'Total de Agravos Processados',
                    'Agravos com Sucesso',
                    'Agravos com Erro',
                    'Completude Média Geral',
                    'Agravo com Maior Completude',
                    'Agravo com Menor Completude'
                ],
                'Valor': [
                    len(results),
                    len([r for r in results if r.get('status') == 'sucesso']),
                    len([r for r in results if r.get('status') != 'sucesso']),
                    f"{df_consolidated['Completude_Média_%'].mean():.2f}%",
                    df_consolidated.loc[df_consolidated['Completude_Média_%'].idxmax(), 'Agravo'] if not df_consolidated['Completude_Média_%'].isna().all() else 'N/A',
                    df_consolidated.loc[df_consolidated['Completude_Média_%'].idxmin(), 'Agravo'] if not df_consolidated['Completude_Média_%'].isna().all() else 'N/A'
                ]
            }
            pd.DataFrame(stats_summary).to_excel(writer, sheet_name='Resumo', index=False)
        
        print(f"✓ Relatório Excel salvo em: {excel_report_path}")
    except ImportError:
        print("⚠ openpyxl não instalado. Relatório Excel não gerado. Instale com: pip install openpyxl")
    
    return excel_report_path if excel_report_path else csv_report_path

# --- Execução Principal ---

def main():
    """Função principal que orquestra a execução do pipeline."""
    # --- Parâmetros de Entrada ---
    ANO = 2022       # Ano dos dados
    UF = "SP"        # Unidade Federativa (SP, RJ, MG, etc.)
    SAMPLE_SIZE = 1000  # Tamanho da amostra por agravo
    OUTPUT_DIR = "./sinan_data"
    PROCESS_ALL_AVAILABLE = True  # Se True, processa todos os agravos com dados disponíveis
    
    print("="*80)
    print("PIPELINE DE ANÁLISE DE COMPLETUDE DE DADOS DO SINAN")
    print("="*80)
    print(f"\nConfigurações:")
    print(f"  - Ano: {ANO}")
    print(f"  - UF: {UF}")
    print(f"  - Amostra por agravo: {SAMPLE_SIZE} registros")
    print(f"  - Diretório de saída: {OUTPUT_DIR}")
    print()
    
    # 1. Instalar dependências
    install_dependencies()
    
    # 2. Detectar agravos com dados disponíveis
    if PROCESS_ALL_AVAILABLE:
        print("🔍 Detectando agravos com dados disponíveis...")
        agravos = detect_agravos_with_data(OUTPUT_DIR, ANO)
        
        if not agravos:
            print("⚠ Nenhum agravo com dados encontrado. Tentando extrair da tabela...")
            # Fallback: tenta extrair da tabela
            agravos = extract_agravos_from_table()
            if agravos:
                print(f"✓ {len(agravos)} agravos extraídos da tabela")
        else:
            print(f"✓ {len(agravos)} agravos com dados encontrados:")
            for idx, agravo in enumerate(agravos, 1):
                print(f"  {idx}. {agravo['nome']} ({agravo['codigo']})")
    else:
        # Lista de agravos principais a processar
        # Nota: Códigos corrigidos conforme disponibilidade no datasus-fetcher
        AGRAVOS_PRINCIPAIS = [
            {'numero': '9', 'nome': 'Dengue - Casos', 'codigo': 'deng', 'chave': 'dengue'},
            {'numero': '54', 'nome': 'Sífilis (Adquirida)', 'codigo': 'sifa', 'chave': 'sifilis'},
            {'numero': '63', 'nome': 'Tuberculose', 'codigo': 'tube', 'chave': 'tuberculose'},
            {'numero': '33', 'nome': 'HIV/AIDS', 'codigo': 'hiva', 'chave': 'hiv-aids'},
            {'numero': '42', 'nome': 'Leptospirose', 'codigo': 'lept', 'chave': 'leptospirose'},
        ]
        agravos = AGRAVOS_PRINCIPAIS
        print(f"✓ {len(agravos)} agravos configurados para processar")
    
    print()
    
    # 3. Processar múltiplos agravos
    results = process_multiple_agravos(agravos, ANO, UF, SAMPLE_SIZE, OUTPUT_DIR, use_existing_dbc=True)
    
    # 4. Gerar relatório consolidado
    report_path = generate_consolidated_report(results, OUTPUT_DIR, ANO, UF)
    
    print("\n" + "="*80)
    print("PIPELINE CONCLUÍDO")
    print("="*80)
    
    # Estatísticas finais
    sucesso = len([r for r in results if r.get('status') == 'sucesso'])
    erros = len([r for r in results if r.get('status') != 'sucesso'])
    
    print(f"\n📊 RESUMO DA EXECUÇÃO:")
    print(f"  ✓ Agravos processados com sucesso: {sucesso}/{len(results)}")
    print(f"  ✗ Agravos com erro: {erros}/{len(results)}")
    
    if sucesso > 0:
        print(f"\n✅ Relatórios gerados em: {OUTPUT_DIR}")
        if report_path:
            print(f"📄 Relatório consolidado: {report_path}")
    
    if erros > 0:
        print(f"\n⚠ ATENÇÃO: {erros} agravo(s) não puderam ser processados.")
        print("  Possíveis causas:")
        print("    - Arquivos DBC não podem ser convertidos sem Visual C++ Build Tools")
        print("    - Agravos não disponíveis para o ano/região especificados")
        print("\n  Para resolver problemas de conversão DBC:")
        print("    1. Instale Visual C++ Build Tools:")
        print("       https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        print("    2. Reinstale readdbc: pip install --force-reinstall readdbc")
        print("    3. Execute o pipeline novamente")
    
    print()

if __name__ == "__main__":
    main()
