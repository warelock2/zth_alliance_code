import json
import os
import requests
import qrcode
import base64
from io import BytesIO
from urllib.parse import urlencode

def generate_qr_code(url):
    """Generate QR code and return as base64 encoded image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert PIL image to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def lambda_handler(event, context):
    try:
        # Get the postal_code from query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        postal_code = query_params.get('postal_code', '')

        if not postal_code:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'text/html'},
                'body': 'Missing postal_code parameter'
            }

        # Get base URL from environment variable
        base_url = os.environ.get('BASE_URL')
        if not base_url:
            raise ValueError("BASE_URL environment variable not set")

        # Get template URL from environment variable
        template_url = os.environ.get('TEMPLATE_URL')
        if not template_url:
            raise ValueError("TEMPLATE_URL environment variable not set")

        # Generate the target URL for QR code
        params = {'postal_code': postal_code}
        target_url = f"{base_url}?{urlencode(params)}"

        # Generate QR code
        qr_code_base64 = generate_qr_code(target_url)

        # Fetch HTML template
        response = requests.get(template_url)
        response.raise_for_status()
        html_template = response.text

        # Replace template variables
        replacements = {
            '{{POSTAL_CODE}}': postal_code,
            '{{QR_CODE}}': f'data:image/png;base64,{qr_code_base64}',
            '{{TARGET_URL}}': target_url
        }

        for key, value in replacements.items():
            html_template = html_template.replace(key, value)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html',
                'Cache-Control': 'no-cache'
            },
            'body': html_template
        }

    except requests.exceptions.RequestException as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/html'},
            'body': f'Error fetching template: {str(e)}'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/html'},
            'body': f'Internal error: {str(e)}'
        }


