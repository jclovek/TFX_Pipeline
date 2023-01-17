import threading
import sys, logging
from flask import Flask, request, json, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from kafka import KafkaConsumer

# todo - move to env variables or kube secrets
sqlHost = "postgres:5432"
sqlUser = "admin"
sqlPassword = "changeme"

app = Flask(__name__)
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logging.info('get_gene called for id: %s', id)
# 'postgresql://admin:psltest@host:port/database'
URI = 'postgresql://' + sqlUser + ':' + sqlPassword + '@' + sqlHost + '/postgresdb'
print("SQLALCHEMY_DATABASE_URI: " + URI, file=sys.stderr)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' + sqlUser + ':' + sqlPassword + '@' + sqlHost + '/postgresdb'
db = SQLAlchemy(app)
# URI = 'postgresql://' + sqlUser + ':' + sqlPassword + '@' + sqlHost + '/postgres'
# print("SQLALCHEMY_DATABASE_URI: " | URI, file=sys.stderr)

kafkaBootstrap = "my-cluster-kafka-bootstrap:9092"

ensembl_consumer = KafkaConsumer(
    'ensemblGenes',
     bootstrap_servers=kafkaBootstrap,
     value_deserializer=lambda m: json.loads(m.decode('ascii'))
)

class Gene(db.Model):
    __tablename__ = 'genes'
    id = db.Column(db.String(), primary_key=True)
    display_name = db.Column(db.String())
    assembly_name = db.Column(db.String())
    biotype = db.Column(db.String())
    object_type = db.Column(db.String())
    strand = db.Column(db.Integer())
    db_type = db.Column(db.String())
    version = db.Column(db.Integer())
    seq_region_name = db.Column(db.String())
    source = db.Column(db.String())
    species = db.Column(db.String())
    start_pos = db.Column(db.Integer())
    logic_name = db.Column(db.String())
    end_pos = db.Column(db.Integer())
    description = db.Column(db.String())
    canonical_transcript = db.Column(db.String())


def add_gene(data):
    print("add_gene()", file=sys.stderr)
    try:
      new_gene = Gene(id=data['id'], 
                      display_name=data['display_name'], 
                      assembly_name=data['assembly_name'], 
                      biotype=data['biotype'],
                      object_type=data['object_type'], 
                      strand=data['strand'], 
                      db_type=data['db_type'], 
                      version=data['version'], 
                      seq_region_name=data['seq_region_name'], 
                      source=data['source'],
                      species=data['species'],
                      start_pos=data['start'],
                      logic_name=data['logic_name'],
                      end_pos=data['end'],
                      description=data['description'],
                      canonical_transcript=data['canonical_transcript'])
      db.session.add(new_gene)
      db.session.commit()
      logging.info('add_gene() success')
      return jsonify({'message': 'new gene added successfully'})
    except SQLAlchemyError as e:
      error = str(e.__dict__['orig'])
      logging.error("add_gene() fail - " + error )
      return jsonify({'message': 'An error occurred while adding the gene'})

def consume_ensembl():
    logging.info("consume_ensembl()")
    for message in ensembl_consumer:
        data = message.value
        # ensembl_db.mycollection.insert_one(data)
        add_gene(data)

@app.route('/sqldb', methods=['POST'])
def send_to_postgres():
  data = request.get_json()
  try:
    add_gene(data)
    return jsonify({'message': 'new gene added successfully'})
  except:
    return jsonify({'message': 'An error occurred while adding the gene'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5030, debug=True)
    with app.app_context(): 
      ensembl_thread = threading.Thread(target=consume_ensembl)
      ensembl_thread.start()    
      db.create_all()
