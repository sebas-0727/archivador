import tkinter as tk
from tkinter import messagebox, ttk
import pymysql
import datetime

# Cambia estos valores para establecer el usuario y la contraseña
USUARIO_CORRECTO = "Archivo"
CONTRASENA_CORRECTA = "azeta"

class AplicacionArchivador:
    def __init__(self, master):
        self.master = master
        master.title("Archivador")
        master.geometry("1200x800")
        master.configure(bg="#f0f0f0")
        self.configurar_estilos()

        # Marco principal
        self.marco_principal = tk.Frame(master, bg="#f0f0f0")
        self.marco_principal.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # Mostrar el formulario de inicio de sesión
        self.mostrar_formulario_login()

        self.CONFIG_BD = {'host':'Archivo.mysql.pythonanywhere-services.com', 'user':'Archivo', 'password':'Archivo@fondrummond.com', 'database':'Archivo$Archivo'}
        self.registros_info = []
        self.registros_historial = []

    def configurar_estilos(self):
        estilo = ttk.Style()
        estilo.theme_use('clam')
        estilo.configure("TLabel", background="#f0f0f0", font=("Arial", 12))
        estilo.configure("TButton", font=("Arial", 12))
        estilo.configure("TEntry", font=("Arial", 12))

    def mostrar_formulario_login(self):
        ttk.Label(self.marco_principal, text="Inicio de Sesión", font=("Arial", 16)).pack(pady=20)

        marco_login = tk.Frame(self.marco_principal, bg="#f0f0f0")
        marco_login.pack(pady=10)

        ttk.Label(marco_login, text="Usuario:", style="TLabel").grid(row=0, column=0, padx=10, pady=5)
        self.entry_usuario = ttk.Entry(marco_login)
        self.entry_usuario.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(marco_login, text="Contraseña:", style="TLabel").grid(row=1, column=0, padx=10, pady=5)
        self.entry_contrasena = ttk.Entry(marco_login, show="*")
        self.entry_contrasena.grid(row=1, column=1, padx=10, pady=5)

        tk.Button(marco_login, text="Iniciar Sesión", command=self.validar_login, bg="#4CAF50", fg="white").grid(row=2, columnspan=2, pady=10)

    def validar_login(self):
        usuario = self.entry_usuario.get()
        contrasena = self.entry_contrasena.get()

        if usuario == USUARIO_CORRECTO and contrasena == CONTRASENA_CORRECTA:
            self.mostrar_menu_principal()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")

    def mostrar_menu_principal(self):
        # Limpiar el marco principal
        for widget in self.marco_principal.winfo_children():
            widget.destroy()

        ttk.Label(self.marco_principal, text="Seleccione una opción:", font=("Arial", 16)).pack(pady=20)

        # Crear marco de navegación en la parte superior
        self.marco_nav = tk.Frame(self.marco_principal, bg="#f0f0f0")
        self.marco_nav.pack(fill=tk.X, pady=10)

        # Crear botones de navegación
        for texto, comando, color in [("Registro", self.mostrar_formulario_registro, "#4CAF50"),
                                       ("Búsqueda", self.mostrar_formulario_busqueda, "#2196F3"),
                                       ("Historial", self.mostrar_historial, "#FF9800")]:
            tk.Button(self.marco_nav, text=texto, command=comando, bg=color, fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)

        # Botón de cerrar sesión
        tk.Button(self.marco_nav, text="Cerrar Sesión", command=self.cerrar_sesion, bg="#f44336", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)

        # Marco de contenido
        self.marco_contenido = tk.Frame(self.marco_principal, bg="#ffffff", borderwidth=2, relief=tk.RIDGE)
        self.marco_contenido.pack(fill=tk.BOTH, expand=True, pady=10)

    def cerrar_sesion(self):
        # Limpiar el marco principal y volver a mostrar el formulario de inicio de sesión
        for widget in self.marco_principal.winfo_children():
            widget.destroy()
        self.mostrar_formulario_login()

    def mostrar_formulario_registro(self):
        self.limpiar_contenido()
        self.crear_formulario("Formulario de Registro", ["Tipo", "Número", "Módulo", "Año", "Ubicación"], self.registrar)

    def crear_formulario(self, titulo, campos, comando_envio):
        ttk.Label(self.marco_contenido, text=titulo, style="TLabel").pack(pady=10)

        marco_formulario = tk.Frame(self.marco_contenido, bg="#ffffff")
        marco_formulario.pack(pady=10)

        entradas = {}
        for campo in campos:
            marco = tk.Frame(marco_formulario, bg="#ffffff")
            marco.pack(fill=tk.X, padx=50, pady=5)
            ttk.Label(marco, text=f"{campo}:", style="TLabel").pack(side=tk.LEFT, padx=10)
            entrada = ttk.Entry(marco, width=40)
            entrada.pack(side=tk.RIGHT, padx=10)
            entradas[campo] = entrada

            # Vincular la tecla Enter para pasar al siguiente campo
            entrada.bind("<Return>", lambda event, next_entry=entrada: self.focus_next_field(next_entry))

        tk.Button(marco_formulario, text="Registrar", command=lambda: comando_envio(entradas), bg="#4CAF50", fg="white", font=("Arial", 12)).pack(pady=20)

    def focus_next_field(self, current_entry):
        # Mover el foco al siguiente campo
        next_widget = current_entry.tk_focusNext()
        if next_widget:
            next_widget.focus()

    def registrar(self, entradas):
        valores = [entradas[campo].get() for campo in entradas]
        if any(not valor for valor in valores):
            messagebox.showerror("Error", "Por favor, complete todos los campos.")
            return
        try:
            with self.conectar_bd() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO AZ (tipo, numero, modulo, año, ubicacion) VALUES (%s, %s, %s, %s, %s)", valores)
                    conn.commit()
                    messagebox.showinfo("Registro", "Registro exitoso")
                    for entrada in entradas.values():
                        entrada.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar: {e}")

    def mostrar_formulario_busqueda(self):
        self.limpiar_contenido()
        ttk.Label(self.marco_contenido, text="Formulario de Búsqueda", style="TLabel").pack(pady=10)
        marco_busqueda = tk.Frame(self.marco_contenido, bg="#ffffff")
        marco_busqueda.pack(fill=tk.X, padx=50, pady=10)

        # Campos de búsqueda: Tipo, Número y Año
        ttk.Label(marco_busqueda, text="Tipo:", style="TLabel").pack(side=tk.LEFT, padx=10)
        self.combobox_tipo = ttk.Combobox(marco_busqueda, width=10)
        self.combobox_tipo.pack(side=tk.LEFT, padx=10)

        ttk.Label(marco_busqueda, text="Número:", style="TLabel").pack(side=tk.LEFT, padx=10)
        self.combobox_numero = ttk.Combobox(marco_busqueda, width=10)
        self.combobox_numero.pack(side=tk.LEFT, padx=10)

        ttk.Label(marco_busqueda, text="Año:", style="TLabel").pack(side=tk.LEFT, padx=10)
        self.combobox_año = ttk.Combobox(marco_busqueda, width=10)
        self.combobox_año.pack(side=tk.LEFT, padx=10)

        tk.Button(marco_busqueda, text="Buscar", command=self.buscar_info, bg="#2196F3", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
        tk.Button(marco_busqueda, text="Limpiar Filtros", command=self.limpiar_filtros, bg="#f44336", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)

        # Crear un canvas y scrollbar para los resultados
        self.canvas_busqueda = tk.Canvas(self.marco_contenido, bg="#ffffff")
        self.scroll_busqueda = tk.Scrollbar(self.marco_contenido, orient="vertical", command=self.canvas_busqueda.yview)
        self.scroll_busqueda.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_busqueda.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.canvas_busqueda.configure(yscrollcommand=self.scroll_busqueda.set)

        self.marco_resultados = tk.Frame(self.canvas_busqueda, bg="#ffffff")
        self.canvas_busqueda.create_window((0, 0), window=self.marco_resultados, anchor="nw")

        self.marco_resultados.bind("<Configure>", lambda e: self.canvas_busqueda.configure(scrollregion=self.canvas_busqueda.bbox("all")))

        # Vincular el evento de desplazamiento del mouse solo al canvas de búsqueda
        self.canvas_busqueda.bind("<MouseWheel>", self.scroll_canvas)

        # Cargar los números al mostrar el formulario de búsqueda
        self.cargar_numeros()
        self.cargar_tipos()
        self.cargar_años()

    def scroll_canvas(self, event):
        # Desplazar el canvas según la dirección del scroll
        self.canvas_busqueda.yview_scroll(int(-1*(event.delta/120)), "units")

    def cargar_tipos(self):
        try:
            with self.conectar_bd() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT DISTINCT tipo FROM AZ")
                    tipos = cursor.fetchall()
                    self.combobox_tipo['values'] = [tipo[0] for tipo in tipos]
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar tipos: {e}")

    def cargar_numeros(self):
        try:
            with self.conectar_bd() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT DISTINCT numero FROM AZ")
                    numeros = cursor.fetchall()
                    self.combobox_numero['values'] = [numero[0] for numero in numeros]
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar números: {e}")

    def cargar_años(self):
        try:
            with self.conectar_bd() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT DISTINCT año FROM AZ")
                    años = cursor.fetchall()
                    self.combobox_año['values'] = [año[0] for año in años]
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar años: {e}")

    def limpiar_filtros(self):
        self.combobox_tipo.set('')
        self.combobox_numero.set('')
        self.combobox_año.set('')
        self.limpiar_resultados()

    def limpiar_resultados(self):
        for widget in self.marco_resultados.winfo_children():
            widget.destroy()

    def buscar_info(self):
        tipo = self.combobox_tipo.get()
        numero = self.combobox_numero.get()
        año = self.combobox_año.get()
        self.limpiar_resultados()

        try:
            with self.conectar_bd() as conn:
                with conn.cursor() as cursor:
                    # Ajustar la consulta para buscar por tipo, número y año
                    sql = "SELECT tipo, numero, modulo, año, ubicacion FROM AZ WHERE tipo = %s AND numero = %s AND año = %s"
                    cursor.execute(sql, (tipo, numero, año))
                    self.registros_info = cursor.fetchall()
                    if not self.registros_info:
                        messagebox.showinfo("Resultado", "No se encontraron registros.")
                    else:
                        self.mostrar_resultados_busqueda()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar información: {e}")

    def mostrar_resultados_busqueda(self):
        self.limpiar_resultados()
        marco_tarjetas = tk.Frame(self.marco_resultados, bg="#ffffff")
        marco_tarjetas.pack(pady=10)

        for i, registro in enumerate(self.registros_info):
            marco_registro = tk.Frame(marco_tarjetas, bg="#ffffff", bd=2, relief=tk.RAISED)
            marco_registro.pack(pady=10, padx=20)  # Cambiar a pack para centrar en una columna

            campos = ["Tipo", "Número", "Módulo", "Año", "Ubicación"]
            for j, (campo, valor) in enumerate(zip(campos, registro)):
                tk.Label(marco_registro, text=f"{campo}:", bg="#ffffff", font=("Arial", 10, "bold")).grid(row=j, column=0, sticky="w", padx=5, pady=2)
                tk.Label(marco_registro, text=valor, bg="#ffffff", font=("Arial", 10)).grid(row=j, column=1, sticky="w", padx=5, pady=2)

            tk.Button(marco_registro, text="Seleccionar", command=lambda r=registro: self.seleccionar_registro(r),
                      bg="#2196F3", fg="white", font=("Arial", 10)).grid(row=len(campos), column=0, columnspan=2, pady=5)

        marco_tarjetas.update_idletasks()
        self.marco_resultados.update_idletasks()

    def seleccionar_registro(self, registro):
        tipo, numero, modulo, año, ubicacion = registro
        fecha_busqueda = datetime.datetime.now()
        self.registrar_busqueda(tipo, numero, modulo, año, fecha_busqueda)
        messagebox.showinfo("Selección", f"Has seleccionado el registro con tipo {tipo} y número {numero}")

    def registrar_busqueda(self, tipo, numero, modulo, año, fecha_busqueda):
        try:
            with self.conectar_bd() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id FROM historial_busquedas
                        WHERE tipo = %s AND numero = %s AND año = %s
                    """, (tipo, numero, año))
                    existente = cursor.fetchone()

                    if existente:
                        cursor.execute("""
                            UPDATE historial_busquedas
                            SET fecha_busqueda = %s
                            WHERE id = %s
                        """, (fecha_busqueda, existente[0]))
                    else:
                        cursor.execute("""
                            INSERT INTO historial_busquedas
                            (tipo, numero, modulo, año, fecha_busqueda, en_uso)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (tipo, numero, modulo, año, fecha_busqueda, "No en Uso"))

                    conn.commit()
                    print("Búsqueda registrada/actualizada exitosamente.")
        except Exception as e:
            print(f"Error al registrar búsqueda: {e}")

    def mostrar_historial(self):
        self.limpiar_contenido()
        ttk.Label(self.marco_contenido, text="Historial de Búsquedas", style="TLabel").pack(pady=10)

        marco_botones = tk.Frame(self.marco_contenido)
        marco_botones.pack(pady=10)

        # Botón de limpiar historial en la parte superior izquierda
        tk.Button(marco_botones, text="Limpiar Historial", command=self.limpiar_historial, bg="#f44336", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)

        # Crear un canvas y scrollbar para el historial
        self.canvas_historial = tk.Canvas(self.marco_contenido, bg="#ffffff")
        self.scroll_historial = tk.Scrollbar(self.marco_contenido, orient="vertical", command=self.canvas_historial.yview)
        self.scroll_historial.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_historial.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.canvas_historial.configure(yscrollcommand=self.scroll_historial.set)

        self.marco_historial = tk.Frame(self.canvas_historial, bg="#ffffff")
        self.canvas_historial.create_window((0, 0), window=self.marco_historial, anchor="nw")

        self.marco_historial.bind("<Configure>", lambda e: self.canvas_historial.configure(scrollregion=self.canvas_historial.bbox("all")))

        # Vincular el evento de desplazamiento del mouse solo al canvas de historial
        self.canvas_historial.bind("<MouseWheel>", self.scroll_canvas)

        self.cargar_historial()

    def scroll_canvas(self, event):
        # Desplazar el canvas según la dirección del scroll
        self.canvas_historial.yview_scroll(int(-1*(event.delta/120)), "units")

    def cargar_historial(self):
        try:
            with self.conectar_bd() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT DISTINCT
                            tipo,
                            numero,
                            modulo,
                            año,
                            fecha_busqueda,
                            en_uso
                        FROM
                            historial_busquedas
                        ORDER BY
                            fecha_busqueda DESC
                    """
                    cursor.execute(sql)
                    self.registros_historial = cursor.fetchall()
                    self.mostrar_registros_historial()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar historial: {e}")

    def mostrar_registros_historial(self):
        self.limpiar_resultados_historial()
        marco_tarjetas = tk.Frame(self.marco_historial, bg="#ffffff")
        marco_tarjetas.pack(pady=10)

        for i, registro in enumerate(self.registros_historial):
            marco_registro = tk.Frame(marco_tarjetas, bg="#ffffff", bd=2, relief=tk.RAISED)
            marco_registro.grid(row=i // 4, column=i % 4, padx=10, pady=10, sticky="nsew")

            campos = ["Uso", "Tipo", "Número", "Módulo", "Año", "Fecha Búsqueda"]
            valores = list(registro[:-1])
            valores.insert(0, registro[-1])  # Usar el valor de en_uso directamente

            for j, (campo, valor) in enumerate(zip(campos, valores)):
                tk.Label(marco_registro, text=f"{campo}:", bg="#ffffff", font=("Arial", 10, "bold")).grid(row=j, column=0, sticky="w", padx=5, pady=2)
                label_valor = tk.Label(marco_registro, text=valor, bg="#ffffff", font=("Arial", 10))
                label_valor.grid(row=j, column=1, sticky="w", padx=5, pady=2)
                if campo == "Uso":
                    label_valor.config(fg="green" if valor == "En Uso" else "black")

            tk.Button(marco_registro, text="Cambiar Estado", command=lambda r=registro, label=label_valor: self.cambiar_estado_registro(r, label),
                      bg="#FF9800", fg="white", font=("Arial", 10)).grid(row=len(campos), column=0, columnspan=2, pady=5)

        for col in range(4):
            marco_tarjetas.grid_columnconfigure(col , weight=1)

        marco_tarjetas.update_idletasks()
        self.marco_historial.update_idletasks()

    def cambiar_estado_registro(self, registro, label_valor):
        tipo, numero, _, año, _, en_uso = registro
        nuevo_estado = "En Uso" if en_uso == "No en Uso" else "No en Uso"
        fecha_cambio = datetime.datetime.now()

        try:
            with self.conectar_bd() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE historial_busquedas
                        SET en_uso = %s, fecha_busqueda = %s
                        WHERE tipo = %s AND numero = %s AND año = %s
                    """, (nuevo_estado, fecha_cambio, tipo, numero, año))
                    conn.commit()
                    messagebox.showinfo("Éxito", f"Estado cambiado a: {nuevo_estado}")
                    label_valor.config(text=nuevo_estado, fg="green" if nuevo_estado == "En Uso" else "black")
                    self.cargar_historial()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cambiar el estado: {e}")

    def limpiar_historial(self):
        if messagebox.askyesno("Confirmar", "¿Estás seguro de que deseas limpiar el historial?"):
            try:
                with self.conectar_bd() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM historial_busquedas")
                        conn.commit()
                        messagebox.showinfo("Éxito", "Historial limpiado exitosamente.")
                        self.mostrar_historial()
            except Exception as e:
                messagebox.showerror("Error", f"Error al limpiar el historial: {e}")

    def limpiar_resultados_historial(self):
        for widget in self.marco_historial.winfo_children():
            widget.destroy()

    def limpiar_contenido(self):
        for widget in self.marco_contenido.winfo_children():
            widget.destroy()

    def conectar_bd(self):
        return pymysql.connect(**self.CONFIG_BD)

def main():
    root = tk.Tk()
    app = AplicacionArchivador(root)
    root.mainloop()

if __name__ == "__main__":
    main()