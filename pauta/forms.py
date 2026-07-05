from django import forms

from .models import PautaItem, Reuniao, Unidade


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + css).strip()


class PautaItemForm(BootstrapFormMixin, forms.ModelForm):
    unidade = forms.ModelChoiceField(
        queryset=Unidade.objects.all(),
        label="Diretoria/Seccional",
        empty_label="Selecione sua unidade",
    )

    class Meta:
        model = PautaItem
        fields = [
            "nome_solicitante",
            "email_solicitante",
            "unidade",
            "titulo",
            "tipo",
            "contexto",
            "link_sei",
            "tempo_solicitado_min",
        ]
        labels = {
            "nome_solicitante": "Seu nome",
            "email_solicitante": "Seu e-mail",
            "titulo": "Título da pauta",
            "tipo": "Natureza da pauta",
            "contexto": "Contexto para o presidente",
            "link_sei": "Link ou nº SEI do documento",
            "tempo_solicitado_min": "Tempo de apresentação solicitado (minutos)",
        }
        widgets = {
            "contexto": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Resuma o assunto e o que precisa ser decidido ou informado.",
                }
            ),
            "link_sei": forms.TextInput(attrs={"placeholder": "Ex: SEI 02001.000000/2026-00 ou link"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tempo_solicitado_min"].choices = [("", "Selecione o tempo")] + list(PautaItem.TEMPO_CHOICES)
        self._apply_bootstrap()


class ConsultaStatusForm(BootstrapFormMixin, forms.Form):
    email = forms.EmailField(label="Seu e-mail", widget=forms.EmailInput(attrs={"placeholder": "voce@ibama.gov.br"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class AcaoPautaForm(BootstrapFormMixin, forms.ModelForm):
    reuniao = forms.ModelChoiceField(
        queryset=Reuniao.objects.all().order_by("data"),
        label="Reunião",
        help_text="Mude aqui se for colocar em backlog para outra reunião.",
    )

    class Meta:
        model = PautaItem
        fields = [
            "reuniao",
            "status",
            "parecer_assessoria",
            "observacao_decisao",
            "tempo_confirmado_min",
            "ordem_apresentacao",
        ]
        widgets = {
            "parecer_assessoria": forms.Textarea(attrs={"rows": 2}),
            "observacao_decisao": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
