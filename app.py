from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pymysql
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

# Configuración de la base de datos usando PyMySQL
CONFIG_BD = {
    'host': 'beseuh7ma1cvxldur6ol-mysql.services.clever-cloud.com',
    'user': 'uyudmrvrkew3rngs',
    'password': 'u0BlOxO6jl1EObPkDyBT',
    'database': 'beseuh7ma1cvxldur6ol'
}

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Cambia aquí la contraseña
VALID_CREDENTIALS = {
    'Archivo': 'AZETA',
    'archivo': 'azeta',  # Puedes agregar más usuarios aquí
}

class User(UserMixin):
    def __init__(self, id, usuario):
        self.id = id
        self.usuario = usuario

@login_manager.user_loader
def load_user(user_id):
    return User(user_id, user_id) 

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']  # Cambiado de 'email' a 'usuario'
        password = request.form['password']
        
        # Verificar las credenciales
        if usuario in VALID_CREDENTIALS and password == VALID_CREDENTIALS[usuario]:  # Cambiado para verificar la contraseña
            login_user(User(usuario, usuario))
            return redirect(url_for('dashboard'))
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Función para obtener la última búsqueda
def get_last_search():
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM historial_busquedas ORDER BY fecha_busqueda DESC LIMIT 1')
            last_search = cursor.fetchone()
            return last_search  # Devuelve el registro completo
    finally:
        connection.close()

# Ruta para el dashboard
@app.route('/dashboard')
def dashboard():
    last_search = get_last_search()  # Llama a la función para obtener la última búsqueda
    return render_template('dashboard.html', last_search=last_search)

@app.route('/registro', methods=['GET', 'POST'])
@login_required
def registro():
    if request.method == 'POST':
        tipo = request.form['tipo']
        modulo = request.form['modulo']
        año = int(request.form['año'])
        ubicacion = request.form['ubicacion']
        
        if 'numero_individual' in request.form and request.form['numero_individual']:
            numero = int(request.form['numero_individual'])
            registrar_en_az(tipo, numero, modulo, año, ubicacion)
        else:
            desde = int(request.form['desde'])
            hasta = int(request.form['hasta'])
            for numero in range(desde, hasta + 1):
                registrar_en_az(tipo, numero, modulo, año, ubicacion)
        
        flash('Registro(s) creado(s) exitosamente')
        return redirect(url_for('registro'))
    
    tipos = obtener_tipos()
    return render_template('registro.html', tipos=tipos)

def registrar_en_az(tipo, numero, modulo, año, ubicacion):
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO AZ (tipo, numero, modulo, año, ubicacion) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (tipo, numero, modulo, año, ubicacion))
            connection.commit()
    finally:
        connection.close()

@app.route('/busqueda', methods=['GET', 'POST'])
@login_required
def busqueda():
    # Obtener listas para los selectores
    tipos = obtener_tipos()  # Usando la función que devuelve lista de strings en lugar de tuplas
    años = [año[0] for año in obtener_años()]  # Convertir tuplas a valores simples
    numeros = [num[0] for num in obtener_numeros()]  # Convertir tuplas a valores simples
    resultados = []
    
    if request.method == 'POST':
        tipo = request.form.get('tipo', '')
        numero = request.form.get('numero', '')  # Solo usar un campo para número
        año = request.form.get('año', '')
        
        # Solo realizar búsqueda si al menos un campo tiene valor
        if tipo or numero or año:
            resultados = buscar_en_az(tipo, numero, año)
            
            if resultados:
                flash(f'Se encontraron {len(resultados)} resultado(s)')
            else:
                flash('No se encontraron registros con los criterios especificados', 'warning')
        else:
            flash('Por favor, complete al menos un campo para realizar la búsqueda', 'warning')
    
    return render_template('busqueda.html', resultados=resultados, tipos=tipos, años=años, numeros=numeros)

def buscar_en_az(tipo=None, numero=None, año=None):
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = "SELECT * FROM AZ WHERE 1=1"
            params = []
            
            if tipo and tipo.strip():
                sql += " AND tipo = %s"
                params.append(tipo)
            if numero and str(numero).strip():
                sql += " AND numero = %s"
                try:
                    params.append(int(numero))
                except ValueError:
                    # Si no se puede convertir a entero, búsqueda por string
                    params.append(numero)
            if año and str(año).strip():
                sql += " AND año = %s"
                try:
                    params.append(int(año))
                except ValueError:
                    # Si no se puede convertir a entero, búsqueda por string
                    params.append(año)
            
            sql += " ORDER BY tipo, numero, año"
            
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        connection.close()

def obtener_numeros():
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT numero FROM AZ ORDER BY numero")
            return cursor.fetchall()
    finally:
        connection.close()

@app.route('/api/copiar-historial', methods=['POST'])
@login_required
def copiar_al_historial():
    data = request.get_json()
    tipo = data.get('tipo')
    numero = data.get('numero')
    año = data.get('año')
    modulo = data.get('modulo')
    ubicacion = data.get('ubicacion')

    # Verificar si el registro ya existe
    if verificar_historial(tipo, numero, año, modulo, ubicacion):
        return jsonify(success=False, error="Este documento ya está en el historial."), 400

    # Guardar en historial
    guardar_historial(tipo, numero, año, modulo, ubicacion)

    return jsonify({'success': True})

def verificar_historial(tipo, numero, año, modulo, ubicacion):
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM historial_busquedas WHERE tipo = %s AND numero = %s AND modulo = %s AND año = %s AND ubicacion = %s',
                           (tipo, numero, modulo, año, ubicacion))
            count = cursor.fetchone()[0]
            return count > 0
    finally:
        connection.close()

def guardar_historial(tipo, numero, año, modulo, ubicacion):
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO historial_busquedas (tipo, numero, año, modulo, ubicacion, fecha_busqueda, en_uso) VALUES (%s, %s, %s, %s, %s, NOW(), %s)"
            cursor.execute(sql, (tipo, numero, año, modulo, ubicacion, 'No en Uso'))
            connection.commit()
    finally:
        connection.close()

# Función modificada para devolver lista de strings en lugar de tuplas
def obtener_tipos():
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT tipo FROM AZ ORDER BY tipo")
            return [row[0] for row in cursor.fetchall()]  # Convertir tuplas a valores simples
    finally:
        connection.close()

def obtener_años():
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT año FROM AZ ORDER BY año DESC")
            return cursor.fetchall()
    finally:
        connection.close()

@app.route('/historial')
@login_required
def historial():
    records = obtener_historial()
    return render_template('historial.html', records=records)

def obtener_historial():
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, tipo, numero, modulo, año, ubicacion, fecha_busqueda, en_uso FROM historial_busquedas ORDER BY fecha_busqueda DESC")
            return cursor.fetchall()
    finally:
        connection.close()

@app.route('/historial/limpiar', methods=['POST'])
@login_required
def limpiar_historial():
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM historial_busquedas")
            connection.commit()
    except pymysql.MySQLError as e:
        flash('Error al limpiar el historial', 'error')
    finally:
        connection.close()
    return redirect(url_for('historial'))

@app.route('/api/cambiar-estado/<int:history_id>', methods=['POST'])
@login_required
def cambiar_estado(history_id):
    connection = pymysql.connect(**CONFIG_BD)
    try:
        data = request.get_json()
        accion = data.get('accion', 'toggle')  # Default is toggle between states
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM historial_busquedas WHERE id = %s", (history_id,))
            history = cursor.fetchone()
            
            if not history:  # Check if history exists
                return jsonify({'success': False, 'error': 'No encontrado'}), 404
                
            if accion == 'marcar_en_uso':
                nuevo_estado = 'En Uso'
            elif accion == 'eliminar_de_uso':
                nuevo_estado = 'No en Uso'
            else:  # toggle (previous behavior)
                nuevo_estado = 'En Uso' if history['en_uso'] == 'No en Uso' else 'No en Uso'
            
            # Update the record
            cursor.execute("UPDATE historial_busquedas SET en_uso = %s, fecha_busqueda = NOW() WHERE id = %s", 
                          (nuevo_estado, history_id))
            connection.commit()
            
            return jsonify({'success': True, 'nuevo_estado': nuevo_estado})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/cambiar_ubicacion')
@login_required
def cambiar_ubicacion():
    tipos = obtener_tipos()
    modulos = obtener_modulos()
    años = [año[0] for año in obtener_años()]  # Convertir tuplas a valores simples
    return render_template('cambiar_ubicacion.html', tipos=tipos, modulos=modulos, años=años)

@app.route('/cambiar_ubicacion_az', methods=['POST'])
@login_required
def cambiar_ubicacion_az():
    tipo = request.form['tipo']
    modulo = request.form['modulo']
    ubicacion = request.form['ubicacion']
    año = request.form['año']
    
    # Verificar si existen registros del tipo y año especificados
    if not verificar_registros_az_existen(tipo, año):
        # Devolver respuesta JSON en lugar de redireccionar
        return jsonify({
            'success': False,
            'message': 'No se encontraron registros AZ con los criterios especificados'
        })
    
    # Actualizar todos los registros de ese tipo y año
    filas_afectadas = actualizar_registros_az(tipo, año, modulo, ubicacion)
    
    # Devolver respuesta JSON en lugar de redireccionar y flash
    return jsonify({
        'success': True,
        'message': f'Se actualizaron {filas_afectadas} registros AZ de tipo {tipo} y año {año}'
    })

@app.route('/cambiar_ubicacion_documento', methods=['POST'])
@login_required
def cambiar_ubicacion_documento():
    tipo = request.form['tipo']
    modulo = request.form['modulo']
    ubicacion = request.form['ubicacion']
    año = request.form['año']
    
    # Verificar si se está procesando un número individual o un rango
    if 'numero' in request.form and request.form['numero'].strip():
        # Procesar un número individual
        numero = request.form['numero']
        
        # Verificar si el documento específico existe
        if not verificar_registro_existe(tipo, numero, año):
            # Devolver respuesta JSON en lugar de redireccionar
            return jsonify({
                'success': False,
                'message': 'No se encontró el documento a actualizar'
            })
        
        # Actualizar el documento específico
        actualizar_registro(numero, tipo, modulo, año, ubicacion)
        return jsonify({
            'success': True,
            'message': f'Documento {tipo} {numero} del año {año} actualizado exitosamente'
        })
    
    elif 'desde' in request.form and 'hasta' in request.form and request.form['desde'].strip() and request.form['hasta'].strip():
        # Procesar un rango de números
        desde = int(request.form['desde'])
        hasta = int(request.form['hasta'])
        
        filas_afectadas = 0
        for numero in range(desde, hasta + 1):
            # Verificar si cada documento específico existe antes de actualizarlo
            if verificar_registro_existe(tipo, numero, año):
                actualizar_registro(numero, tipo, modulo, año, ubicacion)
                filas_afectadas += 1
        
        if filas_afectadas > 0:
            return jsonify({
                'success': True,
                'message': f'Se actualizaron {filas_afectadas} documentos {tipo} del rango {desde}-{hasta} del año {año}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No se encontraron documentos en el rango especificado'
            })
    
    else:
        return jsonify({
            'success': False,
            'message': 'Por favor, proporcione un número de documento o un rango válido'
        })

def verificar_registros_az_existen(tipo, año):
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM AZ WHERE tipo = %s AND año = %s',
                          (tipo, año))
            count = cursor.fetchone()[0]
            return count > 0
    finally:
        connection.close()

def actualizar_registros_az(tipo, año, modulo, ubicacion):
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor() as cursor:
            # Actualizar la tabla AZ para todos los registros del tipo y año especificados
            sql_az = "UPDATE AZ SET modulo=%s, ubicacion=%s WHERE tipo=%s AND año=%s"
            cursor.execute(sql_az, (modulo, ubicacion, tipo, año))

            # Actualizar la tabla historial_busquedas si existen registros
            sql_historial = "UPDATE historial_busquedas SET modulo=%s, ubicacion=%s WHERE tipo=%s AND año=%s"
            cursor.execute(sql_historial, (modulo, ubicacion, tipo, año))

            connection.commit()
            return cursor.rowcount  # Retorna el número de filas afectadas
    finally:
        connection.close()

def verificar_registro_existe(tipo, numero, año):
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM AZ WHERE tipo = %s AND numero = %s AND año = %s',
                          (tipo, numero, año))
            count = cursor.fetchone()[0]
            return count > 0
    finally:
        connection.close()

def actualizar_registro(numero, tipo, modulo, año, ubicacion):
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor() as cursor:
            # Actualizar la tabla AZ
            sql_az = "UPDATE AZ SET modulo=%s, ubicacion=%s WHERE tipo=%s AND año=%s AND numero=%s"
            cursor.execute(sql_az, (modulo, ubicacion, tipo, año, numero))

            # Actualizar la tabla historial_busquedas si existe el registro
            sql_historial = "UPDATE historial_busquedas SET modulo=%s, ubicacion=%s WHERE tipo=%s AND año=%s AND numero=%s"
            cursor.execute(sql_historial, (modulo, ubicacion, tipo, año, numero))

            connection.commit()
    finally:
        connection.close()

# Definición faltante de obtener_modulos()
def obtener_modulos():
    connection = pymysql.connect(**CONFIG_BD)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT modulo FROM AZ ORDER BY modulo")
            return [row[0] for row in cursor.fetchall()]
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(debug=True)