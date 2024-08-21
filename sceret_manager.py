import json
import boto3
from base64 import b64decode
from botocore.config import Config
import logging
from botocore.exceptions import ClientError


def read_aws_secret(secret_name, aws_region='us-west-2', json_type=True):
    """
    this function is to read secrets from secrets manager
    :param secret_name:
    :param aws_region:
    :param json_type:
    :return:
    """
    config = Config(
        retries={
            'max_attempts': 20,
            'mode': 'standard'
        }
    )
    session = boto3.session.Session()
    secrets_client = session.client(service_name='secretsmanager',
                                    region_name=aws_region,
                                    config=config)
    try:
        get_secret_value_response = secrets_client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        return f"The code was not returned or is not accessible1 {e} ", 403
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logging.error("The requested secret " + secret_name + " was not found")
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            logging.error("The request was invalid due to:", e)
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            logging.error("The request had invalid params:", e)
        elif e.response['Error']['Code'] == 'DecryptionFailureException':
            logging.error('Failed to decrypt secret:', e)
    else:
        print(get_secret_value_response)
        return f"The code was not returned or is not accessible1 {get_secret_value_response} ", 403
        if 'SecretString' in get_secret_value_response:
            text_secret_data = get_secret_value_response['SecretString']
            if json_type:
                return json.loads(text_secret_data)
            else:
                return text_secret_data
        else:
            return b64decode(get_secret_value_response['SecretBinary'])