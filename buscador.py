import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
from PIL import Image, ImageTk

DB_PATH = "database.db"

def cargar_imagen(ruta, size=(30, 30)):
    try:
        img = Image.open(ruta)
        img = img.resize(size)
        return ImageTk.PhotoImage(img)
    except:
        return None

def buscar_en_todos_lugares(texto):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    like = f"%{texto}%"
    cur.execute("""
        SELECT l.nombre, i.Cantidad, i.Objeto, i.Codigo, i.Marca, i.Modelo, i.Serie, i.Observaciones
        FROM inventario i
        JOIN lugares l ON l.id = i.lugar_id
        WHERE
            i.Objeto LIKE ?
            OR i.Marca LIKE ?
            OR i.Modelo LIKE ?
            OR i.Serie LIKE ?
            OR i.Codigo LIKE ?
            OR i.Observaciones LIKE ?
        ORDER BY l.nombre ASC;
    """, (like, like, like, like, like, like))

    datos = cur.fetchall()
    conn.close()
    return datos


def obtener_todo_el_inventario():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT l.nombre, i.Cantidad, i.Objeto, i.Codigo, i.Marca, i.Modelo, i.Serie, i.Observaciones
        FROM inventario i
        JOIN lugares l ON l.id = i.lugar_id
        ORDER BY l.nombre;
    """)

    datos = cur.fetchall()
    conn.close()
    return datos


def abrir_buscador():
    ventana = tk.Toplevel()
    ventana.title("Buscar en Inventario")
    ventana.geometry("1000x600")
    ventana.resizable(False, False)

    frame = tk.Frame(ventana, bg="#C6D9E3")
    frame.pack(fill="both", expand=True)

    # Campo de búsqueda
    tk.Label(
        frame, text="Buscar:", font=("Sans", 14, "bold"), bg="#C6D9E3"
    ).place(x=20, y=25)

    entry_buscar = ttk.Entry(frame, font=("Sans", 14))
    entry_buscar.place(x=120, y=20, width=300, height=40)

    # --------- TABLA RESULTADOS ---------
    tree_frame = tk.Frame(frame, bg="white")
    tree_frame.place(x=20, y=70, width=950, height=500)

    scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

    tree = ttk.Treeview(
        tree_frame,
        yscrollcommand=scroll_y.set,
        columns=("Lugar", "Cantidad", "Objeto", "Código",
                 "Marca", "Modelo", "Serie", "Observaciones"),
        show="headings",
        height=40,
    )
    tree.pack(expand=True, fill="both")
    scroll_y.config(command=tree.yview)

    # Encabezados
    encabezados = ["Lugar", "Cantidad", "Objeto", "Código",
                   "Marca", "Modelo", "Serie", "Observaciones"]
    for col in encabezados:
        tree.heading(col, text=col)

    # Columnas
    tree.column("Lugar", width=120, anchor="center")
    tree.column("Cantidad", width=80, anchor="center")
    tree.column("Objeto", width=150, anchor="center")
    tree.column("Código", width=80, anchor="center")
    tree.column("Marca", width=100, anchor="center")
    tree.column("Modelo", width=100, anchor="center")
    tree.column("Serie", width=100, anchor="center")
    tree.column("Observaciones", width=200, anchor="center")

    # --------- FUNCIONES DE BÚSQUEDA ---------
    def ejecutar_busqueda():
        texto = entry_buscar.get().strip()
        for row in tree.get_children():
            tree.delete(row)

        if texto:
            resultados = buscar_en_todos_lugares(texto)
            for fila in resultados:
                tree.insert("", tk.END, values=fila)

    def ejecutar_ver_todo():
        for row in tree.get_children():
            tree.delete(row)

        resultados = obtener_todo_el_inventario()
        for fila in resultados:
            tree.insert("", tk.END, values=fila)

    def exportar_excel():
        # Obtener todas las filas actuales del Treeview
        rows = [tree.item(i, "values") for i in tree.get_children()]

        if not rows:
            messagebox.showinfo("Exportar", "No hay datos en la tabla para exportar.")
            return

        # Elegir dónde guardar
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Archivo de Excel", "*.xlsx"), ("Todos los archivos", "*.*")],
            title="Guardar como"
        )
        if not file_path:
            return  # Usuario canceló

        # Encabezados de las columnas (mismos que en el Treeview)
        headers = ["Lugar", "Cantidad", "Objeto", "Código",
                   "Marca", "Modelo", "Serie", "Observaciones"]

        try:
            from openpyxl import Workbook

            wb = Workbook()
            ws = wb.active
            ws.title = "Inventario"

            # Escribir encabezados
            ws.append(headers)

            # Escribir filas
            for row in rows:
                ws.append(list(row))

            wb.save(file_path)
            messagebox.showinfo("Exportar", f"Inventario exportado correctamente a:\n{file_path}")

        except ImportError:
            # Si no está openpyxl, guardamos como CSV
            import csv
            csv_path = file_path.rsplit(".", 1)[0] + ".csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in rows:
                    writer.writerow(row)
            messagebox.showinfo(
                "Exportar",
                f"No se encontró 'openpyxl'.\nSe exportó en formato CSV:\n{csv_path}\n"
                "Puedes abrirlo con Excel."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al exportar:\n{e}")

    # Botones
    btn_buscar = tk.Button(frame, text="Buscar", font=("Roboto", 12, "bold"), command=ejecutar_busqueda)
    btn_buscar.place(x=450, y=20, width=100, height=40)

    btn_todo = tk.Button(frame, text="Ver Todo El Inventario", font=("Roboto", 12, "bold"), command=ejecutar_ver_todo)
    btn_todo.place(x=570, y=20, width=180, height=40)


    # Imagen para el botón exportar
    img_exportar = cargar_imagen("icono/excel.png", size=(30, 30))

    btn_exportar = tk.Button(frame, text="Exportar", font=("Roboto", 12, "bold"), compound="left", padx=10, command=exportar_excel)

    if img_exportar:
        btn_exportar.config(image=img_exportar)
        btn_exportar.image = img_exportar  # evitar garbage collector

    btn_exportar.place(x=770, y=20, width=130, height=40)
