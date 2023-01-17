import threading
from flask import Flask, json, request
from pymongo import MongoClient, errors
from kafka import KafkaConsumer
import sys, logging

app = Flask(__name__)

# kafkaBroker = "localhost:9092"
kafkaBootstrap = "my-cluster-kafka-bootstrap:9092"
mongoHost = "" 'mongodb://siq-mongo-srv:27017/'

client = MongoClient(mongoHost)
# ensembl_db = client['ensemblGenes']
db = client['genes']
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logging.info("Starting Mongo API.")

# Kafka consumer
ensembl_consumer = KafkaConsumer(
    'ensemblGenes',
     bootstrap_servers=kafkaBootstrap,
     value_deserializer=lambda m: json.loads(m.decode('ascii'))
)

disgenet_consumer = KafkaConsumer(
    'disgenet-genes',
     bootstrap_servers=kafkaBootstrap,
     value_deserializer=lambda m: json.loads(m.decode('ascii'))
)

def consume_ensembl():
    for message in ensembl_consumer:
        data = message.value
        # ensembl_db.mycollection.insert_one(data)
        try:
            logging.info("Sending kafka event to MongoDB - ensembl.")
            db.ensemblGenes.insert_one(data)
        except errors.DuplicateKeyError:
            logging.error(f"Duplicate key error occured while inserting data {data}")
        except Exception as e:
            logging.info(f"Error occured while inserting data {data} to MongoDB: {e}")

def consume_disgenet():
    for message in disgenet_consumer:
        data = message.value
        # disgenet_db.mycollection.insert_one(data)
        try:
            logging.info("Sending kafka event to MongoDB - disgenet.")
            db.disgenetGenes.insert_one(data)
        except errors.DuplicateKeyError:
            logging.info(f"Duplicate key error occured while inserting data {data}")
        except Exception as e:
            logging.info(f"Error occured while inserting data {data} to MongoDB: {e}")

@app.route('/ensembl', methods=['POST'])
def save_ensembl():
    data = request.get_json()
    # ensembl_db.mycollection.insert_one(data)
    # return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    try:
        db.ensemblGenes.insert_one(data)
        logging.info("Saved to MongoDB - ensembl!")
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    except errors.DuplicateKeyError:
        logging.error(f"Duplicate key error occured while inserting data {data}")
    except Exception as e:
        logging.error(f"Error occured while inserting data {data} to MongoDB: {e}")

@app.route('/disgenet', methods=['POST'])
def save_disgenet():
    data = request.get_json()
    # disgenet_db.mycollection.insert_one(data)
    # return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    print("Saving to MongoDB - disgenet")
    try:
        db.disgenetGenes.insert_one(data)
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
        logging.info("Saved to MongoDB - ensembl!")
    except errors.DuplicateKeyError:
        print(f"Duplicate key error occured while inserting data {data}")
    except Exception as e:
        print(f"Error occured while inserting data {data} to MongoDB: {e}")

if __name__ == '__main__':
    ensembl_thread = threading.Thread(target=consume_ensembl)
    ensembl_thread.start()
    disgenet_thread = threading.Thread(target=consume_disgenet)
    disgenet_thread.start()
    app.run(host='0.0.0.0', port=5020, debug=False)
