from flask import Flask, jsonify
import requests
import logging, sys
import json
from kafka import KafkaProducer

app = Flask(__name__)
print('STDIO: Starting kafka ingestor - raw json. v1.0.3')
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

ensembl_lookup_endpoint = "http://rest.ensembl.org/lookup/id/"
kafkaBootstrap = 'my-cluster-kafka-bootstrap:9092'
producer = KafkaProducer(bootstrap_servers=kafkaBootstrap, value_serializer=lambda m: json.dumps(m).encode('ascii'))




@app.route('/ingest/ensembl/gene/<id>', methods=['GET'])
def get_gene(id):
    logging.info('get_gene called for id: %s', id)
    response = requests.get(f"{ensembl_lookup_endpoint}/{id}?content-type=application/json")
    data = response.json()
    try: 
        producer.send(topic='ensemblGenes', value=data)
        logging.info('Kafka publish succedded')
        return jsonify({'message': 'Gene successfully ingested ... Really'}), 201
    except Exception as e:
        logging.error('Kafka publish failed: %s', e)
        return jsonify({'message': 'Error'})

@app.route('/ingest/ensembl/genes', methods=['POST'])
def post_genes():
    ids = request.json['ids']
    id_string = ",".join(ids)
    logging.info('get_gene called for ids: %s', ids)
    response = requests.get(f"{ensembl_lookup_endpoint}/id?id={id_string}?content-type=application/json")
    data = response.json()
    producer.send(topic='ensemblGenes', value=data)
    return jsonify({'message': 'Genes successfully ingested'}), 201

    
    def handle_message(msg, producer):
        logging.info('kafkaBootstrap: ' + kafkaBootstrap)
        # if producer is None:
        #     producer = KafkaProducer(bootstrap_servers=kafkaBootstrap)
        try:
            producer.send('ensemblGenes', data)
            producer.flush()
            logging.info('published to ensemblGenes')
        except Exception as e:
            producer.close()
            producer = None
            #Return False will resend the message.
            logging.error('published failed: %s', e)
            return False
        return True

    # Send gene data to Kafka
    handle_message(data, producer)

    return jsonify(data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5010)
