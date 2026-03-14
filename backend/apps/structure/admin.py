from django.contrib import admin
from .models import Unidade, Setor, Cargo


class SetorInline(admin.TabularInline):
    model = Setor
    extra = 1


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ['nome', 'get_setor_count', 'created_at']
    list_filter = []
    search_fields = ['nome']
    inlines = [SetorInline]

    def get_setor_count(self, obj):
        return obj.setores.count()
    get_setor_count.short_description = 'Setores'


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'unidade', 'created_at']
    list_filter = ['unidade']
    search_fields = ['nome', 'unidade__nome']


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'created_at']
    list_filter = []
    search_fields = ['nome']
