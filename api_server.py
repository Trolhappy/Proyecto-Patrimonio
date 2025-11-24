import os
from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras

# ==========================
#  CONEXIÓN A POSTGRES
# ==========================

def get_conn():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
    )
    return conn


app = Flask(__name__)


# ==========================
#   HELPERS
# ==========================

def query_all(sql, params=None):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params or [])
    rows = cur.fetchall()
    conn.close()
    return rows


def execute_sql(sql, params=None, return_rowcount=False):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or [])
    conn.commit()
    rc = cur.rowcount
    conn.close()
    if return_rowcount:
        return rc


# ==========================
#   ENDPOINTS
# ==========================

@app.get("/health")
def health():
    return {"status": "ok"}, 200


@app.get("/lugares")
def get_lugares():
    """
    Devuelve lista de lugares:
    [
      { "id": 1, "nombre": "Salon 0" },
      ...
    ]
    """
    sql = """
        SELECT id, nombre
        FROM lugares
        ORDER BY
            CASE WHEN nombre LIKE 'Salon %' THEN 0 ELSE 1 END,
            CASE
                WHEN nombre LIKE 'Salon %' THEN CAST(SUBSTRING(nombre FROM 7) AS INTEGER)
                ELSE nombre
            END;
    """
    rows = query_all(sql)
    return jsonify(rows), 200


@app.get("/inventario")
def get_inventario_por_lugar():
    """
    /inventario?lugar=Salon%200
    Devuelve los items de un lugar.
    """
    nombre_lugar = request.args.get("lugar")
    if not nombre_lugar:
        return {"error": "Falta parámetro 'lugar'"}, 400

    # obtener id del lugar
    sql_lugar = "SELECT id FROM lugares WHERE nombre = %s;"
    lugares = query_all(sql_lugar, (nombre_lugar,))
    if not lugares:
        return jsonify([]), 200

    lugar_id = lugares[0]["id"]

    sql = """
        SELECT id, Cantidad, Objeto, Codigo, Marca, Modelo, Serie, Observaciones
        FROM inventario
        WHERE lugar_id = %s
        ORDER BY Objeto;
    """
    rows = query_all(sql, (lugar_id,))
    return jsonify(rows), 200


@app.get("/inventario/all")
def get_inventario_todo():
    """
    Devuelve TODO el inventario con el nombre del lugar.
    Usado por tu ventana 'Ver todo el inventario'
    """
    sql = """
        SELECT l.nombre AS Lugar,
               i.Cantidad,
               i.Objeto,
               i.Codigo,
               i.Marca,
               i.Modelo,
               i.Serie,
               i.Observaciones
        FROM inventario i
        JOIN lugares l ON l.id = i.lugar_id
        ORDER BY l.nombre, i.Objeto;
    """
    rows = query_all(sql)
    return jsonify(rows), 200


@app.post("/inventario")
def crear_inventario():
    """
    Espera JSON:
    {
      "lugar": "Salon 0",
      "Cantidad": 3,
      "Objeto": "Laptop",
      "Codigo": "123",
      "Marca": "Dell",
      "Modelo": "XPS",
      "Serie": "ABC123",
      "Observaciones": "Buen estado"
    }
    """
    data = request.get_json(force=True)

    nombre_lugar = data.get("lugar")
    if not nombre_lugar:
        return {"error": "Campo 'lugar' es requerido"}, 400

    # buscar id del lugar
    sql_lugar = "SELECT id FROM lugares WHERE nombre = %s;"
    lugares = query_all(sql_lugar, (nombre_lugar,))
    if not lugares:
        return {"error": "Lugar no encontrado"}, 404

    lugar_id = lugares[0]["id"]

    sql = """
        INSERT INTO inventario (lugar_id, Cantidad, Objeto, Codigo, Marca, Modelo, Serie, Observaciones)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """

    execute_sql(sql, (
        lugar_id,
        data.get("Cantidad", 0),
        data.get("Objeto"),
        data.get("Codigo"),
        data.get("Marca", "S/N"),
        data.get("Modelo", "S/N"),
        data.get("Serie", "S/N"),
        data.get("Observaciones", "Sin observaciones"),
    ))

    return {"status": "ok"}, 201


@app.put("/inventario/<int:item_id>")
def actualizar_inventario(item_id):
    """
    PUT /inventario/5
    Body JSON con los campos a actualizar (mismos que crear, sin 'lugar')
    """
    data = request.get_json(force=True)

    sql = """
        UPDATE inventario
        SET Cantidad = %s,
            Objeto = %s,
            Codigo = %s,
            Marca = %s,
            Modelo = %s,
            Serie = %s,
            Observaciones = %s
        WHERE id = %s;
    """

    execute_sql(sql, (
        data.get("Cantidad", 0),
        data.get("Objeto"),
        data.get("Codigo"),
        data.get("Marca", "S/N"),
        data.get("Modelo", "S/N"),
        data.get("Serie", "S/N"),
        data.get("Observaciones", "Sin observaciones"),
        item_id,
    ))

    return {"status": "ok"}, 200


@app.delete("/inventario/<int:item_id>")
def borrar_inventario(item_id):
    """
    DELETE /inventario/5
    """
    sql = "DELETE FROM inventario WHERE id = %s;"
    execute_sql(sql, (item_id,))
    return {"status": "ok"}, 200


@app.get("/buscar")
def buscar_inventario():
    """
    /buscar?q=laptop
    Busca en Objeto, Marca, Modelo, Serie, Codigo, Observaciones
    """
    texto = request.args.get("q", "").strip()
    if not texto:
        return jsonify([]), 200

    like = f"%{texto}%"
    sql = """
        SELECT l.nombre AS Lugar,
               i.Cantidad,
               i.Objeto,
               i.Codigo,
               i.Marca,
               i.Modelo,
               i.Serie,
               i.Observaciones
        FROM inventario i
        JOIN lugares l ON l.id = i.lugar_id
        WHERE
            i.Objeto ILIKE %s OR
            i.Marca ILIKE %s OR
            i.Modelo ILIKE %s OR
            i.Serie ILIKE %s OR
            i.Codigo ILIKE %s OR
            i.Observaciones ILIKE %s
        ORDER BY l.nombre, i.Objeto;
    """
    rows = query_all(sql, (like, like, like, like, like, like))
    return jsonify(rows), 200


if __name__ == "__main__":
    # Para pruebas locales (Render usará gunicorn)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
