from flask import Flask, jsonify
import requests
import logging, sys
import json
from kafka import KafkaProducer

app = Flask(__name__)
print('STDIO: Starting kafka ingestor - raw json. v1.0.3')
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

ensembl_lookup_endpoint = "http://rest.ensembl.org/lookup/id"
kafkaBootstrap = 'my-cluster-kafka-bootstrap:9092'
producer = KafkaProducer(bootstrap_servers=kafkaBootstrap, value_serializer=lambda m: json.dumps(m).encode('ascii'))


@app.route('/gene/<id>', methods=['GET'])
def get_gene(id):
    logging.info('get_gene called for id: %s', id)
    kafkaBootstrap = 'my-cluster-kafka-bootstrap:9092'
    # kafkaBrokers = 'localhost:9092'  # run on local
    # Query Ensembl API for gene annotations
    try:
        response = requests.get(f"http://rest.ensembl.org/lookup/id/{id}?content-type=application/json")
    except Exception as e:
        logging.error('Ensembl fetch failed: %s', e)
        return jsonify({'message': 'Errorish'}), 500

    msg = response.json()
    logging.info('published to ensembl-genes ')
    if handle_message(msg, producer):
        logging.info('Kafka publish succedded')
        return jsonify({'message': 'Gene successfully ingested'}), 201
    else:
        logging.error('Kafka publish failed')
        return jsonify({'message': 'Error'}), 500

        

@app.route('/ingest/ensembl/gene/<id>', methods=['GET'])
def get_ensembl_gene(id):
    logging.info('get_ensembl_gene called for id: %s', id)
    
    try: 
        response = requests.get(f"{ensembl_lookup_endpoint}/{id}?content-type=application/json")
        response.raise_for_status()
        msg = response.json()
        handle_message(msg, producer)
        return jsonify({'message': 'Gene successfully ingested ... Really'}), 201
    except requests.exceptions.HTTPError as errh:
        return jsonify(response.json()), errh.response.status_code
    except requests.exceptions.ConnectionError as errc:
        return jsonify({'message': 'Error: ConnectionError'}), 500
    except requests.exceptions.Timeout as errt:
        return jsonify({'message': 'Error: Timeout'}), 500
    except requests.exceptions.RequestException as err:
        return jsonify({'message': 'Error: RequestException'}), 500

# @app.route('/ingest/ensembl/genes', methods=['POST'])
# def post_genes():
#     ids = request.json['ids']
#     id_string = ",".join(ids)
#     logging.info('get_gene called for ids: %s', ids)
#     response = requests.get(f"{ensembl_lookup_endpoint}/id?id={id_string}?content-type=application/json")
#     data = response.json()
#     producer.send(topic='ensemblGenes', value=data)
#     return jsonify({'message': 'Genes successfully ingested'}), 201

    
def handle_message(msg, producer):
    logging.info('kafkaBootstrap: ' + kafkaBootstrap)
    # producer = KafkaProducer(bootstrap_servers=kafkaBootstrap, value_serializer=lambda m: json.dumps(m).encode('ascii'))
    if producer is None:
        producer = KafkaProducer(bootstrap_servers=kafkaBootstrap)
    try:
        producer.send('ensemblGenes', msg)
        producer.flush()
        logging.info(f'published to ensemblGenes -  {msg}')
    except Exception as e:
        producer.close()
        producer = None
        #Return False will resend the message.
        logging.error('published failed: %s', e)
        return False
    logging.info('Kafka publish succedded')
    return True

# Send gene data to Kafka


# return jsonify(data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5010)
