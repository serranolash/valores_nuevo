from flask import Flask, render_template, request, jsonify, redirect, url_for, abort, send_file, session, flash, send_from_directory
import requests, time
import pandas as pd
from datetime import datetime, timedelta
import json
import traceback
from flask_cors import CORS
from io import BytesIO
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired
import os



app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Define un formulario de autenticación
class AuthenticationForm(FlaskForm):
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar')

# ...

# En tu ruta de autenticación
@app.route('/autenticar', methods=['GET', 'POST'])
def autenticar():
    form = AuthenticationForm()

    if form.validate_on_submit():
        # Aquí deberías verificar si la contraseña es correcta
        # Puedes usar una contraseña almacenada o comparar con una contraseña encriptada

        # En este ejemplo, la contraseña es 'mi_contraseña'
        if form.password.data == 'mi_contraseña':
            session['autenticado'] = True
            return redirect(url_for('formulario_actualizacion.html'))
        else:
            flash('Contraseña incorrecta. Inténtalo de nuevo.', 'error')

    return render_template('autenticacion.html', form=form)


#@app.route('/formulario_actualizacion')
def formulario_actualizacion():
    # Verifica si el usuario está autenticado
    if session.get('autenticado'):
        # Renderiza la plantilla de actualización de precios
        return render_template('formulario_actualizacion')
    else:
        # Si no está autenticado, redirige a la página de autenticación
        flash('Debes iniciar sesión para acceder a esta página.', 'error')
        return redirect(url_for('autenticar'))


API_URL_ARTICULO= 'http://190.220.155.74:8008/api.Dragonfish/Articulo/'
API_URL_VALOR = 'http://190.220.155.74:8008/api.Dragonfish/Valor/'
API_URL_CONSULTA = 'http://190.220.155.74:8008/api.Dragonfish/ConsultaStockYPrecios/'

headers = {
    'Authorization': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NDY5MDAwNTMsInVzdWFyaW8iOiJBRE1JTiIsInBhc3N3b3JkIjoiMWFmMjBlZjg2OTkyMjQzNTVlN2M1ZDcxNjBjYmUyMDM5MjBlZTgwZTVmODlkMWY2Mzk5NDVhNDY5YzQ5YWQyYSJ9.bQw_DdHDl3mThtPacAX24GS0YXcnAbEnB_2lR9N0HJU',
    'IdCliente': 'APIALEX',
    'Content-Type': 'application/json',
    'Accept': 'application/json',

}

# Lista de bases de datos disponibles
BASES_DE_DATOS = ['DEPOFORT', 'DEPOSEVN']


'''MODULO PARA REALIZAR LA CONSULTA DE PRECIOS '''

@app.route('/consulta_stock_precios', methods=['GET', 'POST'])
def consulta_stock_precios():
    try:
        if request.method == 'POST':
            codigo = request.form['query']
            base_de_datos = request.form['base_de_datos']

            # Verificar si la base de datos seleccionada es válida
            if base_de_datos not in BASES_DE_DATOS:
                return jsonify({"error": "Base de datos no válida"}), 400

            # Actualizar la base de datos en los encabezados
            headers['BaseDeDatos'] = base_de_datos

            # Construir los parámetros de la consulta
            params = {
                'query': codigo,
                'preciocero': 'true',
                'stockcero': 'true',
                'exacto': 'false',
                
            }

            # Realizar la solicitud GET a la API
            response = requests.get(API_URL_CONSULTA, params=params, headers=headers)
            print(response)
           

            # Verificar si la respuesta fue exitosa (código 200)
            if response.status_code == 200:
                # Intentar parsear la respuesta como JSON
                try:
                    response_json = response.json()
                except json.JSONDecodeError as json_error:
                    print("Error al parsear respuesta como JSON:", str(json_error))
                    return jsonify({"error": "Error al parsear respuesta como JSON"}), 500

                # Redirigir a la página de resultados con la información de la consulta
                return render_template('resultados.html', resultados=response_json)
            else:
                # En caso de respuesta no exitosa, abortar con el código de estado de la respuesta
                abort(response.status_code)

        # Si no es una solicitud POST, simplemente renderizar la página con el formulario
        return render_template('consulta_stock_precios.html', bases_de_datos=BASES_DE_DATOS)

    except Exception as e:
        print("Error durante la consulta GET:", str(e))
        print(traceback.format_exc())  # Imprime el traceback completo
        return jsonify({"error": str(e)}), 500
    
def convertir_fecha_api(api_fecha):
    milisegundos = int(api_fecha[6:-7])
    fecha = datetime.utcfromtimestamp(milisegundos / 1000)
    zona_horaria = timedelta(hours=-3)
    fecha_con_desplazamiento = fecha + zona_horaria
    return fecha_con_desplazamiento

@app.route('/mod', methods=['GET', 'POST'])
def mod():
    if request.method == 'POST':
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        base_de_datos = request.form['base_de_datos']

        # Lista para almacenar DataFrames individuales
        dfs = []

        # URL de la API
        url_api = 'http://190.220.155.74:8008/api.Dragonfish/Modificacionprecios/'

        # Headers con el token de autorización, la base de consulta y el IdCliente
        headers = {
            'Authorization': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NDY5MDAwNTMsInVzdWFyaW8iOiJBRE1JTiIsInBhc3N3b3JkIjoiMWFmMjBlZjg2OTkyMjQzNTVlN2M1ZDcxNjBjYmUyMDM5MjBlZTgwZTVmODlkMWY2Mzk5NDVhNDY5YzQ5YWQyYSJ9.bQw_DdHDl3mThtPacAX24GS0YXcnAbEnB_2lR9N0HJU',  # Tu token aquí
            'BaseDeDatos': base_de_datos,  # Tu base de consulta aquí
            'IdCliente': 'APIALEX',  # Agrega el IdCliente correspondiente
        }

        # Iterar sobre cada fecha en el rango
        fecha_actual = pd.to_datetime(fecha_inicio, format='%d-%m-%Y')
        fecha_fin = pd.to_datetime(fecha_fin, format='%d-%m-%Y')

        while fecha_actual <= fecha_fin:
            # Formatear la fecha actual
            fecha_actual_str = fecha_actual.strftime('%Y-%m-%d')

            # Parámetros de búsqueda
            params = {
                'limit': 100000,  # Cantidad de resultados a obtener
                'FechaVigencia': fecha_actual_str,
                'Fecha': fecha_actual_str,
            }

            # Realizar consulta a la API
            response = requests.get(url_api, headers=headers, params=params)

            # Verificar si la respuesta fue exitosa
            if response.status_code == 200:
                try:
                    # Intentar convertir la respuesta a JSON
                    resultados_json = response.json()

                    # Obtener la lista de resultados
                    resultados = resultados_json.get('Resultados', [])

                    # Verificar si hay resultados
                    if resultados:
                        # Agregar el número de modificación y la fecha al DataFrame
                        for resultado in resultados:
                            numero_modificacion = resultado.get('Numero', '')
                            fecha_modificacion_api = resultado.get('Fecha', '')

                            # Convertir la fecha de la API a un formato legible
                            fecha_modificacion = convertir_fecha_api(fecha_modificacion_api)

                            # Convertir cada elemento de la lista en un DataFrame de pandas
                            df_temp = pd.json_normalize(resultado['ModPrecios'])

                            # Agregar columnas de número y fecha
                            df_temp['NumeroModificacion'] = numero_modificacion
                            df_temp['FechaModificacion'] = fecha_modificacion

                            # Agregar el DataFrame a la lista
                            dfs.append(df_temp)
                except requests.exceptions.JSONDecodeError as e:
                    print(f"Error al decodificar JSON: {e} (Fecha: {fecha_actual_str})")
            else:
                print(f"Error en la consulta API. Código de estado: {response.status_code} (Fecha: {fecha_actual_str})")

            # Avanzar a la siguiente fecha
            fecha_actual += pd.DateOffset(days=1)

        # Concatenar los DataFrames en uno solo
        df_final = pd.concat(dfs, ignore_index=True)

        # Guardar en archivo Excel
        output = BytesIO()
        df_final.to_excel(output, index=False)
        output.seek(0)

        return send_file(output, as_attachment=True, download_name='resultados_mod.xlsx')

    return render_template('mod.html')    

'''MODULO PARA MOSTRAR LOS RESULTADOS DE LA CONSULTA DE PRECIOS'''

@app.route('/resultados', methods=['GET'])
def mostrar_resultados():
    try:
        # Obtén los argumentos de la URL
        resultados = request.args.get('resultados')
        status_code = request.args.get('status_code')      


        # Verificar si los argumentos están presentes
        if resultados is None or status_code is None:
            return jsonify({"error": "Argumentos faltantes"}), 400

        # Intentar cargar la cadena JSON
        try:
            resultados = json.loads(resultados)
        except json.JSONDecodeError as json_error:
            print("Error al parsear respuesta como JSON:", str(json_error))
            return jsonify({"error": "Error al parsear respuesta como JSON"}), 500

        # Aquí podrías hacer algo con los resultados si es necesario

        # Finalmente, renderizas la plantilla con los resultados
        resultados = request.args.get('resultados')
        status_code = request.args.get('status_code')

# Finalmente, renderizas la plantilla con los resultados
        return render_template('resultados.html', resultados=resultados, status_code=status_code)


    except Exception as e:
        print("Error durante la carga de resultados:", str(e))
        print(traceback.format_exc())  # Imprime el traceback completo
        return jsonify({"error": str(e)}), 500



def get_default_boolean_values():
    return {
        "VisualizarEnCaja": False,
        "PersonalizarComprobante": False,
        "ArrastraSaldo": False,
        "NoAplicarEnRecibos": False,
        "ArqueoPorTotales": False,
        "BloqueaModificacionDescripcion": False,
        "PermiteModificarFecha": False,
    }

@app.route('/realizar_post', methods=['POST'])
def realizar_post():
    try:
        # Obtener datos del formulario
        codigo = request.form.get('codigo')
        descripcion = request.form.get('descripcion')
        tipo = request.form.get('tipo')
        simbolo_monetario = request.form.get('simbolo_monetario')
        grupo = request.form.get('grupo')       
        operadora_tarjeta = request.form.get('operadora_tarjeta')
        tipo_tarjeta = request.form.get('tipo_tarjeta')
        base_de_datos = request.form.get('base_de_datos')

        # Agregar la información de la base de datos a los encabezados
        headers['BaseDeDatos'] = base_de_datos

        # Construir el cuerpo de la solicitud
        payload = {
            "Codigo": codigo,
            "Descripcion": descripcion,
            "Tipo": tipo,
            "SimboloMonetario": simbolo_monetario,
            "Grupo": grupo,
            "OperadoraTarjeta": operadora_tarjeta,
            "TipoTarjeta": tipo_tarjeta,
        }

        # Manejar los detalles de los planes
        detalles_planes = []

        # Iterar sobre los datos del formulario que corresponden a los detalles de los planes
        for i in range(1, 13):  # Considerando dos planes, ajusta según sea necesario
            
            cuotas_plan = request.form.get(f'cuotas_plan_{i}')            
            recargo_plan = request.form.get(f'recargo_plan_{i}')           

            # Construir el objeto para el detalle del plan
            detalle_plan = {
                "Cuotas": cuotas_plan,           
                
                "Recargo": recargo_plan,
                
            }

            # Agregar el detalle del plan a la lista
            detalles_planes.append(detalle_plan)

        # Agregar la lista de detalles de planes al payload
        payload["DetallePlanes"] = detalles_planes

        # Agregar valores booleanos fijos por defecto al payload
        payload.update(get_default_boolean_values())

        print("Credenciales:", headers)
        print("Parámetros:", payload)
       
        
        # Realizar la solicitud POST a la API
        print("Solicitud enviada:", request)
        
        response = requests.post(API_URL_VALOR, json=payload, headers=headers)
        
        # Manejar el BOM si está presente
        try:
            response.raise_for_status()  # Lanza una excepción para códigos de estado HTTP 4xx y 5xx
            response_json = response.json()
            print("Respuesta JSON:", response_json)
        except requests.exceptions.RequestException as req_exc:
            print(f"Error durante la solicitud POST: {req_exc}")
            return jsonify({"error": str(req_exc)}), 500
        except json.JSONDecodeError as json_exc:
            print(f"Error decoding JSON: {json_exc}")
            return jsonify({"error": str(json_exc)}), 500

        # Verificar el código de estado de la respuesta
        print("Código de estado de la respuesta:", response.status_code)

        # Manejar la respuesta no autorizada (401)
        if response.status_code == 401:
            return jsonify({"error": "Unauthorized. Verifica las credenciales."}), 401

        # Renderizar la plantilla con la respuesta de la API
        print("Entró en realizar_post")
        return render_template('valores.html', response=response_json, status_code=response.status_code)

    except Exception as e:
        print("Error durante la solicitud POST:", str(e))
        print(traceback.format_exc())  # Imprime el traceback completo
        return jsonify({"error": str(e)}), 500    
    
      
def obtener_datos_articulo(base_de_datos, codigo):
    try:
        headers['BaseDeDatos'] = base_de_datos
        response = requests.get(f"{API_URL_ARTICULO}/{codigo}", headers=headers)

        # Agrega impresiones para depurar
        print(f"Solicitando datos para el código: {codigo}")
        print(f"Headers: {headers}")
        print(f"Obtener Datos Artículo - Response: {response}")
        print(f"Obtener Datos Artículo - Response Text: {response.text}")

        if response.status_code == 200:
            # El código existe, devolver los datos del artículo
            data = json.loads(response.text)
            print(f"Datos del artículo: {data}")
            return data
        elif response.status_code == 404:
            # El código no existe, redirigir a la carga manual
            print(response.status_code)            
            return None
        else:
            # Manejar otros códigos de estado según sea necesario
            print(f"Error en la solicitud. Código de estado: {response.status_code}")
            print(f"Respuesta del servidor: {response.text}")
            return None

    except requests.exceptions.HTTPError as errh:
        print(f"Error HTTP: {errh}")        
        return f"Error HTTP: {errh}"
    except requests.exceptions.ConnectionError as errc:
        print(f"Error de conexión: {errc}")
        return f"Error de conexión: {errc}"
    except requests.exceptions.Timeout as errt:
        print(f"Error de tiempo de espera: {errt}")
        return f"Error de tiempo de espera: {errt}"
    except requests.exceptions.RequestException as err:
        print(f"Error de solicitud: {err}")
        return f"Error de solicitud: {err}"
    except Exception as e:
        print(f"Error inesperado: {e}")
        return f"Error inesperado: {e}"
    

def cargar_datos_manual(base_de_datos, datos, API_URL_ARTICULO):
    app.logger.info('Entró en la función cargar_datos_manual')
    print(app.logger)
    print(f"Base de Datos: {base_de_datos}")

    # Convertir los valores booleanos
    datos["NoPermiteDevoluciones"] = "no_permite_devoluciones" in request.form
    datos["RestringirDescuentos"] = "restringir_descuentos" in request.form
    datos["NoPublicarEnEcommerce"] = "NoPublicarEnEcommerce" in request.form
    datos["SoloPromoYKit"] = "solo_promo_y_kit" in request.form
    
    # Declarar la variable response con un valor predeterminado
    response = None

    # Filtrar campos que son None (no presentes en el formulario)
    datos = {key: value for key, value in datos.items() if value is not None}
    print(f"Cargar Datos Manual - Datos: {datos}")

    try:
        response = requests.post(API_URL_ARTICULO, json=datos, headers=headers)
        print(f"Cargar Datos Manual - Response: {response}")
        print(f"Cargar Datos Manual - Response Text: {response.text}")
        response.raise_for_status()  # Lanza una excepción para códigos de error HTTP

        json_data = json.loads(response.text.lstrip('\ufeff'))
        print(json_data)
        print(f"Cargar Datos Manual - JSON Data: {json_data}")

        if response.status_code == 201:
            return "CÓDIGO CREADO EXITOSAMENTE"
        else:
            return f"Error en la carga. Código de estado: {response.status_code}"

    except requests.exceptions.HTTPError as errh:
        print(f"Error HTTP: {errh}")
        flash('Por favor, complete todos los campos del formulario no sea pelotudo.')
        return f"Error HTTP: {errh}"
        
    except requests.exceptions.ConnectionError as errc:
        print(f"Error de conexión: {errc}")
        return f"Error de conexión: {errc}"
    except requests.exceptions.Timeout as errt:
        print(f"Error de tiempo de espera: {errt}")
        return f"Error de tiempo de espera: {errt}"
    except requests.exceptions.RequestException as err:
        print(f"Error de solicitud: {err}")
        return f"Error de solicitud: {err}"
    except Exception as e:
        print(f"Error inesperado: {e}")
        return f"Error inesperado: {e}"
   

'''MODULO PARA LA CARGA DE ARTICULOS'''

@app.route('/index', methods=['GET', 'POST'])
def index():
    app.logger.info('Entró en la función index')
    print(app.logger.info)
    print("Entró en la función index")

    if request.method == 'POST':
        base_de_datos = request.form['base_de_datos']
        codigo = request.form['codigo']

        if 'manual_submit' in request.form:
            # Verificar si el código ya existe
            datos_existentes = obtener_datos_articulo(base_de_datos, codigo)

            if datos_existentes:
                # El código existe, presentar opción PUT
                return render_template('modificar.html', datos_existentes=datos_existentes)
            else:
                # El código no existe, continuar con la carga manual
                datos_manual_articulo = {
                    "Codigo": request.form['codigo'],
                    "Descripcion": request.form['descripcion'],
                    "DescripcionAdicional": request.form['descripcion_adicional'],
                    "NoPermiteDevoluciones": request.form.get('no_permite_devoluciones', False),
                    "RestringirDescuentos": request.form.get('restringir_descuentos', False),
                    "NoPublicarEnEcommerce": request.form.get('noPublicar_EnEcommerce', False),
                    "SoloPromoYKit": request.form.get('solo_promo_y_kit', False),
                    "Proveedor": request.form['proveedor'],
                    "UnidadDeMedida": request.form['unidad_de_medida'],
                    "Temporada": request.form['temporada'],
                    "Ano": int(request.form['ano']) if request.form['ano'] else None,
                    "Familia": request.form['familia'],
                    "Material": request.form['material'],
                    "Linea": request.form['linea'],
                    "Grupo": request.form['grupo'],
                    "CategoriaDeArticulo": request.form['categoria'],
                    "Clasificacion": request.form['clasificacion'],
                    "TipodeArticulo": request.form['tipo'],
                    "Paletadecolores": request.form['paleta_colores']
                }

                # Agregar la URL de verificación como argumento
                mensaje_del_servidor = cargar_datos_manual(base_de_datos, datos_manual_articulo, API_URL_ARTICULO)
                print(f"Mensaje del servidor: {mensaje_del_servidor}")

                # Verificar si el mensaje indica éxito antes de redirigir
                if "CÓDIGO CREADO EXITOSAMENTE" in mensaje_del_servidor:
                    flash('CÓDIGO CREADO EXITOSAMENTE', 'success')
                    flash('Carga exitosa. Eres un vergatario.', 'success')
                    return redirect(url_for('index'))

                return render_template('index.html', mensaje_del_servidor=mensaje_del_servidor)

    # Añade una variable vacía para evitar errores en la plantilla
    return render_template('index.html', datos_existentes={})

                
def actualizar_datos_articulo(base_de_datos, codigo, nuevos_datos):
    headers['BaseDeDatos'] = base_de_datos
    response = requests.put(f"{API_URL_ARTICULO}/{codigo}", json=nuevos_datos, headers=headers)

    if response.status_code == 200:
        return "Datos del artículo actualizados con éxito."
    else:
        return f"Error en la actualización. Código de estado: {response.status_code}"


@app.route('/modificar', methods=['POST'])
def modificar_articulo():
    base_de_datos = request.form['base_de_datos']
    codigo = request.form['codigo']

    datos_modificados = {
        "Codigo": codigo,
        "Descripcion": request.form['descripcion'],
        "DescripcionAdicional": request.form['descripcion_adicional'],
        "NoPermiteDevoluciones": 'no_permite_devoluciones' in request.form,
        "RestringirDescuentos": 'restringir_descuentos' in request.form,
        "NoPublicarEnEcommerce": 'NoPublicarEnEcommerce' in request.form,
        "SoloPromoYKit": 'solo_promo_y_kit' in request.form,
        "Proveedor": request.form['proveedor'],
        "UnidadDeMedida": request.form['unidad_de_medida'],
        "Temporada": request.form['temporada'],
        "Ano": int(request.form['ano']),
        "Familia": request.form['familia'],
        "Material": request.form['material'],
        "Linea": request.form['linea'],
        "Grupo": request.form['grupo'],
        "CategoriaDeArticulo": request.form['categoria'],
        "Clasificacion": request.form['clasificacion'],
        "TipodeArticulo": request.form['tipo'],
        "Paletadecolores": request.form['paleta_colores']
    }

    # Configurar los encabezados para indicar que estás enviando datos JSON
    headers['Content-Type'] = 'application/json'
    headers['Accept'] = 'application/json'

    # Realizar la solicitud PUT con los datos modificados
    response = requests.put(f"{API_URL_ARTICULO}/{codigo}/", headers=headers, json=datos_modificados  # Usar 'json' en lugar de 'data' para enviar datos JSON
    )

    # Restaurar los encabezados a su estado original
    headers.pop('Content-Type', None)
    headers.pop('Accept', None)

    # Manejar la respuesta según sea necesario
    if response.status_code == 200:
        mensaje_del_servidor = "Artículo modificado con éxito"
    else:
        mensaje_del_servidor = f"Error al modificar el artículo: {response.text}"

    # Obtener datos existentes del artículo después de la modificación
    datos_existentes = obtener_datos_articulo(base_de_datos, codigo)

    return render_template('modificar.html', base_de_datos=base_de_datos, codigo=codigo, mensaje_del_servidor=mensaje_del_servidor, datos_existentes=datos_existentes)


def get_proveedores_path():
    script_dir = os.path.dirname(__file__)
    data_dir = os.path.join(script_dir, 'data')
    proveedores_path = os.path.join(data_dir, 'proveedores.json')
    return proveedores_path


def alta_proveedor_en_api(codigo, nombre, base_de_datos):
    api_url = "http://190.220.155.74:8008/api.Dragonfish/Proveedor/"
    headers = {
        "IdCliente": "APIALEX",
        "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NDY5MDAwNTMsInVzdWFyaW8iOiJBRE1JTiIsInBhc3N3b3JkIjoiMWFmMjBlZjg2OTkyMjQzNTVlN2M1ZDcxNjBjYmUyMDM5MjBlZTgwZTVmODlkMWY2Mzk5NDVhNDY5YzQ5YWQyYSJ9.bQw_DdHDl3mThtPacAX24GS0YXcnAbEnB_2lR9N0HJU",
        "BaseDeDatos": base_de_datos,
        "Content-Type": "application/json"
    }
    params = {
        "Codigo": codigo,
        "Nombre": nombre
        # Agrega otros campos según sea necesario
    }
    response = requests.post(api_url, headers=headers, json=params)
    return response.status_code

def load_proveedores():
    try:
        with open(get_proveedores_path(), 'r') as file:
            # Cargar todo el contenido del archivo como una sola cadena
            content = file.read()
            # Convertir la cadena a un objeto JSON
            proveedores = json.loads(content)
        return proveedores
    except FileNotFoundError:
        return {"opciones": []}
    except json.JSONDecodeError:
        return {"opciones": []}

def save_proveedores(proveedores):
    proveedores_path = get_proveedores_path()
    with open(proveedores_path, 'w') as file:
        # Escribe la lista de proveedores en formato JSON
        json.dump(proveedores, file, indent=2, ensure_ascii=False)

@app.route('/alta_proveedor', methods=['GET', 'POST'])
def alta_proveedor():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nombre = request.form.get('nombre')
        base_de_datos = request.form.get('base_de_datos')

        # Cargar proveedores al inicio de la aplicación
        proveedores = load_proveedores()

        # Verifica si el proveedor ya existe en la lista
        proveedor_existente = next((p for p in proveedores.get("opciones", []) if isinstance(p, dict) and p.get("codigo") == codigo), None)

        if proveedor_existente is None:
            # Intenta dar de alta el proveedor en la API
            api_status_code = alta_proveedor_en_api(codigo, nombre, base_de_datos)

            if api_status_code == 201:
                # El proveedor se creó en la API, ahora añádelo a la lista local
                nuevo_proveedor = {"codigo": codigo, "nombre": nombre}
                
                # Verifica si ya hay opciones, si no, inicializa la lista
                if "opciones" not in proveedores:
                    proveedores["opciones"] = []
                
                proveedores["opciones"].append(nuevo_proveedor)

                # Guarda la lista de proveedores actualizada
                save_proveedores(proveedores)

                flash('Proveedor creado y añadido a la lista principal.', 'success')
                return redirect(url_for('index'))
            else:
                flash(f'Error en la petición a la API: {api_status_code}', 'error')
        else:
            flash('El proveedor ya existe en la lista.', 'error')

    return render_template('proveedores.html')

   
@app.route('/formulario.html', methods=['GET', 'POST'])
def alta_vendedor():
    if request.method == 'POST':
        # Obtener el valor de la base de datos del formulario
        base = request.form['base']

        # Crear el diccionario con los datos a enviar
        data = {
            "Codigo": request.form['codigo'],
            "Nombre": request.form['nombre'],
            "NroDocumento": request.form['nro_documento']
        }

        # Crear los headers con la información de autorización y autenticación
        headers = {
            "accept": "application/json",
            "IdCliente": "APIALEX",
            "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NDY5MDAwNTMsInVzdWFyaW8iOiJBRE1JTiIsInBhc3N3b3JkIjoiMWFmMjBlZjg2OTkyMjQzNTVlN2M1ZDcxNjBjYmUyMDM5MjBlZTgwZTVmODlkMWY2Mzk5NDVhNDY5YzQ5YWQyYSJ9.bQw_DdHDl3mThtPacAX24GS0YXcnAbEnB_2lR9N0HJU",
            "BaseDeDatos": base,
            "Content-Type": "application/json"
        }

        # Hacer la solicitud POST a la API
        url = "http://190.220.155.74:8008/api.Dragonfish/Vendedor/"
        response = requests.post(url, json=data, headers=headers)

        # Verificar si la solicitud fue exitosa
        if response.status_code in [200, 201]:
            mensaje = "Alta de vendedor exitosa."
            nuevo_vendedor = response.json()
            return render_template('alta.html', mensaje=mensaje, nuevo_vendedor=nuevo_vendedor)
        elif response.status_code == 409:
            mensaje = "El código ya existe."
            return jsonify({'mensaje': mensaje, 'nuevo_vendedor': None})
        else:
            mensaje = f"SOLICITUD REALIZADA INCORRECTAMENTE: {response.status_code}"
            return jsonify({'mensaje': mensaje, 'nuevo_vendedor': None})

    return render_template('formulario.html')

@app.route('/consulta', methods=['GET', 'POST'])
def consulta():
    if request.method == 'POST':
        codigo = request.form['codigo']
        base_datos = request.form['base_de_datos']

        headers = {
            'IdCliente': 'APIALEX',
            'Authorization': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NDY5MDAwNTMsInVzdWFyaW8iOiJBRE1JTiIsInBhc3N3b3JkIjoiMWFmMjBlZjg2OTkyMjQzNTVlN2M1ZDcxNjBjYmUyMDM5MjBlZTgwZTVmODlkMWY2Mzk5NDVhNDY5YzQ5YWQyYSJ9.bQw_DdHDl3mThtPacAX24GS0YXcnAbEnB_2lR9N0HJU',
            'BaseDeDatos': base_datos
        }

        params = {
            'query': codigo
        }

        response = requests.get('http://190.220.155.74:8008/api.Dragonfish/Preciodearticulo', headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()

            # Crear un DataFrame con los datos relevantes
            df = pd.DataFrame(data['Resultados'])            
            df_filtered = df[['Articulo', 'Codigo', 'PrecioDirecto', 'ListaDePrecio']]

            # Crear el archivo Excel
            excel_filename = 'consulta_resultado.xlsx'
            df_filtered.to_excel(excel_filename, index=False)

            return render_template('resultado.html', data=df_filtered, excel_filename=excel_filename)
        else:
            return render_template('resultado.html', error='Error en la consulta API')
    else:
        return render_template('consulta.html')
    


@app.route('/descargar/<filename>')
def descargar_resultado(filename):
    return send_file(filename, as_attachment=True)


'''RUTAS DEL SISTEMA'''

@app.route('/formulario_actualizacion.html')
def formulario_actualizacion():
    return render_template('formulario_actualizacion.html')



@app.route('/formulario.html')
def form():
    return render_template('formulario.html')

@app.route('/resultado.html')
def resul():
    return render_template('resultado.html')

@app.route('/valores')
def valores():
    # Lógica de la vista...
    return render_template('valores.html')

@app.route('/')
def inicio():
    return render_template('inicio.html')

# Función para la página de actualización de precios
@app.route('/actualizar_precios', methods=['GET', 'POST'])
def actualizar_precios():
    if request.method == 'POST':
        # Obtener datos del formulario
        codigo = request.form['codigo']
        articulo = request.form['articulo']
        listadeprecio = request.form['listadeprecio']
        preciodirecto = float(request.form['preciodirecto']) 
        Basededatos = request.form['base_de_datos']# Convertir a número

        # Realizar la solicitud PUT a la API para actualizar el precio
        headers = {
            'IdCliente': 'APIALEX',
            'Authorization': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NDY5MDAwNTMsInVzdWFyaW8iOiJBRE1JTiIsInBhc3N3b3JkIjoiMWFmMjBlZjg2OTkyMjQzNTVlN2M1ZDcxNjBjYmUyMDM5MjBlZTgwZTVmODlkMWY2Mzk5NDVhNDY5YzQ5YWQyYSJ9.bQw_DdHDl3mThtPacAX24GS0YXcnAbEnB_2lR9N0HJU',
            'BaseDeDatos': Basededatos
        }

        payload = {
            "Codigo": codigo,
            "Articulo": articulo,
            "ListaDePrecio": listadeprecio,
            "PrecioDirecto": preciodirecto
        }

        response = requests.put(f'http://190.220.155.74:8008/api.Dragonfish/Preciodearticulo/{codigo}/', headers=headers, json=payload)
        print(response.text)

        # Verificar la respuesta de la API
        if response.status_code == 200:
            return render_template('actualizacion_exitosa.html')
        else:
            return render_template('error_actualizacion.html', error='Error al actualizar el precio')
    
    return render_template('formulario_actualizacion.html')

# Ruta para servir archivos estáticos (en este caso, tu archivo JSON)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/data/<path:filename>')
def data_files(filename):
    return send_from_directory('data', filename)


# Plantilla para la actualización exitosa
@app.route('/actualizacion_exitosa.html')
def actualizacion_exitosa():
    return render_template('actualizacion_exitosa.html')

# Plantilla para errores durante la actualización
@app.route('/error_actualizacion.html')
def error_actualizacion():
    return render_template('error_actualizacion.html')


if __name__ == '__main__':
    app.run(debug=False)

