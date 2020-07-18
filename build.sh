#! /bin/bash


docker build -t binary_django:0.1 -f Dockerfile.django .
docker build -t binary_mysql:0.1 -f Dockerfile.mysql .
