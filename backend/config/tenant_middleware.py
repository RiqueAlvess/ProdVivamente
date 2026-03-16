"""
TenantFromHeaderMiddleware

Fallback middleware for development: when the request comes from a domain
that resolves to the public schema (e.g. localhost), check for the header
  X-Tenant-Schema: <schema_name>
and switch to that tenant's schema for the duration of the request.

If no header is provided and the request is an API call outside public
endpoints, falls back to the first active tenant (single-tenant convenience).

Place this AFTER TenantMainMiddleware in the middleware stack.
"""
import logging
from django.db import connection
from django_tenants.utils import get_tenant_model, tenant_context

logger = logging.getLogger(__name__)

# Public-schema-only paths that must NOT be redirected to a tenant schema
PUBLIC_PREFIXES = ('/api/tenants/', '/api/schema/', '/api/docs/', '/api/redoc/', '/admin/')


class TenantFromHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only act when currently on the public schema
        if connection.schema_name != 'public':
            return self.get_response(request)

        schema_header = request.headers.get('X-Tenant-Schema', '').strip().lower()
        TenantModel = get_tenant_model()

        if schema_header:
            # Explicit schema requested via header
            try:
                tenant = TenantModel.objects.get(schema_name=schema_header, ativo=True)
                with tenant_context(tenant):
                    request.tenant = tenant
                    return self.get_response(request)
            except TenantModel.DoesNotExist:
                logger.warning(
                    'X-Tenant-Schema "%s" not found; continuing on public schema.',
                    schema_header,
                )
        elif request.path.startswith('/api/') and not any(
            request.path.startswith(p) for p in PUBLIC_PREFIXES
        ):
            # No header for a non-public API call → fall back to first active tenant.
            # Prevents 404s in development and single-tenant deployments.
            try:
                tenant = TenantModel.objects.exclude(schema_name='public').filter(ativo=True).first()
                if tenant:
                    with tenant_context(tenant):
                        request.tenant = tenant
                        return self.get_response(request)
            except Exception as exc:
                logger.debug('Tenant auto-fallback failed: %s', exc)

        return self.get_response(request)
