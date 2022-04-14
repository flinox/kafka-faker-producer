#!/bin/bash

docker build -t flinox/faker-producer:latest .

docker run --rm -it --hostname faker-producer --name faker-producer \
--mount type=bind,source="$(pwd)"/.keys,target=/app/_key/ \
--mount type=bind,source="$(pwd)"/producer,target=/app/producer/ \
--mount type=bind,source="$(pwd)"/scripts,target=/app/scripts/ \
-e TZ=America/Sao_Paulo \
--security-opt label=disable \
flinox/faker-producer:latest 
