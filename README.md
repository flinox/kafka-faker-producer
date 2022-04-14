# Flinox Faker Producer
Producer 'faker' em python para gerar dados automaticos nos tópicos Kafka seguindo o padrao da última versao de schema avro esperado para esse tópico.

A Aplicação pega o schema do topico informado e te solicita todos os campos necessários com base nesse schema, inclusive informando a documentação preenchida no schema para facilitar o preenchimento.

## Como usar a imagem ?
Primeiro você precisa configurar arquivos com as keys das API's

### 1) Crie uma pasta **.keys** em sua máquina local:
```
mkdir .keys
```

### 2) Crie arquivos distintos por ambiente dentro da pasta **.keys** com o seguinte conteúdo:
```
#!/bin/bash
export KC_URL=https://XXX-XXXXX.XXXXX.confluent.cloud:9092
export KC_API_KEY=XXXXXXXXXXXXXXXXXX
export KC_API_SECRET=XXXXXXXXXXXXXXXXXXXXX
export SR_URL=https://XXXX.XXXX.confluent.cloud
export SR_API_KEY=XXXXXXXXXXXXXXXX
export SR_API_SECRET=XXXXXXXXXXX
export CC_ENVIRONMENT=XXX-XXXXXX
export CC_CLUSTER=XXXXXXXX
```
Um arquivo com os dados para ambiente de DEV o arquivo deve se chamar **env-dev.sh** o outro com os dados para o ambiente de HML o arquivo deve se chamar **env-hml.sh**

Isso servirá para quando rodar a imagem escolher em qual ambiente deseja produzir uma mensagem.

### 3) Fazer o Build da Imagem ( Exemplo )
```
docker build -t flinox/faker-producer:latest .
```

### 4) Rodando a imagem ( Exemplo )
```
docker run --rm -it --hostname flinox/faker-producer --name faker-producer \
--mount type=bind,source="$(pwd)"/.keys,target=/app/_key/ \
--mount type=bind,source="$(pwd)"/producer,target=/app/producer/ \
--mount type=bind,source="$(pwd)"/scripts,target=/app/scripts/ \
flinox/faker-producer:latest 
```
Mapear a pasta **.keys** como /app/_key/


### Importante
A pasta **.keys** não pode estar no repositório, ou se estiver certifique-se de que esteja no .gitignore.


### Exemplo do comando para rodar o producer:
```
python3 /app/producer/producer.py <topic-name> --auto"
```

### Manipulando os dados gerados do producer
Para manipular os dados fake da mensagem antes de produzir no tópico use o parametro --change, Ex.:
```
python3 /app/producer/producer.py <topic-name> --auto --change
```

Parametros:

- topic, nome do topico que deseja produzir mensagens
- --auto, se deseja que as informações sejam preenchidas automaticamente!
- --no-auto, se deseja que as informações não sejam preenchidas automaticamente!
- --semi-auto', se deseja que as informações sejam preenchidas automaticamente com exceção do ID!
- --change', se deseja alterar as informações geradas antes de produzir as mensagens

## Produzindo mensagem
![producer](/images/producer.png)

### Consumindo mensagem produzida
![message](/images/message.png)