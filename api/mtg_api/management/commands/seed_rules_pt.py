"""
Importa as Regras Abrangentes em português para a tabela `rules`.

A tradução oficial é mantida pelo projeto Translated Rules dos juízes de Magic:
https://blogs.magicjudges.org/translatedrules/?lang=pt_br

ATENÇÃO: a última tradução para português disponível é de 03/05/2019. O texto
em inglês continua sendo atualizado a cada coleção, então mecânicas novas não
estarão aqui. Para as regras atuais em inglês, use `seed_rules`.

Uso:
    python manage.py seed_rules_pt                    # baixa a versão padrão
    python manage.py seed_rules_pt --file regras.pdf  # a partir de um arquivo
    python manage.py seed_rules_pt --url https://...  # de outra URL
"""
import re
import urllib.request

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

URL_PADRAO = ('https://blogs.magicjudges.org/translatedrules/files/2019/05/'
              'MagicCompRules_20190503_PT.pdf')
HEADERS = {'User-Agent': 'MTGNexus-Seed/1.0'}

# Ex.: "100.1a Estas regras de Magic aplicam-se a..."
REGRA_RE = re.compile(r'^(\d{3}\.\d+[a-z]?)\.?\s+(.+)$')


class Command(BaseCommand):
    help = 'Importa as Regras Abrangentes em português (tradução dos juízes).'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default='',
                            help='Caminho de um PDF ou TXT local.')
        parser.add_argument('--url', type=str, default=URL_PADRAO,
                            help='URL do documento (PDF ou TXT).')
        parser.add_argument('--keep-english', action='store_true',
                            help='Mantém as regras em inglês já gravadas.')

    def handle(self, *args, **options):
        origem = options['file'] or options['url']
        self.stdout.write(f'Lendo regras de {origem}')

        if options['file']:
            with open(options['file'], 'rb') as arquivo:
                bruto = arquivo.read()
        else:
            try:
                pedido = urllib.request.Request(options['url'], headers=HEADERS)
                with urllib.request.urlopen(pedido, timeout=90) as resposta:
                    bruto = resposta.read()
            except Exception as exc:
                raise CommandError(
                    f'Não foi possível baixar o documento ({exc}). '
                    'Baixe o PDF manualmente em '
                    'https://blogs.magicjudges.org/translatedrules/?lang=pt_br '
                    'e rode com --file.'
                ) from None

        texto = self.extrair_texto(bruto, origem)
        regras = self.parsear(texto)

        if not regras:
            raise CommandError(
                'Nenhuma regra reconhecida no documento. Confira se o arquivo é '
                'mesmo as Regras Abrangentes.'
            )

        if not options['keep_english']:
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM rules')

        with connection.cursor() as cursor:
            cursor.executemany(
                'REPLACE INTO rules (rule_number, rule_text, chapter_id) VALUES (%s, %s, %s)',
                regras,
            )

        self.stdout.write(self.style.SUCCESS(f'{len(regras)} regras importadas em português.'))
        self.stdout.write(self.style.WARNING(
            'Lembrete: a tradução para português está congelada em 03/05/2019; '
            'mecânicas posteriores não constam.'))

    def extrair_texto(self, bruto, origem):
        if bruto[:4] != b'%PDF' and not str(origem).lower().endswith('.pdf'):
            return bruto.decode('utf-8-sig', errors='ignore')

        try:
            import pdfplumber
        except ImportError:
            raise CommandError(
                'Leitura de PDF requer o pacote pdfplumber (já incluído no '
                'requirements.txt). Reconstrua a imagem: docker compose build api'
            ) from None

        import io
        paginas = []
        with pdfplumber.open(io.BytesIO(bruto)) as pdf:
            total = len(pdf.pages)
            for indice, pagina in enumerate(pdf.pages, start=1):
                paginas.append(pagina.extract_text() or '')
                if indice % 25 == 0:
                    self.stdout.write(f'  {indice}/{total} páginas lidas...')
        return '\n'.join(paginas)

    def parsear(self, texto):
        """
        Junta as linhas de cada regra: no PDF uma regra costuma quebrar em
        várias linhas, e só a primeira começa com o número.
        """
        regras, vistas = [], set()
        numero_atual, partes = None, []

        def fechar():
            if numero_atual and partes:
                corpo = ' '.join(partes).strip()
                corpo = re.sub(r'\s{2,}', ' ', corpo)
                if corpo and numero_atual not in vistas:
                    vistas.add(numero_atual)
                    regras.append((numero_atual, corpo, numero_atual.split('.')[0][0]))

        for linha in texto.splitlines():
            linha = linha.strip()
            if not linha:
                continue
            achou = REGRA_RE.match(linha)
            if achou:
                fechar()
                numero_atual, partes = achou.group(1), [achou.group(2).strip()]
            elif numero_atual and not re.match(r'^\d+$', linha):
                partes.append(linha)   # continuação da regra anterior
        fechar()
        return regras
