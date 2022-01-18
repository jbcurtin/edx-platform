"""
Management command for enrolling a user into a course via the enrollment api
"""

import logging
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.management.base import BaseCommand
from openedx.core.djangoapps.enrollments.data import CourseEnrollmentExistsError
from openedx.core.djangoapps.enrollments.api import add_enrollment
from confluent_kafka import KafkaError, KafkaException, DeserializingConsumer
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.error import ValueSerializationError
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer


logger = logging.getLogger(__name__)

class TrackingEvent:
    """
    License events to be put on event bus
    """

    def __init__(self, *args, **kwargs):
        print(kwargs)
        self.license_uuid = kwargs.get('license_uuid', None)
        self.license_activation_key = kwargs.get('license_activation_key', None)
        self.previous_license_uuid = kwargs.get('previous_license_uuid', None)
        self.assigned_date = kwargs.get('assigned_date', None)
        self.activation_date = kwargs.get('activation_date', None)
        self.assigned_lms_user_id = kwargs.get('assigned_lms_user_id', None)
        self.assigned_email = kwargs.get('assigned_email', None)
        self.expiration_processed = kwargs.get('expiration_processed', None)
        self.auto_applied = kwargs.get('auto_applied', None)
        self.enterprise_customer_uuid = kwargs.get('enterprise_customer_uuid', None)
        self.enterprise_customer_slug = kwargs.get('enterprise_customer_slug', None)
        self.enterprise_customer_name = kwargs.get('enterprise_customer_name', None)
        self.customer_agreement_uuid = kwargs.get('customer_agreement_uuid', None)

    # Some paths will set assigned_lms_user_id to '' if empty, so need to allow strings in the schema
    TRACKING_EVENT_AVRO_SCHEMA = """
        {
            "namespace": "license_manager.apps.subscriptions",
            "name": "TrackingEvent",
            "type": "record",
            "fields": [
                {"name": "license_uuid", "type": "string"},
                {"name": "license_activation_key", "type": "string"},
                {"name": "previous_license_uuid", "type": "string"},
                {"name": "assigned_date", "type": "string"},
                {"name": "assigned_lms_user_id", "type": ["int", "string", "null"], "default": "null"},
                {"name": "assigned_email", "type":"string"},
                {"name": "expiration_processed", "type": "boolean"},
                {"name": "auto_applied", "type": "boolean", "default": "false"},
                {"name": "enterprise_customer_uuid", "type": ["string", "null"], "default": "null"},
                {"name": "customer_agreement_uuid", "type": ["string", "null"], "default": "null"},
                {"name": "enterprise_customer_slug", "type": ["string", "null"], "default": "null"},
                {"name": "enterprise_customer_name", "type": ["string", "null"], "default": "null"}
            ]
        }

    """

    @staticmethod
    def from_dict(dict_instance, ctx=None):  # pylint: disable=unused-argument
        return TrackingEvent(**dict_instance)

    @staticmethod
    def to_dict(obj, ctx=None):  # pylint: disable=unused-argument
        return {
            'enterprise_customer_uuid': obj.enterprise_customer_uuid,
            'customer_agreement_uuid': obj.customer_agreement_uuid,
            'enterprise_customer_slug': obj.enterprise_customer_slug,
            'enterprise_customer_name': obj.enterprise_customer_name,
            "license_uuid": obj.license_uuid,
            "license_activation_key": obj.license_activation_key,
            "previous_license_uuid": obj.previous_license_uuid,
            "assigned_date": obj.assigned_date,
            "activation_date": obj.activation_date,
            "assigned_lms_user_id": obj.assigned_lms_user_id,
            "assigned_email": (obj.assigned_email or ''),
            "expiration_processed": obj.expiration_processed,
            "auto_applied": (obj.auto_applied or False),
        }



class Command(BaseCommand):
    """
    Listen for license events from the event bus and log them
    """
    help = """
    This starts an event consumer
    """

    def handle(self, *args, **options):
        KAFKA_SCHEMA_REGISTRY_CONFIG = {
            'url': "",
            'basic.auth.user.info':
                ""
        }
        schema_registry_client = SchemaRegistryClient(KAFKA_SCHEMA_REGISTRY_CONFIG)

        value_deserializer = AvroDeserializer(schema_str=TrackingEvent.TRACKING_EVENT_AVRO_SCHEMA,
                                              schema_registry_client=schema_registry_client,
                                              from_dict=TrackingEvent.from_dict)

        consumer = DeserializingConsumer({
            'bootstrap.servers': "pkc-2396y.us-east-1.aws.confluent.cloud:9092",
            'group.id': 'license_manager_stage',
            'key.deserializer': StringDeserializer('utf-8'),
            'value.deserializer': value_deserializer,
            'auto.offset.reset': 'earliest',
            'sasl.mechanism': 'PLAIN',
            'security.protocol': 'SASL_SSL',
            'sasl.username': "",
            'sasl.password': "",
        })
        try:

            consumer.subscribe(["license-event-stage"])

            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None: continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        print('%% %s [%d] reached end at offset %d\n' %
                              (msg.topic(), msg.partition(), msg.offset()))
                    elif msg.error():
                        print(msg.error())
                else:
                    print("Received message:")
                    print(msg.key())
                    print(msg.value())
                    print(TrackingEvent.to_dict(msg.value()))

        finally:
            # Close down consumer to commit final offsets.
            consumer.close()
