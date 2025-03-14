import pika
import os
import ast 
import requests
import time
from datetime import datetime 
from google.cloud import storage
from productorRespuesta import enviar_prediccion


tiempo_inicio_programa = datetime.now()


rabbit_host = '10.128.0.3'
rabbit_user = 'monitoring_user'
rabbit_password = 'isis2503'
exchange = 'monitoring_prediction'
topic = 'eeg.request'

COLAB_SERVER_URL = "https://8127-34-86-68-242.ngrok-free.app/upload"

connection = pika.BlockingConnection(pika.ConnectionParameters(
    host=rabbit_host,
    credentials=pika.PlainCredentials(rabbit_user, rabbit_password)
))
channel = connection.channel()
channel.queue_declare(queue='monitoring_prediction')
channel.queue_bind(exchange=exchange, queue='monitoring_prediction', routing_key=topic)

storage_client = storage.Client()
def log_tiempo(mensaje):
    tiempo_transcurrido = (datetime.now() - tiempo_inicio_programa).total_seconds()
    print()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ({tiempo_transcurrido:.3f} s) {mensaje}")
    
def descargar_archivo_gcs(gs_path):
    inicio = datetime.now()
    log_tiempo("Descargando archivo desde GCS...")
    parts = gs_path.replace("gs://", "").split("/", 1)
    bucket_name, file_name = parts
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    local_path = f"/home/mariajosemantilla0/{os.path.basename(file_name)}"
    blob.download_to_filename(local_path)
    fin = datetime.now()
    tiempo_descarga = (fin - inicio).total_seconds() 
    log_tiempo(f"Archivo descargado en {local_path} en {tiempo_descarga:.3f} segundos")
    return local_path

log_tiempo("procesando archivo para analizar...")

def enviar_a_colab(local_file,id_examen):
    inicio = datetime.now()
    log_tiempo(f"Enviando archivo {local_file} a Colab...")
    files = {'file': open(local_file, 'rb')}
    response = requests.post(COLAB_SERVER_URL, files=files)
    response_json = response.json()
    fin = datetime.now()
    tiempo_transcurrido = (fin - inicio).total_seconds()
    if response.status_code == 200:
        resultado = response_json.get("mensaje", "Error en la predicción")
        print(f" Predicción recibida: {resultado} en {tiempo_transcurrido:.3f} segundos")


        prediccion = "{'id': '%s', 'resultado':'%s'}" % (id_examen, resultado)
        enviar_prediccion(prediccion)
    else:
        log_tiempo(f"Error en la respuesta del servidor Colab: {response.text}")


def on_request(ch, method, properties, body):
    inicio_proceso = datetime.now()
    start_time = time.time()
    log_tiempo("Mensaje recibido, procesando...")

    mensaje = body.decode().strip()
    print(mensaje)
    data = ast.literal_eval(mensaje)
    file_path = data.get('path')
    log_tiempo(f"Modelo recibió EEG: {file_path}")
    local_file = descargar_archivo_gcs(file_path)
    print(local_file)

    enviar_a_colab(local_file,data.get('id'))
    os.remove(local_file)
    fin_proceso = datetime.now()
    tiempo_total = (fin_proceso - inicio_proceso).total_seconds()
    log_tiempo(f"Proceso finalizado en {tiempo_total:.3f} segundos")
    print("-----------------------------------------------------------------------------------")


channel.basic_consume(queue='monitoring_prediction', on_message_callback=on_request, auto_ack=True)
log_tiempo("Esperando mensajes...")
channel.start_consuming()
