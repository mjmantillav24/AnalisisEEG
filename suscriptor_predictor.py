import pika
import os
import ast  
from google.cloud import storage
from modelo import iniciar
from productorRespuesta import enviar_prediccion

rabbit_host = '10.128.0.3'
rabbit_user = 'monitoring_user'
rabbit_password = 'isis2503'
exchange = 'monitoring_prediction'
topic = 'eeg.request'


connection = pika.BlockingConnection(pika.ConnectionParameters(
    host=rabbit_host,
    credentials=pika.PlainCredentials(rabbit_user, rabbit_password)
))
channel = connection.channel()
channel.queue_declare(queue='monitoring_prediction')
channel.queue_bind(exchange=exchange, queue='monitoring_prediction', routing_key=topic)

storage_client = storage.Client()
def descargar_archivo_gcs(gs_path):
    parts = gs_path.replace("gs://", "").split("/", 1)
    bucket_name, file_name = parts
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    local_path = f"/home/mariajosemantilla0/{os.path.basename(file_name)}"
    blob.download_to_filename(local_path)
    print(f"Archivo descargado desde GCS: {local_path}")
    return local_path


print("procesando archivo para analizar...")

def on_request(ch, method, properties, body):
    print("entro")
    mensaje = body.decode().strip()
    print(mensaje)
    data = ast.literal_eval(mensaje)
    print("entro")
    file_path = data.get('path')
    print(f" Modelo recibió EEG: {file_path}")
    local_file = descargar_archivo_gcs(file_path)
    resultado = iniciar(local_file)
    print(f"  Predicción generada: {resultado}")

    enviar_prediccion(resultado)


channel.basic_consume(queue='monitoring_prediction', on_message_callback=on_request, auto_ack=True)
print("Esperando mensajes")
channel.start_consuming()