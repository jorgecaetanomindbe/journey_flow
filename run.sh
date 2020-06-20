#!/bin/bash

until nc -z ${BROKER_HOST} ${BROKER_PORT}; do
    echo "$(date) - waiting for broker..."
    sleep 1
done

until nc -z ${STORAGE_CRUD_HOST} ${STORAGE_CRUD_PORT}; do
    echo "$(date) - waiting for storage database..."
    sleep 1
done

until nc -z ${IN_MEMORY_STATE_HOST} ${IN_MEMORY_STATE_PORT}; do
    echo "$(date) - waiting for state database..."
    sleep 1
done

echo Starting Nameko.
exec nameko run --config flow/config.yaml flow.rpc