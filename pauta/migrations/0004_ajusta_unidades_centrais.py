# Correção da migration 0002: não existe Superintendência do Ibama no Distrito Federal (a sede
# fica no DF, mas não há uma Supes-DF decentralizada — restam as 26 Supes estaduais). Também
# adiciona os órgãos de assistência direta e imediata à presidência, ligados diretamente à
# cúpula no mesmo nível hierárquico das diretorias/superintendências: Procuradoria Federal
# Especializada, Auditoria Interna, Corregedoria, Ouvidoria e Assessoria de Gestão Estratégica.
# Fontes: https://www.gov.br/ibama/pt-br/composicao/estrutura e
# https://www.gov.br/ibama/pt-br/composicao/quem-e-quem

from django.db import migrations

UNIDADES_CENTRAIS = [
    ("PFE", "Procuradoria Federal Especializada junto ao Ibama"),
    ("Audit", "Auditoria Interna"),
    ("Coger", "Corregedoria"),
    ("Ouv", "Ouvidoria"),
    ("Agest", "Assessoria de Gestão Estratégica"),
]


def ajustar(apps, schema_editor):
    Unidade = apps.get_model("pauta", "Unidade")

    Unidade.objects.filter(sigla="Supes-DF").delete()

    for sigla, nome in UNIDADES_CENTRAIS:
        Unidade.objects.get_or_create(sigla=sigla, defaults={"nome": nome, "tipo": "CENTRAL"})


def reverter(apps, schema_editor):
    Unidade = apps.get_model("pauta", "Unidade")

    siglas = [sigla for sigla, _ in UNIDADES_CENTRAIS]
    Unidade.objects.filter(sigla__in=siglas).delete()

    Unidade.objects.get_or_create(
        sigla="Supes-DF",
        defaults={"nome": "Superintendência do Ibama - Distrito Federal", "tipo": "SECCIONAL"},
    )


class Migration(migrations.Migration):
    dependencies = [("pauta", "0003_alter_unidade_tipo")]

    operations = [migrations.RunPython(ajustar, reverter)]
