from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import AcaoPautaForm, ConsultaStatusForm, PautaItemForm
from .models import PautaItem, Reuniao
from .resumo import montar_resumo_status


def nova_pauta(request):
    proxima = Reuniao.proxima_aberta()

    if request.method == "POST":
        if not (proxima and proxima.esta_aberta):
            messages.error(
                request,
                "O prazo de submissão para a próxima reunião já encerrou. "
                "Aguarde a abertura da pauta da próxima reunião.",
            )
            return redirect("nova_pauta")

        form = PautaItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.reuniao = proxima
            item.save()
            messages.success(
                request,
                "Pauta enviada com sucesso! Guarde seu e-mail para acompanhar o andamento em "
                "“Acompanhar pauta”.",
            )
            return redirect(f"{reverse('acompanhar')}?{urlencode({'email': item.email_solicitante})}")
    else:
        form = PautaItemForm()

    return render(request, "pauta/nova_pauta.html", {"form": form, "proxima": proxima})


def acompanhar(request):
    form = ConsultaStatusForm(request.GET or None)
    itens = None
    if request.GET and form.is_valid():
        email = form.cleaned_data["email"]
        itens = (
            PautaItem.objects.filter(email_solicitante__iexact=email)
            .select_related("reuniao", "unidade")
            .order_by("-enviado_em")
        )

    return render(request, "pauta/acompanhar.html", {"form": form, "itens": itens})


@login_required
def gestao_painel(request):
    reunioes = Reuniao.objects.all()
    reuniao_id = request.GET.get("reuniao")

    if reuniao_id:
        reuniao_atual = get_object_or_404(Reuniao, pk=reuniao_id)
    else:
        reuniao_atual = Reuniao.proxima_aberta() or reunioes.first()

    itens = []
    if reuniao_atual:
        itens = list(reuniao_atual.itens.select_related("unidade").all())

    colunas = [
        (status_value, label, [item for item in itens if item.status == status_value])
        for status_value, label in PautaItem.STATUS_CHOICES
    ]

    return render(
        request,
        "pauta/gestao_painel.html",
        {"reunioes": reunioes, "reuniao_atual": reuniao_atual, "colunas": colunas},
    )


@login_required
def gestao_item_editar(request, pk):
    item = get_object_or_404(PautaItem, pk=pk)

    if request.method == "POST":
        form = AcaoPautaForm(request.POST, instance=item)
        if form.is_valid():
            novo = form.save(commit=False)
            if novo.status in (PautaItem.STATUS_EM_ANALISE, PautaItem.STATUS_ANALISADA) and not novo.analisado_em:
                novo.analisado_em = timezone.now()
            if (
                novo.status in (PautaItem.STATUS_APROVADA, PautaItem.STATUS_BACKLOG, PautaItem.STATUS_RECUSADA)
                and not novo.decidido_em
            ):
                novo.decidido_em = timezone.now()
            novo.save()
            messages.success(request, "Pauta atualizada. Copie o resumo abaixo para avisar o solicitante por e-mail.")
            return redirect("gestao_item_editar", pk=novo.pk)
    else:
        form = AcaoPautaForm(instance=item)

    resumo = montar_resumo_status(request, item)

    return render(request, "pauta/gestao_item_editar.html", {"form": form, "item": item, "resumo": resumo})


@login_required
def gestao_pauta_final(request, reuniao_id):
    reuniao = get_object_or_404(Reuniao, pk=reuniao_id)
    itens = (
        reuniao.itens.filter(status=PautaItem.STATUS_APROVADA)
        .select_related("unidade")
        .order_by("ordem_apresentacao", "enviado_em")
    )
    tempo_total = sum((item.tempo_confirmado_min or item.tempo_solicitado_min) for item in itens)

    return render(
        request,
        "pauta/pauta_final.html",
        {"reuniao": reuniao, "itens": itens, "tempo_total": tempo_total},
    )
