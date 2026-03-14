"""
Custom exception handler for DRF.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """Custom exception handler that normalizes error responses."""
    response = exception_handler(exc, context)

    if response is not None:
        # Normalize to always have an 'error' key at top level
        if isinstance(response.data, dict):
            if 'detail' in response.data and len(response.data) == 1:
                response.data = {'error': str(response.data['detail'])}
        elif isinstance(response.data, list):
            response.data = {'error': response.data}

    return response
