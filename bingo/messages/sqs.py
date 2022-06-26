import json
import os
from datetime import datetime
from typing import Dict

import boto3
import botocore


class SQSMeta(type):
    def __new__(mcs, name, bases, attrs):
        queue_name = attrs.get("name")

        if not queue_name and name != "SQSQueue":
            raise NotImplementedError(
                f"SQSQueue <{name}> incomplete. Missing attribute (name -> SQS queue name)."
            )

        cls = super().__new__(mcs, name, bases, attrs)

        if name != "SQSQueue":
            setattr(cls, "__client__", boto3.client("sqs"))

            try:
                response = cls.__client__.get_queue_url(QueueName=f"bingo_{queue_name}")
            except botocore.exceptions.ClientError as e:
                if (
                    e.response["Error"]["Code"]
                    == "AWS.SimpleQueueService.NonExistentQueue"
                ):
                    response = cls.__client__.create_queue(
                        QueueName=f"bingo_{queue_name}",
                        Attributes={
                            "ReceiveMessageWaitTimeSeconds": "20",
                            "VisibilityTimeout": "60",
                        },
                        tags={
                            "Owner": "bingo",
                            "Created": datetime.now().isoformat(),
                            "Maintainer": os.getenv(
                                "BINGO_SERVICE_NAME", "hackblitz/bingo"
                            ),
                            "DEAD_LETTER_QUEUE_NAME": f"bingo_dlq_{queue_name}",
                        },
                    )

            setattr(cls, "__url__", response["QueueUrl"])

        return cls


class SQSQueueSendPriority:
    HIGH = 0
    MEDIUM = 10
    LOW = 15


class SQSQueue(metaclass=SQSMeta):
    """
    Class to send/receive message via AWS SQS service.
    """

    PRIORITY = SQSQueueSendPriority.HIGH
    BATCH_SIZE = 1
    PRIORITIES = SQSQueueSendPriority

    @classmethod
    def send(cls, message: Dict, priority: int = PRIORITY) -> str:
        response = cls.__client__.send_message(
            QueueUrl=cls.__url__, MessageBody=json.dumps(message), DelaySeconds=priority
        )
        return response["MessageId"]

    @classmethod
    def receive(cls) -> None:
        response = cls.__client__.receive_message(
            QueueUrl=cls.__url__,
            AttributeNames=["SentTimestamp"],
            MaxNumberOfMessages=cls.BATCH_SIZE,
            MessageAttributeNames=["All"],
            WaitTimeSeconds=20,
        )

        for message in response.get("Messages", []):
            cls.message_handler(json.loads(message["Body"]))
            cls.__client__.delete_message(
                QueueUrl=cls.__url__, ReceiptHandle=message["ReceiptHandle"]
            )

    @classmethod
    def message_handler(cls, message: Dict) -> None:
        raise NotImplementedError(
            f"Message handler not implemented. Received message {str(message)}."
        )
