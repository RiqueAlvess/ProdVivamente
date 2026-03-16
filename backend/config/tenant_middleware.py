"""
TenantFromHeaderMiddleware

Fallback middleware for development: when the request comes from a domain
that resolves to the public schema (e.g. localhost), check for the header
  X-Tenant-Schema: <schema_name>
and switch to that tenant's schema for the duration of the request.

This allows the frontend running at localhost:3000 to target a specific
tenant without needing subdomain DNS setup.

Place this AFTER TenantMainMiddleware in the middleware stack.
"""
from django.db import connection
from django_tenants.utils import get_tenant_model, tenant_context


class TenantFromHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        schema_header = request.headers.get('X-Tenant-Schema', '').strip().lower()

        if schema_header and connection.schema_name == 'public':
            TenantModel = get_tenant_model()
            try:
                tenant = TenantModel.objects.get(schema_name=schema_header, ativo=True)
                with tenant_context(tenant):
                    request.tenant = tenant
                    response = self.get_response(request)
                return response
            except TenantModel.DoesNotExist:
                pass

        return self.get_response(request)
