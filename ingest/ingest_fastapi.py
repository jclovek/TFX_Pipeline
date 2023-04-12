from fastapi import FastAPI, HTTPException
import requests
import logging, sys
import json
from kafka import KafkaProducer

app = FastAPI()
print('STDIO: Starting kafka ingestor - raw json. v1.0.3')
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

ensembl_lookup_endpoint = "http://rest.ensembl.org/lookup/id"
kafkaBootstrap = 'my-cluster-kafka-bootstrap:9092'
producer = KafkaProducer(bootstrap_servers=kafkaBootstrap, value_serializer=lambda m: json.dumps(m).encode('ascii'))

@app.get("/gene/{id}")
def get_gene(id: str):
    logging.info('get_gene called for id: %s', id)
    kafkaBootstrap = 'my-cluster-kafka-bootstrap:9092'
    try:
        response = requests.get(f"http://rest.ensembl.org/lookup/id/{id}?content-type=application/json")
    except Exception as e:
        logging.error('Ensembl fetch failed: %s', e)
        raise HTTPException(status_code=500, detail={'message': 'Errorish'})

    msg = response.json()
    logging.info('published to ensembl-genes ')
    if handle_message(msg, producer):
        logging.info('Kafka publish succedded')
        return {'message': 'Gene successfully ingested'}
    else:
        logging.error('Kafka publish failed')
        raise HTTPException(status_code=500, detail={'message': 'Error'})


@app.get("/ingest/ensembl/gene/{id}")
def get_ensembl_gene(id: str):
    logging.info('get_ensembl_gene called for id: %s', id)
    try: 
        response = requests.get(f"{ensembl_lookup_endpoint}/{id}?content-type=application/json")
        response.raise_for_status()
        msg = response.json()
        handle_message(msg, producer)
        return {'message': 'Gene successfully ingested ... Really'}
    except requests.exceptions.HTTPError as errh:
        raise HTTPException(status_code=errh.response.status_code, detail=response.json())
    except requests.exceptions.ConnectionError as errc:
        raise HTTPException(status_code=500, detail={'message': 'Error: ConnectionError'})
    except requests.exceptions.Timeout as errt:
        raise HTTPException(status_code=500, detail={'message': 'Error: Timeout'})
    except requests.exceptions.RequestException as err:
        raise HTTPException(status_code=500, detail={'message': 'Error: RequestException'})


def handle_message(msg, producer):
    logging.info('kafkaBootstrap: ' + kafkaBootstrap)
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5010)
