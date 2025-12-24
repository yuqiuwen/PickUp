#!/bin/bash


docker build -t pickup .
docker compose -f docker-compose.dev.yml up -d
