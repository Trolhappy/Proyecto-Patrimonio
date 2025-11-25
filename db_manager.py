import sqlite3

DB_PATH = "database.db"

# ============================
#    CONEXIÓN A LA BD
# ============================

def conectar():
    return sqlite3.connect(DB_PATH)

# ============================
#     CONSULTAR INVENTARIO
# ============================

def obtener_inventario_por_lugar(nombre_lugar):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT id FROM lugares WHERE nombre = ?;", (nombre_lugar,))
    lugar = cur.fetchone()
    if not lugar:
        conn.close()
        return []

    lugar_id = lugar[0]

    cur.execute("""
        SELECT id, Cantidad, Objeto, Codigo, Marca, Modelo, Serie, Observaciones
        FROM inventario
        WHERE lugar_id = ?
        ORDER BY Objeto;
    """, (lugar_id,))

    datos = cur.fetchall()
    conn.close()
    return datos

# ============================
#         REGISTRAR
# ============================

def registrar_item(nombre_lugar, cantidad, objeto, codigo, marca, modelo, serie, observaciones):
    conn = conectar()
    cur = conn.cursor()

    # obtener ID del lugar
    cur.execute("SELECT id FROM lugares WHERE nombre = ?;", (nombre_lugar,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False

    lugar_id = row[0]

    cur.execute("""
        INSERT INTO inventario (lugar_id, Cantidad, Objeto, Codigo, Marca, Modelo, Serie, Observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (lugar_id, cantidad, objeto, codigo, marca, modelo, serie, observaciones))

    conn.commit()
    conn.close()
    return True

# ============================
#         MODIFICAR
# ============================

def modificar_item(id_item, cantidad, objeto, codigo, marca, modelo, serie, observaciones):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        UPDATE inventario
        SET Cantidad = ?, Objeto = ?, Codigo = ?, Marca = ?, Modelo = ?, Serie = ?, Observaciones = ?
        WHERE id = ?
    """, (cantidad, objeto, codigo, marca, modelo, serie, observaciones, id_item))

    conn.commit()
    conn.close()
    return True

# ============================
#          ELIMINAR
# ============================

def eliminar_item(id_item):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("DELETE FROM inventario WHERE id = ?;", (id_item,))

    conn.commit()
    conn.close()
    return True
