"""
CSV import service for survey invitations.
Supports both ',' and ';' separators (common in Brazilian Excel exports).
"""
import csv
import io
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {'nome', 'email', 'unidade', 'setor'}
OPTIONAL_COLUMNS = {'cargo'}

# Template CSV content for download
TEMPLATE_ROWS = [
    ['nome', 'email', 'unidade', 'setor', 'cargo'],
    ['João Silva', 'joao.silva@empresa.com.br', 'Matriz', 'Tecnologia', 'Analista'],
    ['Maria Souza', 'maria.souza@empresa.com.br', 'Filial SP', 'RH', 'Coordenadora'],
    ['Pedro Costa', 'pedro.costa@empresa.com.br', 'Matriz', 'Operações', ''],
]

SURVEY_INVITE_EMAIL_TEMPLATE = """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: {cor_primaria};">Pesquisa de Clima Psicossocial - {empresa_nome}</h2>
  <p>Olá, {nome}!</p>
  <p>Você foi convidado(a) a participar da nossa pesquisa de bem-estar e saúde no trabalho.</p>
  <p>Sua participação é <strong>voluntária, confidencial e anônima</strong>.
  As respostas são processadas de forma agregada e nunca identificam o respondente individualmente.</p>
  <p>Clique no link abaixo para responder a pesquisa:</p>
  <div style="text-align: center; margin: 30px 0;">
    <a href="{survey_url}"
       style="background-color: {cor_primaria}; color: white; padding: 15px 30px;
              text-decoration: none; border-radius: 5px; font-size: 16px;">
      Responder Pesquisa
    </a>
  </div>
  <p style="color: #666; font-size: 12px;">
    Este link é pessoal e válido até {data_expiracao}.
    Não compartilhe com outras pessoas.
  </p>
  <p style="color: #666; font-size: 12px;">
    Se não reconhece este e-mail, por favor, ignore-o.
  </p>
</div>
"""


def _detect_delimiter(content: str) -> str:
    """Auto-detect CSV delimiter: ';' (Brazilian Excel) or ',' (international)."""
    first_line = content.split('\n')[0] if content else ''
    semicolons = first_line.count(';')
    commas = first_line.count(',')
    return ';' if semicolons > commas else ','


class ImportService:
    """Validates and processes CSV files for invitation import."""

    def validate_csv(self, content: str) -> Tuple[bool, str, List[dict]]:
        """
        Validate CSV content and return parsed rows.
        Supports both ',' and ';' separators.

        Args:
            content: UTF-8 CSV string

        Returns:
            (is_valid, error_message, rows)
        """
        delimiter = _detect_delimiter(content)
        try:
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            fieldnames = {f.strip().lower() for f in (reader.fieldnames or [])}
        except Exception as e:
            return False, f'Erro ao ler CSV: {e}', []

        # Check required columns
        missing = REQUIRED_COLUMNS - fieldnames
        if missing:
            return (
                False,
                f'Colunas obrigatórias ausentes: {", ".join(sorted(missing))}. '
                f'Colunas encontradas: {", ".join(sorted(fieldnames))}',
                [],
            )

        rows = []
        errors = []

        for i, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            normalized = {k.strip().lower(): v.strip() for k, v in row.items() if k}

            for col in REQUIRED_COLUMNS:
                if not normalized.get(col):
                    errors.append(f'Linha {i}: campo "{col}" está vazio')

            if not errors:
                email = normalized.get('email', '')
                if '@' not in email or '.' not in email:
                    errors.append(f'Linha {i}: e-mail inválido: "{email}"')
                else:
                    rows.append({
                        'nome': normalized['nome'],
                        'email': normalized['email'].lower(),
                        'unidade': normalized['unidade'],
                        'setor': normalized['setor'],
                        'cargo': normalized.get('cargo', ''),
                    })

            if len(errors) >= 10:
                errors.append('... (mais erros encontrados, corrija os primeiros e tente novamente)')
                break

        if errors:
            return False, '\n'.join(errors), []

        if not rows:
            return False, 'CSV não contém linhas de dados.', []

        # Check for duplicate emails
        emails = [r['email'] for r in rows]
        if len(emails) != len(set(emails)):
            dupes = [e for e in emails if emails.count(e) > 1]
            return False, f'E-mails duplicados encontrados: {", ".join(set(dupes))}', []

        return True, '', rows

    def get_template_csv(self, separator: str = ';') -> str:
        """
        Generate a template CSV string for download.
        Uses ';' separator by default (Brazilian Excel compatibility).
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=separator)
        for row in TEMPLATE_ROWS:
            writer.writerow(row)
        return output.getvalue()

    def get_email_html(self, invitation, empresa) -> str:
        """Generate email HTML for an invitation."""
        data_exp = invitation.expires_at.strftime('%d/%m/%Y')
        nome = ''
        try:
            from services.crypto_service import crypto_service
            nome = crypto_service.decrypt(invitation.nome_encrypted)
        except Exception:
            nome = 'Colaborador(a)'

        return SURVEY_INVITE_EMAIL_TEMPLATE.format(
            empresa_nome=empresa.nome_app,
            nome=nome.split()[0] if nome else 'Colaborador(a)',
            survey_url=invitation.survey_url,
            cor_primaria=empresa.cor_primaria,
            data_expiracao=data_exp,
        )


import_service = ImportService()
