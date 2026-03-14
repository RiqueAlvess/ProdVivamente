from django.contrib import admin
from .models import Unidade, Setor, Cargo


class SetorInline(admin.TabularInline):
    model = Setor
    extra = 1


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'get_setor_count', 'created_at']
    list_filter = ['empresa']
    search_fields = ['nome', 'empresa__nome']
    inlines = [SetorInline]

    def get_setor_count(self, obj):
        return obj.setores.count()
    get_setor_count.short_description = 'Setores'


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'unidade', 'get_empresa', 'created_at']
    list_filter = ['unidade__empresa']
    search_fields = ['nome', 'unidade__nome', 'unidade__empresa__nome']

    def get_empresa(self, obj):
        return obj.unidade.empresa.nome
    get_empresa.short_description = 'Empresa'


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'created_at']
    list_filter = ['empresa']
    search_fields = ['nome', 'empresa__nome']
