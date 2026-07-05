from django.contrib import admin

from .models import PautaItem, Reuniao, Unidade


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ("sigla", "nome", "tipo")
    list_filter = ("tipo",)
    search_fields = ("nome", "sigla")


@admin.register(Reuniao)
class ReuniaoAdmin(admin.ModelAdmin):
    list_display = ("data", "status", "prazo_submissao")
    list_filter = ("status",)
    ordering = ("-data",)


@admin.register(PautaItem)
class PautaItemAdmin(admin.ModelAdmin):
    list_display = ("titulo", "unidade", "reuniao", "tipo", "status", "enviado_em")
    list_filter = ("status", "tipo", "reuniao")
    search_fields = ("titulo", "nome_solicitante", "email_solicitante")
