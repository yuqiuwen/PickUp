#!/bin/bash

echo "Starting build process..."

docker build -t pickup .
docker compose up -d


echo "Build and deployment completed successfully!"
