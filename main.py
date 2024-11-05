from flet import *
import flet
import mysql.connector
import threading

# Conexión a la base de datos de productos
conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    db="appFletProduct"
)

cursor = conexion.cursor()  # Cursor para ejecutar consultas SQL

# Variables de paginación
page_number = 1  # Página actual
items_per_page = 5  # Productos por página

# Función principal de la aplicación
def main(page: Page):
    global page_number  # Se usa para la paginación

    # Configuración inicial de la página
    page.bgcolor = "#808080"  # Color de fondo de la página
    page.padding = 20  # Espaciado en los bordes de la página
    page.title = "Gestión de Productos"  # Título de la aplicación
    page.theme_mode = ThemeMode.LIGHT  # Tema claro

    # Label para mostrar mensajes de validación al usuario
    mensaje_lbl = Text("", size=14, color="green")

    # Campos de entrada para los datos del producto
    nombre_txt = TextField(label="Nombre", width=150)
    descripcion_txt = TextField(label="Descripción", multiline=True, max_lines=2, width=150)
    precio_txt = TextField(label="Precio", keyboard_type="number", width=150)
    cantidad_txt = TextField(label="Cantidad", keyboard_type="number", width=150)

    # Campos de entrada para editar productos
    edit_nombre_txt = TextField(label="Nombre", width=150)
    edit_descripcion_txt = TextField(label="Descripción", multiline=True, max_lines=2, width=150)
    edit_precio_txt = TextField(label="Precio", keyboard_type="number", width=150)
    edit_cantidad_txt = TextField(label="Cantidad", keyboard_type="number", width=150)
    edit_id = Text()  # ID del producto a editar

    # Tabla que mostrará los productos
    datos = DataTable(
        columns=[
            DataColumn(Text("ID")),
            DataColumn(Text("Nombre")),
            DataColumn(Text("Descripción")),
            DataColumn(Text("Precio")),
            DataColumn(Text("Cantidad")),
            DataColumn(Text("Acción"))  # Columna para botones de acción (editar/eliminar)
        ],
        rows=[]
    )

    # Control de paginación
    pagination = Row()  # Fila que contendrá los botones de paginación

    # Función para cargar datos de productos desde la base de datos
    def cargar_datos():
        global page_number

        # Consultar el total de productos en la base de datos
        cursor.execute("SELECT COUNT(*) FROM productos")
        total_items = cursor.fetchone()[0]
        total_pages = (total_items + items_per_page - 1) // items_per_page  # Calcular número de páginas

        # Obtener productos para la página actual
        offset = (page_number - 1) * items_per_page
        cursor.execute(f"SELECT * FROM productos LIMIT {offset}, {items_per_page}")
        resultado = cursor.fetchall()
        columns = [column[0] for column in cursor.description]  # Nombres de columnas
        rows = [dict(zip(columns, row)) for row in resultado]  # Convertir en diccionarios para acceso fácil

        # Limpiar filas anteriores de la tabla
        datos.rows.clear()

        # Agregar filas a la tabla para cada producto
        for row in rows:
            datos.rows.append(
                DataRow(
                    cells=[
                        DataCell(Text(row['idproducto'])),
                        DataCell(Text(row['prod_nombre'])),
                        DataCell(Text(row['prod_descripcion'])),
                        DataCell(Text(row['prod_precio'])),
                        DataCell(Text(row['prod_cantidad'])),
                        DataCell(
                            Row([
                                IconButton("delete", icon_color="red", data=row, on_click=btn_eliminar),
                                IconButton("edit", icon_color="red", data=row, on_click=lambda e: abrir_dialogo_editar(e))
                            ])
                        )
                    ]
                )
            )

        # Actualizar el control de paginación
        update_pagination(total_pages)

        page.update()  # Actualizar la interfaz de usuario

    # Función para actualizar los botones de paginación
    def update_pagination(total_pages):
        pagination.controls.clear()
        # Botón de retroceso de página
        if page_number > 1:
            pagination.controls.append(
                IconButton("chevron_left", on_click=lambda e: change_page(page_number - 1))
            )
        # Botones para cada número de página
        for i in range(1, total_pages + 1):
            pagination.controls.append(
                TextButton(str(i), on_click=lambda e, page=i: change_page(page), width=50)
            )
        # Botón de avance de página
        if page_number < total_pages:
            pagination.controls.append(
                IconButton("chevron_right", on_click=lambda e: change_page(page_number + 1))
            )
        page.update()

    # Función para cambiar la página actual y recargar los datos
    def change_page(new_page):
        global page_number
        page_number = new_page
        cargar_datos()

    # Mostrar un mensaje temporal en el label de mensajes
    def mostrar_mensaje(mensaje, color="green"):
        mensaje_lbl.value = mensaje
        mensaje_lbl.color = color
        page.update()
        threading.Timer(3, lambda: limpiar_mensaje()).start()  # Borrar mensaje después de 3 segundos

    # Función para limpiar el mensaje
    def limpiar_mensaje():
        mensaje_lbl.value = ""
        page.update()

    # Función para eliminar un producto
    def btn_eliminar(e):
        try:
            sql = "DELETE FROM productos WHERE idproducto = %s"
            val = (e.control.data['idproducto'],)
            cursor.execute(sql, val)
            conexion.commit()
            cargar_datos()  # Recargar datos después de eliminar
            mostrar_mensaje("Producto eliminado correctamente.", "red")
        except Exception as e:
            mostrar_mensaje("Error al eliminar el producto.", "red")

    # Función para guardar los cambios al editar un producto
    def guardar_editado(e):
        # Validaciones de entrada
        if not edit_nombre_txt.value:
            mostrar_mensaje("El nombre del producto no puede estar vacío.", "red")
            return
        if not edit_descripcion_txt.value:
            mostrar_mensaje("La descripción no puede estar vacía.", "red")
            return
        try:
            precio = float(edit_precio_txt.value)
            if precio <= 0:
                mostrar_mensaje("El precio debe ser un número positivo.", "red")
                return
        except ValueError:
            mostrar_mensaje("El precio debe ser un número válido.", "red")
            return
        try:
            cantidad = int(edit_cantidad_txt.value)
            if cantidad < 0:
                mostrar_mensaje("La cantidad debe ser un número entero positivo.", "red")
                return
        except ValueError:
            mostrar_mensaje("La cantidad debe ser un número entero válido.", "red")
            return

        # Actualización en la base de datos
        try:
            sql = "UPDATE productos SET prod_nombre=%s, prod_descripcion=%s, prod_precio=%s, prod_cantidad=%s WHERE idproducto=%s"
            val = (edit_nombre_txt.value, edit_descripcion_txt.value, edit_precio_txt.value, edit_cantidad_txt.value, edit_id.value)
            cursor.execute(sql, val)
            conexion.commit()
            cargar_datos()  # Recargar datos para actualizar la tabla
            alerta.open = False  # Cerrar el diálogo de edición
            mostrar_mensaje("Producto actualizado correctamente.")
        except Exception as e:
            mostrar_mensaje("Error al actualizar el producto.", "red")

    # Diálogo de edición de producto
    alerta = AlertDialog(
        title=Text("Editar Producto"),
        content=Column([
            edit_nombre_txt,
            edit_descripcion_txt,
            edit_precio_txt,
            edit_cantidad_txt
        ]),
        actions=[TextButton("Guardar", on_click=guardar_editado)]
    )

    # Función para abrir el diálogo de edición
    def abrir_dialogo_editar(e):
        # Rellenar campos con datos del producto a editar
        edit_nombre_txt.value = e.control.data['prod_nombre']
        edit_descripcion_txt.value = e.control.data['prod_descripcion']
        edit_precio_txt.value = str(e.control.data['prod_precio'])
        edit_cantidad_txt.value = str(e.control.data['prod_cantidad'])
        edit_id.value = e.control.data['idproducto']
        page.dialog = alerta  # Asignar diálogo a la página
        alerta.open = True
        page.update()

    # Función para registrar un nuevo producto
    def registrar_producto(e):
        # Validaciones de entrada
        if not nombre_txt.value:
            mostrar_mensaje("El nombre del producto no puede estar vacío.", "red")
            return
        if not descripcion_txt.value:
            mostrar_mensaje("La descripción no puede estar vacía.", "red")
            return
        try:
            precio = float(precio_txt.value)
            if precio <= 0:
                mostrar_mensaje("El precio debe ser un número positivo.", "red")
                return
        except ValueError:
            mostrar_mensaje("El precio debe ser un número válido.", "red")
            return
        try:
            cantidad = int(cantidad_txt.value)
            if cantidad < 0:
                mostrar_mensaje("La cantidad debe ser un número entero positivo.", "red")
                return
        except ValueError:
            mostrar_mensaje("La cantidad debe ser un número entero válido.", "red")
            return

        # Registro del nuevo producto en la base de datos
        try:
            sql = "INSERT INTO productos (prod_nombre, prod_descripcion, prod_precio, prod_cantidad) VALUES (%s, %s, %s, %s)"
            val = (nombre_txt.value, descripcion_txt.value, precio_txt.value, cantidad_txt.value)
            cursor.execute(sql, val)
            conexion.commit()
            cargar_datos()  # Recargar datos después de agregar
            mostrar_mensaje("Producto agregado correctamente.")
            nombre_txt.value = descripcion_txt.value = precio_txt.value = cantidad_txt.value = ""  # Limpiar los campos
            page.update()
        except Exception as e:
            mostrar_mensaje("Error al agregar el producto.", "red")

    # Cargar datos al iniciar la aplicación
    cargar_datos()

    # Diseño de la página, agregando los controles en columnas y filas
    page.add(
        Column([
            Text("Registro de Productos BRUNO YAMPEY", size=24, weight="bold", color="RED"),
            mensaje_lbl,
            Row([nombre_txt, descripcion_txt, precio_txt, cantidad_txt, ElevatedButton("Agregar", on_click=registrar_producto, bgcolor="red", color="white")]),
            datos,
            pagination  # Añadir la fila de paginación aquí
        ])
    )

flet.app(target=main)