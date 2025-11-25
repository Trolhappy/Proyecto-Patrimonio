import tkinter as tk
from tkinter import ttk, Label, Button
from PIL import Image, ImageTk
import sqlite3

from db_manager import (
    obtener_inventario_por_lugar,
    registrar_item,
    modificar_item,
    eliminar_item,
)

DB_PATH = "database.db"


# ------------------ LUGARES (para el ComboBox) ------------------ #
def obtener_lugares():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT nombre
        FROM lugares
        ORDER BY
            CASE WHEN nombre LIKE 'Salon %' THEN 0 ELSE 1 END,
            CASE
                WHEN nombre LIKE 'Salon %' THEN CAST(substr(nombre, 7) AS INTEGER)
                ELSE nombre
            END;
    """)

    nombres = [row[0] for row in cur.fetchall()]
    conn.close()
    return nombres



# -------------------- VENTANA DE SALÓN -------------------- #
def abrir_ventana_salon(nombre_salon="Salon 0"):
    # Ventana secundaria
    ventana = tk.Toplevel()
    ventana.title(nombre_salon)
    ventana.geometry("1300x600")
    ventana.resizable(False, False)

    # Frame principal
    frame = tk.Frame(ventana, bg="#C6D9E3")
    frame.place(x=0, y=0, width=1300, height=600)

    # Marco de formulario
    labelframe = tk.LabelFrame(
        frame, text="Inventario", font=("Sans", 22, "bold"), bg="#C6D9E3"
    )
    labelframe.place(x=10, y=10, width=450, height=570)

    # ---------- VARIABLES DE FORMULARIO ----------
    selected_id = tk.StringVar(value="")
    cantidad_var = tk.StringVar()
    objeto_var = tk.StringVar()
    codigo_var = tk.StringVar()
    marca_var = tk.StringVar()
    modelo_var = tk.StringVar()
    serie_var = tk.StringVar()
    observaciones_var = tk.StringVar()

    # ---------- LABELS + ENTRYS ----------
    Label(labelframe, text="Cantidad:", font=("Sans", 14, "bold"), bg="#C6D9E3").place(x=10, y=20)
    entry_cantidad = ttk.Entry(labelframe, font=("Sans", 14), textvariable=cantidad_var)
    entry_cantidad.place(x=170, y=20, width=260, height=30)

    Label(labelframe, text="Objeto:", font=("Sans", 14, "bold"), bg="#C6D9E3").place(x=10, y=60)
    entry_objeto = ttk.Entry(labelframe, font=("Sans", 14), textvariable=objeto_var)
    entry_objeto.place(x=170, y=60, width=260, height=30)

    Label(labelframe, text="Código:", font=("Sans", 14, "bold"), bg="#C6D9E3").place(x=10, y=100)
    entry_codigo = ttk.Entry(labelframe, font=("Sans", 14), textvariable=codigo_var)
    entry_codigo.place(x=170, y=100, width=260, height=30)

    Label(labelframe, text="Marca:", font=("Sans", 14, "bold"), bg="#C6D9E3").place(x=10, y=140)
    entry_marca = ttk.Entry(labelframe, font=("Sans", 14), textvariable=marca_var)
    entry_marca.place(x=170, y=140, width=260, height=30)

    Label(labelframe, text="Modelo:", font=("Sans", 14, "bold"), bg="#C6D9E3").place(x=10, y=180)
    entry_modelo = ttk.Entry(labelframe, font=("Sans", 14), textvariable=modelo_var)
    entry_modelo.place(x=170, y=180, width=260, height=30)

    Label(labelframe, text="Serie:", font=("Sans", 14, "bold"), bg="#C6D9E3").place(x=10, y=220)
    entry_serie = ttk.Entry(labelframe, font=("Sans", 14), textvariable=serie_var)
    entry_serie.place(x=170, y=220, width=260, height=30)

    Label(labelframe, text="Observaciones:", font=("Sans", 14, "bold"), bg="#C6D9E3").place(x=10, y=260)
    entry_obs = ttk.Entry(labelframe, font=("Sans", 14), textvariable=observaciones_var)
    entry_obs.place(x=170, y=260, width=260, height=30)

    # ---------- COMBOBOX LUGAR ----------
    Label(labelframe, text="Lugar:", font=("Sans", 14, "bold"), bg="#C6D9E3").place(x=10, y=300)
    combo_lugar = ttk.Combobox(labelframe, font=("Sans", 14), state="readonly")
    combo_lugar.place(x=170, y=300, width=260, height=30)

    lugares = obtener_lugares()
    combo_lugar["values"] = lugares

    # Seleccionar automáticamente el salón que se pidió
    nombre_salon = nombre_salon.strip()
    lugares_norm = [l.strip() for l in lugares]

    if nombre_salon in lugares_norm:
        combo_lugar.set(nombre_salon)
    elif lugares:
        combo_lugar.current(0)

    # ---------- TABLA (TREEVIEW) ----------
    treFrame = tk.Frame(frame, bg="white")
    treFrame.place(x=480, y=10, width=810, height=570)

    scrol_y = ttk.Scrollbar(treFrame, orient="vertical")
    scrol_y.pack(side=tk.RIGHT, fill=tk.Y)

    tree = ttk.Treeview(
        treFrame,
        yscrollcommand=scrol_y.set,
        columns=("ID", "Cantidad", "Objeto", "Código",
                 "Marca", "Modelo", "Serie", "Observaciones"),
        show="headings",
        height=40,
    )
    tree.pack(expand=True, fill=tk.BOTH)
    scrol_y.config(command=tree.yview)

    # Encabezados
    tree.heading("ID", text="ID")
    tree.heading("Cantidad", text="Cantidad")
    tree.heading("Objeto", text="Objeto")
    tree.heading("Código", text="Código")
    tree.heading("Marca", text="Marca")
    tree.heading("Modelo", text="Modelo")
    tree.heading("Serie", text="Serie")
    tree.heading("Observaciones", text="Observaciones")

    # Columnas
    tree.column("ID", width=40, anchor="center")
    tree.column("Cantidad", width=70, anchor="center")
    tree.column("Objeto", width=150, anchor="center")
    tree.column("Código", width=80, anchor="center")
    tree.column("Marca", width=90, anchor="center")
    tree.column("Modelo", width=90, anchor="center")
    tree.column("Serie", width=90, anchor="center")
    tree.column("Observaciones", width=180, anchor="center")

    # ---------- FUNCIONES DE LÓGICA ----------
    def cargar_tabla():
        # limpiar tabla
        for row in tree.get_children():
            tree.delete(row)

        nombre_lugar = combo_lugar.get()
        datos = obtener_inventario_por_lugar(nombre_lugar)
        # datos: (id, Cantidad, Objeto, Codigo, Marca, Modelo, Serie, Observaciones)
        for fila in datos:
            tree.insert("", tk.END, values=fila)

    def on_tree_select(event):
        selected = tree.selection()
        if not selected:
            return
        valores = tree.item(selected[0], "values")
        _id, cant, obj, cod, mar, mod, ser, obs = valores

        selected_id.set(_id)
        cantidad_var.set(cant)
        objeto_var.set(obj)
        codigo_var.set(cod)
        marca_var.set(mar)
        modelo_var.set(mod)
        serie_var.set(ser)
        observaciones_var.set(obs)

    tree.bind("<<TreeviewSelect>>", on_tree_select)

    # Cargar datos al iniciar y actualizar cuando cambie el lugar
    cargar_tabla()
    combo_lugar.bind("<<ComboboxSelected>>", lambda e: cargar_tabla())


    def limpiar_formulario():
        selected_id.set("")
        cantidad_var.set("")
        objeto_var.set("")
        codigo_var.set("")
        marca_var.set("")
        modelo_var.set("")
        serie_var.set("")
        observaciones_var.set("")

    def on_registrar():
        try:
            cantidad = int(cantidad_var.get() or "0")
        except ValueError:
            print("Cantidad inválida")
            return

        nombre_lugar = combo_lugar.get()
        ok = registrar_item(
            nombre_lugar,
            cantidad,
            objeto_var.get(),
            codigo_var.get() or None,
            marca_var.get() or "S/N",
            modelo_var.get() or "S/N",
            serie_var.get() or "S/N",
            observaciones_var.get() or "Sin observaciones",
        )
        if ok:
            cargar_tabla()
            limpiar_formulario()

    def on_modificar():
        if not selected_id.get():
            print("Selecciona un registro primero")
            return

        try:
            cantidad = int(cantidad_var.get() or "0")
        except ValueError:
            print("Cantidad inválida")
            return

        modificar_item(
            int(selected_id.get()),
            cantidad,
            objeto_var.get(),
            codigo_var.get() or None,
            marca_var.get() or "S/N",
            modelo_var.get() or "S/N",
            serie_var.get() or "S/N",
            observaciones_var.get() or "Sin observaciones",
        )
        cargar_tabla()
        limpiar_formulario()

    def on_eliminar():
        if not selected_id.get():
            print("Selecciona un registro primero")
            return
        eliminar_item(int(selected_id.get()))
        cargar_tabla()
        limpiar_formulario()

    # ---------- BOTONES ----------
    def cargar_imagen(ruta):
        try:
            img = Image.open(ruta)
            img = img.resize((40, 40))
            return ImageTk.PhotoImage(img)
        except:
            return None

    img_add = cargar_imagen("icono/ingresar.png")
    btn_add = Button(
        labelframe,
        text="Ingresar",
        font=("Roboto", 12, "bold"),
        compound="top",
        padx=10,
        command=on_registrar,
    )
    if img_add:
        btn_add.config(image=img_add)
        btn_add.image = img_add
    btn_add.place(x=40, y=380, width=100, height=90)

    img_edit = cargar_imagen("icono/modificar.png")
    btn_edit = Button(
        labelframe,
        text="Modificar",
        font=("Roboto", 12, "bold"),
        compound="top",
        padx=10,
        command=on_modificar,
    )
    if img_edit:
        btn_edit.config(image=img_edit)
        btn_edit.image = img_edit
    btn_edit.place(x=170, y=380, width=100, height=90)

    img_delete = cargar_imagen("icono/eliminar.png")
    btn_delete = Button(
        labelframe,
        text="Eliminar",
        font=("Roboto", 12, "bold"),
        compound="top",
        padx=10,
        command=on_eliminar,
    )
    if img_delete:
        btn_delete.config(image=img_delete)
        btn_delete.image = img_delete
    btn_delete.place(x=300, y=380, width=100, height=90)
