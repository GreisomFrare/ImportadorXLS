from flask import Blueprint, request, jsonify
from models import get_db

layouts_bp = Blueprint('layouts', __name__)

@layouts_bp.route('/', methods=['GET'])
def listar():
    db = get_db()
    rows = db.execute("SELECT * FROM layouts ORDER BY nome").fetchall()
    return jsonify([dict(r) for r in rows])

@layouts_bp.route('/', methods=['POST'])
def criar():
    data = request.get_json()
    db = get_db()
    cur = db.execute(
        """INSERT INTO layouts (nome, tipo_arquivo, separador_csv, linha_inicio, tabela_oracle)
           VALUES (:nome, :tipo, :sep, :linha, :tabela)""",
        {
            'nome': data['nome'],
            'tipo': data.get('tipo_arquivo', 'xlsx'),
            'sep': data.get('separador_csv', ','),
            'linha': data.get('linha_inicio', 2),
            'tabela': data['tabela_oracle']
        }
    )
    db.commit()
    return jsonify({'id': cur.lastrowid}), 201

@layouts_bp.route('/<int:layout_id>', methods=['GET'])
def detalhe(layout_id):
    db = get_db()
    layout = db.execute("SELECT * FROM layouts WHERE id = ?", (layout_id,)).fetchone()
    if not layout:
        return jsonify({'erro': 'Layout não encontrado'}), 404
    campos = db.execute(
        "SELECT * FROM campos_layout WHERE layout_id = ? ORDER BY id", (layout_id,)
    ).fetchall()
    return jsonify({**dict(layout), 'campos': [dict(c) for c in campos]})

@layouts_bp.route('/<int:layout_id>', methods=['PUT'])
def atualizar(layout_id):
    data = request.get_json()
    db = get_db()
    db.execute(
        """UPDATE layouts SET nome=:nome, tipo_arquivo=:tipo, separador_csv=:sep,
           linha_inicio=:linha, tabela_oracle=:tabela,
           updated_at=CURRENT_TIMESTAMP WHERE id=:id""",
        {
            'nome': data['nome'],
            'tipo': data.get('tipo_arquivo', 'xlsx'),
            'sep': data.get('separador_csv', ','),
            'linha': data.get('linha_inicio', 2),
            'tabela': data['tabela_oracle'],
            'id': layout_id
        }
    )
    if 'campos' in data:
        db.execute("DELETE FROM campos_layout WHERE layout_id = ?", (layout_id,))
        for campo in data['campos']:
            db.execute(
                """INSERT INTO campos_layout
                   (layout_id, campo_oracle, tipo_mapeamento, coluna_planilha, valor_fixo, mascara_data)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (layout_id, campo['campo_oracle'], campo['tipo_mapeamento'],
                 campo.get('coluna_planilha'), campo.get('valor_fixo'),
                 campo.get('mascara_data') or None)
            )
    db.commit()
    return jsonify({'ok': True})

@layouts_bp.route('/<int:layout_id>', methods=['DELETE'])
def excluir(layout_id):
    db = get_db()
    db.execute("DELETE FROM layouts WHERE id = ?", (layout_id,))
    db.commit()
    return jsonify({'ok': True})
