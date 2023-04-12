from flask import Flask, jsonify
import requests
import logging, sys
import json
from kafka import KafkaProducer

app = Flask(__name__)
print('STDIO: Starting kafka ingestor - raw json. v1.0.3')


@app.route('/ingest/gene/<id>', methods=['GET'])
def get_gene(id):
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    logging.info('get_gene called for id: %s', id)
    kafkaBootstrap = 'my-cluster-kafka-bootstrap:9092'
    # kafkaBrokers = 'localhost:9092'  # run on local
    producer = KafkaProducer(bootstrap_servers=kafkaBootstrap, value_serializer=lambda m: json.dumps(m).encode('ascii'))
    # Query Ensembl API for gene annotations
    response = requests.get(f"http://rest.ensembl.org/lookup/id/{id}?content-type=application/json")
    data = response.json()

    # Extract relevant data from Ensembl API response
    # gene = {
    #     'id': data['id'],
    #     'displayName': data['display_name'],
    #     'seqRegionName': data['seq_region_name'],
    #     'location': {
    #         'start': data['start'],
    #         'end': data['end'],
    #         'strand': data['strand'],
    #         'chromosome': data['seq_region_name'],
    #     },
    #     'strand': data['strand'],
    #     'start': data['start'],
    #     'end': data['end'],
    #     'assemblyName': data['assembly_name'],
    #     'objectType': data['object_type'],
    #     'source': data['source'],
    #     'logicName': data['logic_name'],
    #     'species': data['species'],
    #     'version': data['version'],
    #     'biotype': data['biotype'],
    #     'canonicalTranscript': data['canonical_transcript'],
    #     'description': data['description'],
    #     'dbType': data['db_type'],
    # }

    
    def handle_message(msg, producer):
        logging.info('kafkaBootstrap: ' + kafkaBootstrap)
        # if producer is None:
        #     producer = KafkaProducer(bootstrap_servers=kafkaBootstrap)
        try:
            producer.send('ensembl-genes', data)
            producer.flush()
            logging.info('published to ensembl-genes')
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
