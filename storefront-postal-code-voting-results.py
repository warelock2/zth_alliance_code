import os
import json
import boto3
from boto3.dynamodb.conditions import Key
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    # Get table name from environment variable
    table_name = os.environ.get('DYNAMODB_TABLE')
    if not table_name:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'DYNAMODB_TABLE environment variable not set'})
        }

    try:
        # Initialize DynamoDB resource
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)

        # Perform query on the table
        response = table.scan(
            ProjectionExpression='postal_code, visit_count',
            Select='SPECIFIC_ATTRIBUTES'
        )

        # Sort the items by visit_count in descending order
        items = sorted(
            response['Items'],
            key=lambda x: int(x['visit_count']),
            reverse=True
        )

        # Format the results as a table
        if items:
            # Calculate column widths
            visit_width = max(len(str(item['visit_count'])) for item in items)
            visit_width = max(visit_width, len('Visit Count'))
            postal_width = max(len(item['postal_code']) for item in items)
            postal_width = max(postal_width, len('Postal Code'))

            # Create table header
            table_output = [
                f"{'Visit Count'.ljust(visit_width)} | {'Postal Code'.ljust(postal_width)}",
                f"{'-' * visit_width}-+-{'-' * postal_width}"
            ]

            # Add table rows
            for item in items:
                table_output.append(
                    f"{str(item['visit_count']).ljust(visit_width)} | {item['postal_code'].ljust(postal_width)}"
                )

            formatted_table = '\n'.join(table_output)

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/plain'
                },
                'body': formatted_table
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No records found'})
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

