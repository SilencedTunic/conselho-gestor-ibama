from urllib.parse import quote, urlencode

from django.urls import reverse


def montar_resumo_status(request, item):
    """Texto pronto para a assessoria copiar e colar (ou abrir direto) no próprio e-mail,
    avisando o solicitante sobre o status atual da pauta."""
    link = request.build_absolute_uri(
        reverse("acompanhar") + "?" + urlencode({"email": item.email_solicitante})
    )
    assunto = f'Conselho Gestor: pauta "{item.titulo}" — {item.get_status_display()}'

    linhas = [
        f"Olá, {item.nome_solicitante}.",
        "",
        f'O status da sua pauta "{item.titulo}" foi atualizado:',
        "",
        f"Novo status: {item.get_status_display()}",
    ]
    if item.parecer_assessoria:
        linhas += ["", f"Parecer da assessoria: {item.parecer_assessoria}"]
    if item.observacao_decisao:
        linhas += ["", f"Decisão do presidente: {item.observacao_decisao}"]
    linhas += [
        "",
        f"Acompanhe todos os detalhes em:\n{link}",
        "",
        "Atenciosamente,\nAssessoria da Presidência – Ibama",
    ]
    corpo = "\n".join(linhas)

    return {
        "destinatario": item.email_solicitante,
        "assunto": assunto,
        "corpo": corpo,
        "texto_completo": f"Para: {item.email_solicitante}\nAssunto: {assunto}\n\n{corpo}",
        "mailto_href": f"mailto:{item.email_solicitante}?subject={quote(assunto)}&body={quote(corpo)}",
    }
