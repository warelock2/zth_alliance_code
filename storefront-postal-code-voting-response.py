import boto3
import os
import requests
from botocore.exceptions import ClientError
from urllib.parse import parse_qs

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

# URL of the static HTML template - should be set in environment variables
TEMPLATE_URL = os.environ['TEMPLATE_URL']

def fetch_template():
    """Fetch the HTML template from external URL"""
    try:
        response = requests.get(TEMPLATE_URL)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching template: {str(e)}")
        return None

def increment_counter(postal_code):
    """Increment counter for given postal code in DynamoDB"""
    try:
        # Update expression to increment counter, creating item if it doesn't exist
        response = table.update_item(
            Key={'postal_code': postal_code},
            UpdateExpression='SET visit_count = if_not_exists(visit_count, :start) + :inc',
            ExpressionAttributeValues={
                ':inc': 1,
                ':start': 0
            },
            ReturnValues='UPDATED_NEW'
        )
        return int(response['Attributes']['visit_count'])
    except ClientError as e:
        print(f"Error updating DynamoDB: {str(e)}")
        return None

def lambda_handler(event, context):
    """Main Lambda handler function"""
    try:
        # Extract postal_code from query parameters
        query_parameters = event.get('queryStringParameters', {}) or {}
        postal_code = query_parameters.get('postal_code')

        if not postal_code:
            return {
                'statusCode': 400,
                'body': 'Missing postal_code parameter'
            }

        # Increment counter for this postal code
        visit_count = increment_counter(postal_code)
        if visit_count is None:
            return {
                'statusCode': 500,
                'body': 'Error updating counter'
            }

        # Fetch and process template
        template = fetch_template()
        if template is None:
            return {
                'statusCode': 500,
                'body': 'Error fetching template'
            }

        # Replace template tags with values
        # Assuming template uses {{postal_code}} and {{visit_count}} as placeholders
        processed_html = template.replace('{{postal_code}}', postal_code)
        processed_html = processed_html.replace('{{visit_count}}', str(visit_count))

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html'
            },
            'body': processed_html
        }

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Internal server error'
        }

