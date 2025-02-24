import os
from contextlib import contextmanager
from typing import Generator

import json
from kafka import KafkaProducer


def check_and_get_kafka_creds() -> tuple[str, str, str, str]:
    fqdn = os.getenv("VIBEAI_KAFKA_FQDN")
    user = os.getenv("VIBEAI_KAFKA_USER")
    password = os.getenv("VIBEAI_KAFKA_PASSWORD")
    kafka_topic_name = os.getenv("VIBEAI_KAFKA_TOPIC_NAME")
    if not all((fqdn, user, password, kafka_topic_name)):
        raise ValueError("Not all kafka credentials specified.")
    return fqdn, user, password, kafka_topic_name


@contextmanager
def kafka_manager() -> Generator[tuple[KafkaProducer, str], any, any]:
    fqdn, user, password, kafka_topic_name = check_and_get_kafka_creds()
    producer = KafkaProducer(
        bootstrap_servers=f"{fqdn}:9091",
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        sasl_plain_username=user,
        sasl_plain_password=password,
        ssl_cafile="/usr/local/share/ca-certificates/Yandex/YandexInternalRootCA.crt",
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    )
    try:
        yield producer, kafka_topic_name
    finally:
        producer.flush()
        producer.close()


def push_to_kafka(
        data: dict,
        kafka_producer: KafkaProducer,
        topic_name: str,
) -> None:
    kafka_producer.send(topic_name, data)
    kafka_producer.flush()


def push_inference_completed_msg(
        chat_id: int,
        job_id: str,
        upload_path: str,
        kafka_producer: KafkaProducer,
        topic_name: str,
) -> None:
    data = {
        "chat_id": chat_id,
        "rp_job_id": job_id,
        "upload_path": upload_path,
    }
    push_to_kafka(data, kafka_producer, topic_name)