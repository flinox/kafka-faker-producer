## 
## Programa para gerar mensagens para tópicos kafka usando como base o schema atual do tópico
## obtido através do schema registry de maneira automatica ou informando os valores campo a campo
##
## v1 - 11/2021 - Fernando Lino Di Tomazzo Silva - https://www.linkedin.com/in/flinox
##
## usage: 
##    producer.py [-h] topico --auto True
## 
## positional arguments:
##   topico                Informe o nome do topico que deseja produzir as mensagens!
## 
## optional arguments:
##   -h, --help         show this help message and exit
##   --auto, --no-auto  Opcional, informe se deseja que as informações sejam preenchidas automaticamente! --auto ou --no-auto
## 
## python producer.py account-created --auto True


# from confluent_kafka.serialization import StringDeserializer
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
import argparse
import uuid
import os
import json
import re
import datetime
from faker import Faker
import random 
  



def get_mock_data(field_type,retorno):

    faker = Faker(['pt_BR'])

    if 'string' in field_type['type']:

        # REGRAS PARA DAR MAIS REALISMO AOS DADOS FAKE
        if field_type['name'] == 'id':
            return '{}-{}'.format('FAKE',str(uuid.uuid4()).upper())
        else:
            return faker.name()

    elif 'boolean' in field_type['type']:
        return random.choice([True, False])

    elif 'long' in field_type['type']:
        return int(datetime.datetime.now().timestamp()) # *1000 para mandar miliseconds

    elif 'int' in field_type['type']:
        return faker.random_int(0, 100)

    elif 'float' in field_type['type']:
        return float(faker.random_int(0, 100))

    elif 'bytes' in field_type['type']:
        return os.urandom(5)
    
    elif isinstance(field_type,dict):

        if isinstance(field_type['type'],list):

            if 'null' in field_type['type']: 
                field_type['type'].remove('null')
            field_type_new = field_type.copy()
            field_type_new['type'] = field_type['type'][0]
            return get_mock_data(field_type_new,None)

        elif 'enum' in field_type['type']['type']:
            return random.choice(field_type['type']['symbols'])

        elif 'record' in field_type['type']['type']:

            if retorno is None:
                retorno = {}

            for recordField in field_type['type']['fields']:

                # record
                if isinstance(recordField['type'],dict) and recordField['type']['type'] == 'record':
                    
                    retornoInside = {}
                    for recordFieldInside in recordField['type']['fields']:

                        retornoInside[recordFieldInside['name']] = faker.name()

                    retorno[recordField['name']] = retornoInside

                # array
                elif isinstance(recordField['type'],dict) and recordField['type']['type'] == 'array':

                    if recordField['name'] not in retorno:
                        retorno[recordField['name']] = []

                    for _ in range(0,faker.random_int(1, 2)):
                        recordField_type_copy = random.choice(list(recordField['type']['items']['fields'])).copy()
                        recordField_type_copy['type'][1]['fields'][0]['name'] = recordField_type_copy['name']
                        retorno[recordField['name']].append(get_mock_data(recordField_type_copy,None))
                
                else:
                    retorno[recordField['name']] = get_mock_data(recordField,retorno)

            return retorno
    
        elif 'array' in field_type['type']['type']:

            if  retorno is None:
                retorno = []

            field_type_copy = field_type.copy()
            field_type_copy['type'] = field_type['type']['items']

            for _ in range(0,faker.random_int(1, 3)):
                retorno.append(get_mock_data(field_type_copy,None))
            
            return retorno

        elif 'long' in field_type['type']['type']:
            return int(datetime.datetime.now().timestamp())

        elif 'int' in field_type['type']['type']:
            return faker.random_int(0, 100)

    elif 'null' in field_type['type']:
        return None 

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
        print('-'*80)
    else:
        print('')
        print('Message delivered!')
        print('   Topic    : {} '.format(msg.topic()))
        print('   Partition: {} '.format(msg.partition()))
        print('   Offset   : {} '.format(msg.offset()))
        print('-'*80)

def get_schema_of_topic(sr_url,sr_key,sr_secret,topico):


    # Schema Registry Configuration
    schema_registry_conf = {'url'                 : sr_url,
                            'basic.auth.user.info': '{}:{}'.format(sr_key,sr_secret)}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    try:

        key_schema = None
        key_avro_serializer = None
        key_json_schema = None
        key_fields_schema = None

        key_schema = schema_registry_client.get_latest_version('{}-key'.format(topico))
        key_avro_serializer = AvroSerializer(schema_registry_client,key_schema.schema.schema_str)
        key_json_schema = json.loads(key_schema.schema.schema_str)
        key_fields_schema = key_json_schema['fields']

    except Exception as e :
        print('   >>> Sem schema para a chave! {}'.format(e))


    try:

        value_schema = None
        value_avro_serializer = None
        value_json_schema = None
        value_fields_schema = None

        value_schema = schema_registry_client.get_latest_version('{}-value'.format(topico))
        value_avro_serializer = AvroSerializer(schema_registry_client,value_schema.schema.schema_str)
        value_json_schema = json.loads(value_schema.schema.schema_str)
        value_fields_schema = value_json_schema['fields']
    
    except Exception as e :
        print('   >>> ERROR pegando o schema do topico de valor!')
        print('   >>> {}'.format(e))
        exit(1)
    
    return key_avro_serializer, value_avro_serializer, key_fields_schema, value_fields_schema

def get_parameters(params):
    
    # Define os parametros esperados e obrigatorios
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", type=str, help="Opcional, informe o nome do topico")
    parser.add_argument('--auto', default=False, action='store_true', help="Informe se deseja que as informações sejam preenchidas automaticamente!")
    parser.add_argument('--no-auto', dest='auto', action='store_false', help="Informe se deseja que as informações não sejam preenchidas automaticamente!")
    parser.add_argument('--semi-auto', dest='semi', action='store_true', help="Informe se deseja que as informações sejam preenchidas automaticamente com exceção do ID!")
    parser.add_argument('--change', dest='change', action='store_true', help="Informe se deseja alterar as informações geradas antes de produzir as mensagens")
    args = parser.parse_args()


    # Pega os argumentos passados
    params['SR_URL'] = os.environ['SR_URL']
    params['SR_API_KEY'] = os.environ['SR_API_KEY']
    params['SR_API_SECRET'] = os.environ['SR_API_SECRET']
    params['KC_URL'] = os.environ['KC_URL']    
    params['KC_API_KEY'] = os.environ['KC_API_KEY']
    params['KC_API_SECRET'] = os.environ['KC_API_SECRET']
    params['PRODUCERID'] = 'mocker'
    params['TOPICO'] = args.topic
    params['AUTO'] = args.auto
    params['SEMI'] = args.semi
    params['CHANGE'] = args.change

    print('#'*80)
    print('   Kafka Cluster        : {}'.format(params['KC_URL']))
    print('   Schema Registry Url  : {}'.format(params['SR_URL']))
    print('   Producer ID          : {}'.format(params['PRODUCERID']))
    print('   KEY                  : {}'.format(params['KC_API_KEY']))
    print('#'*80)

    return params

def set_producer(broker,producerid,kc_key,kc_secret,avro_key,avro_value):

    # kafka configuration

    url = re.compile(r"https?://(www\.)?")
    kafka_broker = url.sub('', broker).strip().strip('/')

    kafka_conf = {'bootstrap.servers': kafka_broker,
                'client.id': producerid,
                'security.protocol':'SASL_SSL',
                'sasl.mechanisms':'PLAIN',
                'sasl.username':kc_key,
                'sasl.password':kc_secret,
                'on_delivery': delivery_report,
                'acks':"all",
                'value.serializer': avro_value}

    if (avro_key is not None):
        kafka_conf['key.serializer'] = avro_key 
    # else:
    #     string_deserializer = StringDeserializer('utf_8')
    #     kafka_conf['key.serializer'] = string_deserializer

    return SerializingProducer(kafka_conf)

def set_mock_data_key(key_fields_schema,auto):

    fake_key_data = None
    fake_key = None

    # print('\n')
    # print('Message Key:')
    # print('='*70)
    # print('\n')

    ## Tratamento para "evento" applied-student
    if key_fields_schema is not None:

        fake_key_data = {}
        for field in key_fields_schema:

            if auto:
                fake_key_data[field['name']] = get_mock_data(field,None)
                fake_key = fake_key_data[field['name']]
                #print('{} : {}'.format(field['name'],fake_key_data[field['name']]))                    
            else:
                fake_key_data[field['name']] = input("\n'{}' tipo {} para a mensagem\n{} : ".format(field['name'],field['type'],field['doc']))
                fake_key = fake_key_data[field['name']]      
    else:
            if auto:
                fake_key_data = '{}-{}'.format('FAKE',str(uuid.uuid4()).upper())
                fake_key = fake_key_data
                #print('id : {}'.format(fake_key_data))                    
            else:
                fake_key_data = input("\nid tipo string para a mensagem\n : ")
                fake_key = fake_key_data

    return fake_key, fake_key_data

def set_mock_data_value(fake_key,value_fields_schema,auto,semi):

    fake_value_data = {}
    # print('\n')
    # print('Message Value:')
    # print('='*70)
    # print('\n')

    for field in value_fields_schema:

        if auto:
            if field['name'] in ['id']:
                fake_value_data[field['name']] = fake_key
            else:
                fake_value_data[field['name']] = get_mock_data(field,None)
            #print('{} : {}'.format(field['name'],fake_value_data[field['name']]))                    
        else:

            if 'id' == field['name']:
                value = fake_key
            elif semi:
                value = get_mock_data(field,None)
                #print('{} : {}'.format(field['name'],value)) 
            else:
                value = input("\n'{}' tipo {} para a mensagem\n{} : ".format(field['name'],field['type'],field['doc']))

                if field['type'] in ['int','long']:
                    value = int(value)
                elif field['type'] in ['boolean']:
                    value = bool(value)
                elif field['type'] in ['float']:
                    value = float(value)
                elif isinstance(field['type'],list):
                    if field['type']['type'] in ['int','long']:
                        value = int(value)
                elif isinstance(field['type'],dict):
                    if field['type']['type'] == 'enum':
                        value = value     
                    else:
                        value = eval(value)
                elif value == '':
                    value = None

            fake_value_data[field['name']] = value
    
    return fake_value_data

# INICIO
# https://backbone.krthomolog.com.br/nodeserver/graphql

params = {}
params = get_parameters(params)
auto = params['AUTO']
semi = params['SEMI']



print((datetime.datetime.now()).strftime("%d/%m/%Y %H:%M:%S"))

reenvio = False
produce = True
while produce:

    if reenvio:

        print('-'*80)
        print('Producing Message on Topic {}'.format(params['TOPICO']))
        for key_value in list_key_value:

            key = key_value['key']
            value = key_value['value']

            try:
                print('Producing messages key: {}'.format(key_value['key']))
                producer = set_producer(params['KC_URL'],params['PRODUCERID'],params['KC_API_KEY'],params['KC_API_SECRET'],key_avro_serializer,value_avro_serializer)
                producer.produce(topic=params['TOPICO'], key=key, value=value)
                producer.flush()
            except Exception as e :
                print('>>> ERROR producing message to topic!')
                print('>>> {}'.format(e))
                exit(1)

    else:

        if params['TOPICO'] is None:
            params['TOPICO'] = input("Informe o nome do topico que deseja produzir uma mensagem: ")

        print('   Topico               :',params['TOPICO'])

        key_avro_serializer, value_avro_serializer, key_fields_schema, value_fields_schema = get_schema_of_topic(params['SR_URL'],params['SR_API_KEY'],params['SR_API_SECRET'],params['TOPICO'])

        # Guarda o par da key/value gerado
        pair_key_value = {}


        # TESTES MANUAIS
        if 1==1:

            # Schema Key Message
            ##########################
            fake_key, fake_key_data = set_mock_data_key(key_fields_schema,auto)
            pair_key_value['key'] = fake_key_data

            #############
            # VALUE: para cada campo na lista de campos do schema de value
            fake_value_data = set_mock_data_value(fake_key,value_fields_schema,auto,semi)
            pair_key_value['value'] = fake_value_data

        else:

            pair_key_value['key'] = {'id': 'FAKE-TEMP-STUDENT-DOCUMENT-PENDING-1'}
            pair_key_value['value'] = {
                                        'programEnrollmentBK': 'TEMP-STUDENT-DOCUMENT-PENDING-1',
                                        'pendingDocuments': [
                                            {
                                                'type': 'Grupo 1',
                                                'documentTypes': [
                                                    {
                                                        'documentSubType': 'RG'
                                                    },
                                                    {
                                                        'documentSubType': 'CPF'
                                                    }
                                                ]
                                            }
                                        ]
                                    }


        # Alterar mensagem antes de enviar...
        if params['CHANGE']:

            print('-'*80)
            print('\nAltere os dados de KEY e MESSAGE antes de produzir a mensagem, abaixo os valores gerados para KEY e MESSAGE, use-os como base para alterar a mensagem que deseja produzir:')

            print('\n---- KEY     ----')
            print(fake_key_data)

            print('\n---- MESSAGE ----')        
            print(fake_value_data)

            print('\n')
            print('-'*80)

            dict_key =     input("Informe a nova KEY     : ")
            dict_message = input("Informe a nova MESSAGE : ")

            try:

                dict_key = dict_key.replace("'", "\"")
                dict_key = json.loads(dict_key)

                dict_message = ((dict_message.replace("'", "\"")).replace("False", "false")).replace("True", "true")
                dict_message = json.loads(dict_message)

                pair_key_value['key']   = dict_key
                pair_key_value['value'] = dict_message

            except Exception as e :

                print('*** Não foi possível converter os dados informados, tente novamente! \n\n%s' % e)
                exit(1)
            
        # Adicionando o par key/value a lista
        list_key_value = []
        list_key_value.append(pair_key_value)

        print('\n---- KEY     ----')
        print(pair_key_value['key'])

        print('\n---- MESSAGE ----')
        print(pair_key_value['value'])


        print('-'*80)
        print('Producing Message on Topic {}'.format(params['TOPICO']))
        for key_value in list_key_value:

            key = key_value['key']
            value = key_value['value']

            try:
                print('Producing messages key: {}'.format(key_value['key']))
                producer = set_producer(params['KC_URL'],params['PRODUCERID'],params['KC_API_KEY'],params['KC_API_SECRET'],key_avro_serializer,value_avro_serializer)
                producer.produce(topic=params['TOPICO'], key=key, value=value)
                producer.flush()
            except Exception as e :
                print('>>> ERROR producing message to topic!')
                print('>>> {}'.format(e))
                exit(1)

    if input("Quer reenviar a mensagem ? (S/N) ") in ('S','s'):
        reenvio = True
        produce = True 
    else:
        reenvio = False
        produce = False

    
print('Done!')
print('#'*80)