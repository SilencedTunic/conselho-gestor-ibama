# Dados extraídos do Regimento Interno do Ibama
# (https://www.gov.br/ibama/pt-br/acesso-a-informacao/institucional/regimento-interno-do-ibama,
# Portaria Ibama nº 73/2025) e da lista pública de Superintendências (Supes) do Ibama nos estados
# (https://www.gov.br/ibama/pt-br/composicao/quem-e-quem/ibama-nos-estados).

from django.db import migrations

DIRETORIAS = [
    ("Dilic", "Diretoria de Licenciamento Ambiental"),
    ("Diqua", "Diretoria de Qualidade Ambiental"),
    ("DBFlo", "Diretoria de Biodiversidade e Florestas"),
    ("Dipro", "Diretoria de Proteção Ambiental"),
    ("Diplan", "Diretoria de Planejamento, Administração e Logística"),
]

ESTADOS = [
    ("AC", "Acre"), ("AL", "Alagoas"), ("AP", "Amapá"), ("AM", "Amazonas"),
    ("BA", "Bahia"), ("CE", "Ceará"), ("DF", "Distrito Federal"), ("ES", "Espírito Santo"),
    ("GO", "Goiás"), ("MA", "Maranhão"), ("MT", "Mato Grosso"), ("MS", "Mato Grosso do Sul"),
    ("MG", "Minas Gerais"), ("PA", "Pará"), ("PB", "Paraíba"), ("PR", "Paraná"),
    ("PE", "Pernambuco"), ("PI", "Piauí"), ("RJ", "Rio de Janeiro"), ("RN", "Rio Grande do Norte"),
    ("RS", "Rio Grande do Sul"), ("RO", "Rondônia"), ("RR", "Roraima"), ("SC", "Santa Catarina"),
    ("SP", "São Paulo"), ("SE", "Sergipe"), ("TO", "Tocantins"),
]


def seed_unidades(apps, schema_editor):
    Unidade = apps.get_model("pauta", "Unidade")

    for sigla, nome in DIRETORIAS:
        Unidade.objects.get_or_create(sigla=sigla, defaults={"nome": nome, "tipo": "DIRETORIA"})

    for uf, estado in ESTADOS:
        Unidade.objects.get_or_create(
            sigla=f"Supes-{uf}",
            defaults={"nome": f"Superintendência do Ibama - {estado}", "tipo": "SECCIONAL"},
        )


def remove_unidades(apps, schema_editor):
    Unidade = apps.get_model("pauta", "Unidade")
    siglas = [sigla for sigla, _ in DIRETORIAS] + [f"Supes-{uf}" for uf, _ in ESTADOS]
    Unidade.objects.filter(sigla__in=siglas).delete()


class Migration(migrations.Migration):
    dependencies = [("pauta", "0001_initial")]

    operations = [migrations.RunPython(seed_unidades, remove_unidades)]
