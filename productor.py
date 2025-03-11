                                                                 
import pika

rabbit_host = '10.128.0.3'
rabbit_user = 'monitoring_user'
rabbit_password = 'isis2503'
exchange = 'monitoring_prediction'
topic = 'eeg.response'

def enviar_prediccion(resultado):
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=rabbit_host,
        credentials=pika.PlainCredentials(rabbit_user, rabbit_password)
    ))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange, exchange_type='topic')

    channel.basic_publish(
        exchange=exchange,
        routing_key=topic,
        body=resultado
    )

    print(f" Predicción calculada: {resultado}")

    connection.close()