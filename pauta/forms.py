from django import forms
from django.utils import timezone

from .models import PautaItem, Reuniao, Unidade


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + css).strip()


class ReuniaoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        base = f"{obj.data.strftime('%d/%m/%Y')} (sexta-feira)"
        if not obj.esta_aberta:
            return f"{base} — prazo encerrado (menos de {Reuniao.PRAZO_MINIMO_DIAS} dias)"
        return base


class PautaItemForm(BootstrapFormMixin, forms.ModelForm):
    unidade = forms.ModelChoiceField(
        queryset=Unidade.objects.all(),
        label="Diretoria/Seccional",
        empty_label="Selecione sua unidade",
    )
    reuniao = ReuniaoChoiceField(
        queryset=Reuniao.objects.none(),
        label="Reunião desejada",
        empty_label="Selecione a data da reunião",
        help_text=(
            f"É preciso escolher uma reunião com pelo menos {Reuniao.PRAZO_MINIMO_DIAS} dias de "
            "antecedência, para dar tempo de análise da assessoria e despacho com o presidente."
        ),
    )

    class Meta:
        model = PautaItem
        fields = [
            "nome_solicitante",
            "email_solicitante",
            "unidade",
            "reuniao",
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
        Reuniao.garantir_proximas_semanas()
        self.fields["reuniao"].queryset = Reuniao.objects.filter(
            status=Reuniao.STATUS_ABERTA, data__gte=timezone.localdate()
        ).order_by("data")
        self.fields["tempo_solicitado_min"].choices = [("", "Selecione o tempo")] + list(PautaItem.TEMPO_CHOICES)
        self._apply_bootstrap()

    def clean_reuniao(self):
        reuniao = self.cleaned_data["reuniao"]
        if not reuniao.esta_aberta:
            raise forms.ValidationError(
                "Não há tempo hábil para análise e despacho com o presidente para a data "
                f"escolhida (menos de {Reuniao.PRAZO_MINIMO_DIAS} dias de antecedência). "
                "Escolha outra data de reunião."
            )
        return reuniao


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
        Reuniao.garantir_proximas_semanas()
        self.fields["reuniao"].queryset = Reuniao.objects.all().order_by("data")
        self._apply_bootstrap()
