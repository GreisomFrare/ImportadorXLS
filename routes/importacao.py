import csv
import io
import json
import os
import re
from flask import Blueprint, request, jsonify
from models import get_db
import db_oracle
import openpyxl
import xlrd

importacao_bp = Blueprint('importacao', __name__)

_RE_MOEDA_BR = re.compile(r'^\s*(-?)\s*R?\$?\s*([\d.]*\d+),(\d{2})\s*$', re.IGNORECASE)

def _aplicar_substr(val, regra):
    """Aplica recorte de string. regra: '-6' = últimos 6, '0:6' = primeiros 6, '3:9' = posição 3 a 9."""
    if not regra or not isinstance(val, str):
        return val
    regra = regra.strip()
    try:
        if ':' in regra:
            partes = regra.split(':', 1)
            de = int(partes[0]) if partes[0] else None
            ate = int(partes[1]) if partes[1] else None
            return val[de:ate]
        else:
            n = int(regra)
            return val[n:] if n >= 0 else val[n:]
    except (ValueError, TypeError):
        return val

def _normalizar_numero_br(val):
    """Converte 'R$ 1.234,56' → '1234.56'. Retorna o valor original se não bater."""
    if not isinstance(val, str):
        return val
    m = _RE_MOEDA_BR.match(val)
    if m:
        sinal, inteiros, decimais = m.group(1), m.group(2).replace('.', ''), m.group(3)
        return f'{sinal}{inteiros}.{decimais}'
    return val

def _avaliar_formula(formula, linha):
    """Avalia fórmula com referências de colunas: {E}-{F} ou {5}-{6}."""
    def resolver_col(m):
        ref = m.group(1)
        idx = int(ref) - 1 if ref.isdigit() else _letra_para_indice(ref)
        val = linha[idx] if idx < len(linha) else ''
        if val == '' or val is None:
            return '0'
        val = _normalizar_numero_br(str(val))
        try:
            float(val)
            return val
        except (ValueError, TypeError):
            return '0'
    expr = re.sub(r'\{([A-Za-z0-9]+)\}', resolver_col, formula)
    try:
        result = eval(expr, {'__builtins__': {}}, {})  # noqa: S307
        return str(round(float(result), 2))
    except Exception:
        return None

def _letra_para_indice(letra):
    resultado = 0
    for c in letra.upper():
        resultado = resultado * 26 + (ord(c) - ord('A') + 1)
    return resultado - 1

def _indice_para_letra(idx):
    result = ''
    while True:
        result = chr(ord('A') + idx % 26) + result
        idx = idx // 26 - 1
        if idx < 0:
            break
    return result

def _ler_planilha(file_bytes, tipo, separador, linha_inicio):
    if tipo == 'csv':
        texto = file_bytes.decode('utf-8-sig', errors='replace')
        todas = list(csv.reader(io.StringIO(texto), delimiter=separador))
        cabecalho = todas[linha_inicio - 2] if linha_inicio > 1 and len(todas) >= linha_inicio - 1 else []
        linhas = todas[linha_inicio - 1:] if len(todas) >= linha_inicio else []
        return cabecalho, linhas

    elif tipo == 'xls':
        wb = xlrd.open_workbook(file_contents=file_bytes)
        ws = wb.sheet_by_index(0)
        cabecalho = ([str(ws.cell_value(linha_inicio - 2, c)) for c in range(ws.ncols)]
                     if linha_inicio > 1 else [])
        linhas = [[str(ws.cell_value(r, c)) for c in range(ws.ncols)]
                  for r in range(linha_inicio - 1, ws.nrows)]
        return cabecalho, linhas

    else:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
        ws = wb.active
        todas = list(ws.iter_rows(values_only=True))
        wb.close()
        cabecalho = (['' if v is None else str(v) for v in todas[linha_inicio - 2]]
                     if linha_inicio > 1 and len(todas) >= linha_inicio - 1 else [])
        linhas = [['' if v is None else str(v) for v in row] for row in todas[linha_inicio - 1:]]
        return cabecalho, linhas

@importacao_bp.route('/preview', methods=['POST'])
def preview():
    if 'arquivo' not in request.files:
        return jsonify({'erro': 'Arquivo não enviado'}), 400
    layout_id = request.form.get('layout_id')
    if not layout_id:
        return jsonify({'erro': 'Layout não informado'}), 400

    db = get_db()
    layout = db.execute("SELECT * FROM layouts WHERE id = ?", (layout_id,)).fetchone()
    if not layout:
        return jsonify({'erro': 'Layout não encontrado'}), 404

    layout = dict(layout)
    campos = [dict(c) for c in db.execute(
        "SELECT * FROM campos_layout WHERE layout_id = ? ORDER BY id", (layout_id,)
    ).fetchall()]

    file_bytes = request.files['arquivo'].read()
    try:
        cabecalho, linhas = _ler_planilha(
            file_bytes, layout['tipo_arquivo'], layout['separador_csv'], layout['linha_inicio']
        )
    except Exception as e:
        return jsonify({'erro': f'Erro ao ler arquivo: {e}'}), 400

    return jsonify({
        'cabecalho': cabecalho,
        'total': len(linhas),
        'amostra': linhas[:20],
        'layout': layout,
        'campos': campos
    })

@importacao_bp.route('/cabecalho', methods=['POST'])
def cabecalho_arquivo():
    if 'arquivo' not in request.files:
        return jsonify({'erro': 'Arquivo não enviado'}), 400

    tipo = request.form.get('tipo', 'xlsx')
    separador = request.form.get('separador', ',')
    linha_cab = int(request.form.get('linha_cabecalho', 1))

    file_bytes = request.files['arquivo'].read()
    try:
        cabecalho, _ = _ler_planilha(file_bytes, tipo, separador, linha_cab + 1)
    except Exception as e:
        return jsonify({'erro': f'Erro ao ler arquivo: {e}'}), 400

    colunas = [{'indice': i, 'letra': _indice_para_letra(i), 'cabecalho': h or _indice_para_letra(i)}
               for i, h in enumerate(cabecalho)]
    return jsonify({'colunas': colunas})

@importacao_bp.route('/executar', methods=['POST'])
def executar():
    if 'arquivo' not in request.files:
        return jsonify({'erro': 'Arquivo não enviado'}), 400
    layout_id = request.form.get('layout_id')
    if not layout_id:
        return jsonify({'erro': 'Layout não informado'}), 400

    db = get_db()
    layout = db.execute("SELECT * FROM layouts WHERE id = ?", (layout_id,)).fetchone()
    if not layout:
        return jsonify({'erro': 'Layout não encontrado'}), 404

    layout = dict(layout)
    campos = [dict(c) for c in db.execute(
        "SELECT * FROM campos_layout WHERE layout_id = ?", (layout_id,)
    ).fetchall()]

    if not campos:
        return jsonify({'erro': 'Layout sem mapeamento de campos configurado'}), 400

    arquivo = request.files['arquivo']
    nome_arquivo = arquivo.filename
    file_bytes = arquivo.read()

    try:
        _, linhas = _ler_planilha(
            file_bytes, layout['tipo_arquivo'], layout['separador_csv'], layout['linha_inicio']
        )
    except Exception as e:
        return jsonify({'erro': f'Erro ao ler arquivo: {e}'}), 400

    try:
        conn = db_oracle.get_connection()
    except Exception as e:
        return jsonify({'erro': f'Erro ao conectar ao Oracle: {e}'}), 500

    # Monta listas separando campos com sequence (usam NEXTVAL inline) dos demais
    cols_sql = []
    vals_sql = []
    campos_bind = []  # apenas campos que usam bind variable

    for c in campos:
        cols_sql.append(c['campo_oracle'])
        if c['tipo_mapeamento'] == 'sequence':
            seq = (c.get('valor_fixo') or '').strip()
            vals_sql.append(f'{seq}.NEXTVAL' if seq else 'NULL')
        else:
            key = c['campo_oracle'].lower().replace(' ', '_')
            mascara = (c.get('mascara_data') or '').strip()
            if mascara:
                vals_sql.append(f"TO_DATE(:{key}, '{mascara}')")
            else:
                vals_sql.append(f':{key}')
            campos_bind.append((c, key))

    sql = (f"INSERT INTO {layout['tabela_oracle']} "
           f"({', '.join(cols_sql)}) VALUES ({', '.join(vals_sql)})")

    cursor = conn.cursor()
    importadas = 0
    erros = 0
    log_erros = []

    for i, linha in enumerate(linhas, start=layout['linha_inicio']):
        try:
            bind = {}
            for campo, key in campos_bind:
                tipo_camp = campo['tipo_mapeamento']
                if tipo_camp == 'fixo':
                    bind[key] = campo.get('valor_fixo')
                elif tipo_camp == 'arquivo':
                    bind[key] = nome_arquivo
                elif tipo_camp == 'calculado':
                    bind[key] = _avaliar_formula(campo.get('valor_fixo') or '', linha)
                else:
                    col = campo.get('coluna_planilha', '')
                    idx = int(col) - 1 if col.isdigit() else _letra_para_indice(col)
                    val = linha[idx] if idx < len(linha) else None
                    if val == '':
                        val = None
                    padrao = campo.get('valor_padrao') or None
                    if val is None:
                        val = padrao
                    elif isinstance(val, str):
                        # De Para de valores: substitui valor da planilha antes de qualquer transformação
                        depara_raw = (campo.get('depara_json') or '').strip()
                        if depara_raw:
                            try:
                                for regra in json.loads(depara_raw):
                                    if str(regra.get('origem', '')) == val:
                                        val = str(regra.get('destino', ''))
                                        break
                            except (json.JSONDecodeError, Exception):
                                pass

                        regex = (campo.get('regex_extrair') or '').strip()
                        if regex:
                            try:
                                m = re.search(regex, val)
                                val = m.group(1) if m and m.lastindex else (m.group(0) if m else None)
                            except re.error:
                                val = None
                            if val is None:
                                val = padrao
                        if val:
                            val = _aplicar_substr(val, campo.get('substr_regra'))
                            val = _normalizar_numero_br(val)
                            # Se ainda não for numérico e houver valor padrão, usa o padrão
                            if padrao and val:
                                try:
                                    float(val)
                                except (ValueError, TypeError):
                                    val = padrao
                    bind[key] = val
            cursor.execute(sql, bind)
            importadas += 1
        except Exception as e:
            erros += 1
            vals_linhas = '\n    '.join(f'{k} = {repr(v)}' for k, v in bind.items())
            log_erros.append(f'Linha {i}: {e}\n    {vals_linhas}')

    conn.commit()
    conn.close()

    db.execute(
        """INSERT INTO importacoes
           (layout_id, nome_layout, nome_arquivo, total_linhas, linhas_importadas, linhas_erro, status, log)
           VALUES (?, ?, ?, ?, ?, ?, 'concluido', ?)""",
        (layout_id, layout['nome'], nome_arquivo, len(linhas), importadas, erros,
         '\n'.join(log_erros) if log_erros else None)
    )
    db.commit()

    return jsonify({
        'ok': True,
        'total': len(linhas),
        'importadas': importadas,
        'erros': erros,
        'log': log_erros[:50]
    })

@importacao_bp.route('/historico', methods=['GET'])
def historico():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM importacoes ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    return jsonify([dict(r) for r in rows])
