import datetime

from django.db import models
from django.urls import reverse
from django.utils import timezone


class Unidade(models.Model):
    TIPO_DIRETORIA = "DIRETORIA"
    TIPO_SECCIONAL = "SECCIONAL"
    TIPO_CENTRAL = "CENTRAL"
    TIPO_CHOICES = [
        (TIPO_DIRETORIA, "Diretoria"),
        (TIPO_SECCIONAL, "Seccional"),
        (TIPO_CENTRAL, "Unidade central (assessoramento/controle)"),
    ]

    nome = models.CharField(max_length=150)
    sigla = models.CharField(max_length=20)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_DIRETORIA)

    class Meta:
        ordering = ["tipo", "nome"]

    def __str__(self):
        return f"{self.sigla} - {self.nome}"


class Reuniao(models.Model):
    STATUS_ABERTA = "ABERTA"
    STATUS_FECHADA = "FECHADA"
    STATUS_REALIZADA = "REALIZADA"
    STATUS_CHOICES = [
        (STATUS_ABERTA, "Aberta para pauta"),
        (STATUS_FECHADA, "Fechada"),
        (STATUS_REALIZADA, "Realizada"),
    ]

    data = models.DateField(help_text="Data da reunião do Conselho Gestor (sexta-feira).")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ABERTA)

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"Conselho Gestor de {self.data.strftime('%d/%m/%Y')}"

    @property
    def prazo_submissao(self):
        return self.data - datetime.timedelta(days=7)

    @property
    def esta_aberta(self):
        return self.status == self.STATUS_ABERTA and timezone.localdate() <= self.prazo_submissao

    @classmethod
    def proxima_aberta(cls):
        return (
            cls.objects.filter(status=cls.STATUS_ABERTA, data__gte=timezone.localdate())
            .order_by("data")
            .first()
        )


class PautaItem(models.Model):
    TIPO_DELIBERATIVA = "DELIBERATIVA"
    TIPO_INFORMATIVA = "INFORMATIVA"
    TIPO_CHOICES = [
        (TIPO_DELIBERATIVA, "Deliberativa"),
        (TIPO_INFORMATIVA, "Informativa"),
    ]

    TEMPO_CHOICES = [
        (5, "5 minutos"),
        (10, "10 minutos"),
        (15, "15 minutos"),
        (30, "30 minutos"),
    ]

    STATUS_ENVIADA = "ENVIADA"
    STATUS_EM_ANALISE = "EM_ANALISE"
    STATUS_ANALISADA = "ANALISADA"
    STATUS_APROVADA = "APROVADA"
    STATUS_BACKLOG = "BACKLOG"
    STATUS_RECUSADA = "RECUSADA"
    STATUS_CHOICES = [
        (STATUS_ENVIADA, "Enviada"),
        (STATUS_EM_ANALISE, "Em análise pela assessoria"),
        (STATUS_ANALISADA, "Analisada, aguardando deliberação"),
        (STATUS_APROVADA, "Aprovada para o conselho"),
        (STATUS_BACKLOG, "Em backlog"),
        (STATUS_RECUSADA, "Recusada"),
    ]

    reuniao = models.ForeignKey(Reuniao, on_delete=models.PROTECT, related_name="itens")
    unidade = models.ForeignKey(Unidade, on_delete=models.PROTECT, related_name="pautas")

    nome_solicitante = models.CharField(max_length=150)
    email_solicitante = models.EmailField()

    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_DELIBERATIVA)
    contexto = models.TextField(help_text="Resumo do assunto para contextualizar o presidente.")
    link_sei = models.CharField(
        "Link ou nº SEI do documento", max_length=300, blank=True
    )

    tempo_solicitado_min = models.PositiveIntegerField("Tempo solicitado (min)", choices=TEMPO_CHOICES)
    tempo_confirmado_min = models.PositiveIntegerField(
        "Tempo confirmado (min)", blank=True, null=True
    )
    ordem_apresentacao = models.PositiveIntegerField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ENVIADA)
    parecer_assessoria = models.TextField(blank=True)
    observacao_decisao = models.TextField(blank=True)

    enviado_em = models.DateTimeField(auto_now_add=True)
    analisado_em = models.DateTimeField(blank=True, null=True)
    decidido_em = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ordem_apresentacao", "-enviado_em"]

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("acompanhar")
