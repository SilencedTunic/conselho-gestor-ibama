from django.core.management.base import BaseCommand
from django.utils import timezone

from pauta.models import PautaItem, Reuniao, Unidade


class Command(BaseCommand):
    help = (
        "Cria 5 pautas de demonstração (uma por diretoria: Dilic, Diqua, DBFlo, Dipro, Diplan) "
        "numa reunião futura válida, para simular a análise/deliberação no painel de gestão. "
        "Uso local/manual, não é chamado no deploy. Idempotente: identifica cada pauta pelo "
        "título e não duplica em reruns."
    )

    ITENS_DEMO = [
        {
            "sigla_unidade": "Dilic",
            "nome_solicitante": "Marina Alves Costa",
            "email_solicitante": "marina.costa@ibama.gov.br",
            "titulo": "Deliberação sobre a Licença Prévia do Complexo Eólico Offshore Costa Norte",
            "tipo": PautaItem.TIPO_DELIBERATIVA,
            "tempo_solicitado_min": 15,
            "link_sei": "SEI 02001.004521/2026-77",
            "contexto": (
                "O processo de licenciamento do Complexo Eólico Offshore Costa Norte concluiu "
                "audiências públicas e pareceres técnicos (EIA/RIMA) sem apontamentos "
                "impeditivos, mas há divergência entre a área técnica e a Procuradoria Federal "
                "Especializada quanto às condicionantes de monitoramento de fauna marinha. A "
                "diretoria solicita deliberação do presidente para destravar a emissão da "
                "Licença Prévia, dado o interesse estratégico do empreendimento para a matriz "
                "energética e o prazo contratual do investidor."
            ),
        },
        {
            "sigla_unidade": "Diqua",
            "nome_solicitante": "Rodrigo Nunes Barbosa",
            "email_solicitante": "rodrigo.barbosa@ibama.gov.br",
            "titulo": "Aprovação de nova norma técnica para registro de agrotóxicos de menor risco",
            "tipo": PautaItem.TIPO_DELIBERATIVA,
            "tempo_solicitado_min": 10,
            "link_sei": "SEI 02001.008832/2026-04",
            "contexto": (
                "A minuta de instrução normativa que cria rito simplificado de registro para "
                "agrotóxicos classificados como de menor risco ambiental já passou por consulta "
                "pública e ajuste redacional conjunto com o Mapa e a Anvisa. Falta apenas o aval "
                "do presidente para publicação, já que a medida reduz o passivo de processos "
                "represados na Diqua sem abrir mão da avaliação técnica de risco."
            ),
        },
        {
            "sigla_unidade": "DBFlo",
            "nome_solicitante": "Juliana Ferreira Lima",
            "email_solicitante": "juliana.lima@ibama.gov.br",
            "titulo": "Balanço da temporada de queimadas 2026 e plano de prevenção para o próximo período seco",
            "tipo": PautaItem.TIPO_INFORMATIVA,
            "tempo_solicitado_min": 10,
            "link_sei": "SEI 02001.011290/2026-55",
            "contexto": (
                "Apresentação dos números consolidados de focos de incêndio e área queimada na "
                "temporada 2026, comparados aos últimos 5 anos, com destaque para a redução nas "
                "unidades de conservação monitoradas pelo Prevfogo. A diretoria quer informar o "
                "presidente sobre os resultados antes de divulgar o plano de prevenção do "
                "próximo período seco, que envolve reforço de brigadas em áreas críticas do "
                "Cerrado e da Amazônia."
            ),
        },
        {
            "sigla_unidade": "Dipro",
            "nome_solicitante": "Carlos Eduardo Martins",
            "email_solicitante": "carlos.martins@ibama.gov.br",
            "titulo": "Resultados da Operação Guardiões da Floresta e proposta de reforço logístico",
            "tipo": PautaItem.TIPO_DELIBERATIVA,
            "tempo_solicitado_min": 30,
            "link_sei": "SEI 02001.015678/2026-22",
            "contexto": (
                "A operação de fiscalização integrada contra garimpo e desmatamento ilegal na "
                "Terra Indígena Yanomami e entorno resultou em embargo de área recorde e "
                "apreensão de maquinário pesado, mas a equipe de campo relata risco operacional "
                "crescente e desgaste de aeronaves fretadas. A diretoria solicita deliberação do "
                "presidente sobre reforço orçamentário emergencial para manter o ritmo das "
                "operações no segundo semestre."
            ),
        },
        {
            "sigla_unidade": "Diplan",
            "nome_solicitante": "Fernanda Souza Ribeiro",
            "email_solicitante": "fernanda.ribeiro@ibama.gov.br",
            "titulo": "Revisão do plano de contratações de TI para 2027",
            "tipo": PautaItem.TIPO_DELIBERATIVA,
            "tempo_solicitado_min": 15,
            "link_sei": "SEI 02001.019943/2026-10",
            "contexto": (
                "O Plano Anual de Contratações de TI para 2027 prevê a renovação de licenças de "
                "sistemas corporativos e a contratação de consultoria para modernização do "
                "SISLIC, mas o orçamento disponível cobre apenas 70% do valor estimado. A "
                "diretoria pede deliberação do presidente sobre priorização dos itens, já que "
                "postergar a renovação de licenças críticas pode interromper serviços em "
                "produção a partir de janeiro."
            ),
        },
    ]

    def handle(self, *args, **options):
        reuniao = self._escolher_reuniao()
        if not reuniao:
            self.stdout.write(self.style.ERROR(
                "Não foi possível localizar uma reunião futura válida (aberta e com pelo menos "
                f"{Reuniao.PRAZO_MINIMO_DIAS} dias de antecedência)."
            ))
            return

        criados = 0
        for dados in self.ITENS_DEMO:
            unidade = Unidade.objects.filter(sigla=dados["sigla_unidade"]).first()
            if not unidade:
                self.stdout.write(self.style.WARNING(
                    f"Unidade '{dados['sigla_unidade']}' não encontrada, pulando '{dados['titulo']}'."
                ))
                continue

            _, created = PautaItem.objects.get_or_create(
                titulo=dados["titulo"],
                defaults={
                    "reuniao": reuniao,
                    "unidade": unidade,
                    "nome_solicitante": dados["nome_solicitante"],
                    "email_solicitante": dados["email_solicitante"],
                    "tipo": dados["tipo"],
                    "contexto": dados["contexto"],
                    "link_sei": dados["link_sei"],
                    "tempo_solicitado_min": dados["tempo_solicitado_min"],
                },
            )
            if created:
                criados += 1

        self.stdout.write(self.style.SUCCESS(
            f"{criados} pauta(s) demo criada(s) (de {len(self.ITENS_DEMO)} definidas) para a "
            f"reunião de {reuniao.data.strftime('%d/%m/%Y')}."
        ))

    def _escolher_reuniao(self):
        Reuniao.garantir_proximas_semanas()
        hoje = timezone.localdate()
        candidatas = Reuniao.objects.filter(
            status=Reuniao.STATUS_ABERTA, data__gte=hoje
        ).order_by("data")
        return next((r for r in candidatas if r.esta_aberta), None)
