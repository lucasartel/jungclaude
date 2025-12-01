"""
pdf_generator.py - Gerador de Relatórios PDF Psicométricos
============================================================

Gera relatórios profissionais em PDF com:
- Big Five (OCEAN)
- Inteligência Emocional (EQ)
- VARK (Estilos de Aprendizagem)
- Valores de Schwartz

Autor: Sistema Jung
Data: 2025-11-29
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class PsychometricPDFGenerator:
    """Gerador de relatórios PDF psicométricos profissionais"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Cria estilos customizados para o PDF"""

        # Título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#283593'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))

        # Seção
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#3949ab'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))

        # Corpo de texto
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=10
        ))

        # Evidências (citações)
        self.styles.add(ParagraphStyle(
            name='Evidence',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#424242'),
            leftIndent=20,
            rightIndent=20,
            spaceAfter=8,
            fontName='Helvetica-Oblique',
            borderPadding=5,
            borderColor=colors.HexColor('#e0e0e0'),
            borderWidth=1
        ))

    def _add_header(self, canvas_obj, doc):
        """Adiciona cabeçalho em todas as páginas"""
        canvas_obj.saveState()

        # Linha superior
        canvas_obj.setStrokeColor(colors.HexColor('#3949ab'))
        canvas_obj.setLineWidth(2)
        canvas_obj.line(50, letter[1] - 50, letter[0] - 50, letter[1] - 50)

        # Texto do cabeçalho
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.setFillColor(colors.HexColor('#1a237e'))
        canvas_obj.drawString(50, letter[1] - 35, "Jung AI - Relatório Psicométrico")

        # Data no canto direito
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.HexColor('#757575'))
        canvas_obj.drawRightString(
            letter[0] - 50,
            letter[1] - 35,
            f"Gerado em: {datetime.now().strftime('%d/%m/%Y')}"
        )

        canvas_obj.restoreState()

    def _add_footer(self, canvas_obj, doc):
        """Adiciona rodapé em todas as páginas"""
        canvas_obj.saveState()

        # Linha inferior
        canvas_obj.setStrokeColor(colors.HexColor('#e0e0e0'))
        canvas_obj.setLineWidth(1)
        canvas_obj.line(50, 50, letter[0] - 50, 50)

        # Número da página
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.HexColor('#757575'))
        page_num = canvas_obj.getPageNumber()
        canvas_obj.drawCentredString(letter[0] / 2, 35, f"Página {page_num}")

        # Nota de confidencialidade
        canvas_obj.setFont('Helvetica-Oblique', 7)
        canvas_obj.drawCentredString(
            letter[0] / 2,
            20,
            "Documento Confidencial - Uso restrito ao titular dos dados"
        )

        canvas_obj.restoreState()

    def _create_cover_page(self, user_name: str, total_conversations: int):
        """Cria página de capa do relatório"""
        elements = []

        # Espaçamento inicial
        elements.append(Spacer(1, 2 * inch))

        # Título principal
        title = Paragraph("RELATÓRIO PSICOMÉTRICO", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.3 * inch))

        # Nome do usuário
        user_para = Paragraph(
            f"<b>{user_name}</b>",
            ParagraphStyle(
                'UserName',
                parent=self.styles['Normal'],
                fontSize=18,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#424242')
            )
        )
        elements.append(user_para)
        elements.append(Spacer(1, 0.5 * inch))

        # Informações do relatório
        info_data = [
            ["Data do Relatório:", datetime.now().strftime('%d de %B de %Y')],
            ["Conversas Analisadas:", str(total_conversations)],
            ["Modelo de IA:", "Claude Sonnet 4.5"],
            ["Tipo de Análise:", "Psicometria Computacional"]
        ]

        info_table = Table(info_data, colWidths=[2.5 * inch, 3 * inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#424242')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e0e0e0')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 1 * inch))

        # Aviso legal
        disclaimer = Paragraph(
            "<b>AVISO LEGAL:</b> Este relatório foi gerado por Inteligência Artificial "
            "através da análise de conversas naturais. Não constitui diagnóstico clínico "
            "e deve ser interpretado como ferramenta complementar de autoconhecimento. "
            "Protegido pela LGPD (Lei 13.709/2018).",
            ParagraphStyle(
                'Disclaimer',
                parent=self.styles['Normal'],
                fontSize=8,
                alignment=TA_JUSTIFY,
                textColor=colors.HexColor('#757575'),
                borderPadding=10,
                borderColor=colors.HexColor('#e0e0e0'),
                borderWidth=1,
                backColor=colors.HexColor('#f5f5f5')
            )
        )
        elements.append(disclaimer)
        elements.append(PageBreak())

        return elements

    def _create_big_five_section(self, big_five_data: dict):
        """Cria seção Big Five (OCEAN)"""
        elements = []

        # Título da seção
        elements.append(Paragraph("1. ANÁLISE BIG FIVE (OCEAN)", self.styles['CustomSubtitle']))
        elements.append(Paragraph(
            "O modelo Big Five avalia cinco dimensões fundamentais da personalidade.",
            self.styles['CustomBody']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Interpretação geral
        if 'interpretation' in big_five_data:
            elements.append(Paragraph("<b>Interpretação Geral:</b>", self.styles['SectionHeader']))
            elements.append(Paragraph(big_five_data['interpretation'], self.styles['CustomBody']))
            elements.append(Spacer(1, 0.15 * inch))

        # Tabela com scores
        dimensions = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        dimension_names = {
            'openness': 'Abertura à Experiência',
            'conscientiousness': 'Conscienciosidade',
            'extraversion': 'Extroversão',
            'agreeableness': 'Amabilidade',
            'neuroticism': 'Neuroticismo'
        }

        table_data = [['Dimensão', 'Score', 'Nível', 'Descrição']]

        for dim in dimensions:
            if dim in big_five_data:
                dim_data = big_five_data[dim]
                score = dim_data.get('score', 0)
                level = dim_data.get('level', 'N/A')
                description = dim_data.get('description', '')

                # Barra de progresso visual
                bar = self._create_score_bar(score)

                table_data.append([
                    dimension_names[dim],
                    f"{score}/100",
                    level,
                    description[:100] + "..." if len(description) > 100 else description
                ])

        score_table = Table(table_data, colWidths=[1.5 * inch, 0.8 * inch, 1 * inch, 3.2 * inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3949ab')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(score_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Confiança da análise
        if 'confidence' in big_five_data:
            conf_para = Paragraph(
                f"<b>Confiança da Análise:</b> {big_five_data['confidence']}% "
                f"(baseado em {big_five_data.get('conversations_analyzed', 'N/A')} conversas)",
                self.styles['CustomBody']
            )
            elements.append(conf_para)

        elements.append(PageBreak())
        return elements

    def _create_score_bar(self, score: int) -> str:
        """Cria representação visual de score (não usado diretamente no PDF mas útil para referência)"""
        filled = int(score / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty

    def _create_vark_section(self, vark_data: dict):
        """Cria seção VARK (Estilos de Aprendizagem)"""
        elements = []

        elements.append(Paragraph("2. ESTILOS DE APRENDIZAGEM (VARK)", self.styles['CustomSubtitle']))
        elements.append(Paragraph(
            "Análise dos estilos preferenciais de aprendizagem e processamento de informação.",
            self.styles['CustomBody']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Estilo dominante
        if 'dominant_style' in vark_data:
            elements.append(Paragraph(
                f"<b>Estilo Dominante:</b> {vark_data['dominant_style']}",
                self.styles['SectionHeader']
            ))
            elements.append(Spacer(1, 0.1 * inch))

        # Tabela de scores VARK
        vark_styles = ['visual', 'auditory', 'reading', 'kinesthetic']
        vark_names = {
            'visual': 'Visual',
            'auditory': 'Auditivo',
            'reading': 'Leitura/Escrita',
            'kinesthetic': 'Cinestésico'
        }

        table_data = [['Estilo', 'Score', 'Porcentagem']]

        for style in vark_styles:
            if style in vark_data:
                score = vark_data[style]
                table_data.append([
                    vark_names[style],
                    f"{score}/100",
                    f"{score}%"
                ])

        vark_table = Table(table_data, colWidths=[2 * inch, 1.5 * inch, 2 * inch])
        vark_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3949ab')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(vark_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Recomendação de treinamento
        if 'recommended_training' in vark_data:
            elements.append(Paragraph("<b>Recomendação de Treinamento:</b>", self.styles['SectionHeader']))
            elements.append(Paragraph(vark_data['recommended_training'], self.styles['CustomBody']))

        elements.append(PageBreak())
        return elements

    def _create_eq_section(self, eq_data: dict):
        """Cria seção de Inteligência Emocional"""
        elements = []

        elements.append(Paragraph("3. INTELIGÊNCIA EMOCIONAL (EQ)", self.styles['CustomSubtitle']))
        elements.append(Paragraph(
            "Avaliação das competências emocionais e sociais.",
            self.styles['CustomBody']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Score total de EQ
        if 'eq_score' in eq_data:
            eq_para = Paragraph(
                f"<b>Score Total de EQ:</b> {eq_data['eq_score']}/100 - {eq_data.get('eq_level', 'N/A')}",
                self.styles['SectionHeader']
            )
            elements.append(eq_para)
            elements.append(Spacer(1, 0.15 * inch))

        # Componentes do EQ
        if 'eq_details' in eq_data and eq_data['eq_details']:
            eq_details = eq_data['eq_details']

            components_data = [['Componente', 'Score', 'Descrição']]

            for component, data in eq_details.items():
                if isinstance(data, dict):
                    components_data.append([
                        component.replace('_', ' ').title(),
                        f"{data.get('score', 0)}/100",
                        data.get('description', '')[:80] + "..." if len(data.get('description', '')) > 80 else data.get('description', '')
                    ])

            if len(components_data) > 1:
                eq_table = Table(components_data, colWidths=[2 * inch, 1 * inch, 3.5 * inch])
                eq_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3949ab')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(eq_table)

        elements.append(PageBreak())
        return elements

    def _create_values_section(self, values_data: dict):
        """Cria seção de Valores de Schwartz"""
        elements = []

        elements.append(Paragraph("4. VALORES PESSOAIS (SCHWARTZ)", self.styles['CustomSubtitle']))
        elements.append(Paragraph(
            "Análise dos valores universais que guiam suas decisões e comportamentos.",
            self.styles['CustomBody']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Top 3 valores
        if 'top_3_values' in values_data:
            elements.append(Paragraph("<b>Top 3 Valores Dominantes:</b>", self.styles['SectionHeader']))
            for i, value in enumerate(values_data['top_3_values'][:3], 1):
                elements.append(Paragraph(f"{i}. {value}", self.styles['CustomBody']))
            elements.append(Spacer(1, 0.15 * inch))

        # Tabela de todos os valores
        schwartz_values = [
            'self_direction', 'stimulation', 'hedonism', 'achievement', 'power',
            'security', 'conformity', 'tradition', 'benevolence', 'universalism'
        ]

        values_names = {
            'self_direction': 'Autodireção',
            'stimulation': 'Estimulação',
            'hedonism': 'Hedonismo',
            'achievement': 'Realização',
            'power': 'Poder',
            'security': 'Segurança',
            'conformity': 'Conformidade',
            'tradition': 'Tradição',
            'benevolence': 'Benevolência',
            'universalism': 'Universalismo'
        }

        table_data = [['Valor', 'Score']]

        for val in schwartz_values:
            if val in values_data and isinstance(values_data[val], dict):
                score = values_data[val].get('score', 0)
                table_data.append([values_names[val], f"{score}/100"])

        if len(table_data) > 1:
            values_table = Table(table_data, colWidths=[3 * inch, 2 * inch])
            values_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3949ab')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(values_table)
            elements.append(Spacer(1, 0.2 * inch))

        # Cultural fit e retention risk
        if 'cultural_fit' in values_data:
            elements.append(Paragraph("<b>Fit Cultural:</b>", self.styles['SectionHeader']))
            elements.append(Paragraph(values_data['cultural_fit'], self.styles['CustomBody']))

        if 'retention_risk' in values_data:
            elements.append(Paragraph(
                f"<b>Risco de Retenção:</b> {values_data['retention_risk']}",
                self.styles['CustomBody']
            ))

        return elements

    def generate_pdf(
        self,
        user_name: str,
        total_conversations: int,
        big_five: dict,
        eq: dict,
        vark: dict,
        values: dict
    ) -> BytesIO:
        """
        Gera PDF completo com todas as análises psicométricas

        Returns:
            BytesIO: Buffer com o PDF gerado
        """
        logger.info(f"📄 Gerando PDF para {user_name}")

        # Criar buffer para o PDF
        buffer = BytesIO()

        # Criar documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=80,
            bottomMargin=80
        )

        # Elementos do documento
        elements = []

        # Página de capa
        elements.extend(self._create_cover_page(user_name, total_conversations))

        # Big Five
        if big_five and 'error' not in big_five:
            elements.extend(self._create_big_five_section(big_five))

        # VARK
        if vark and 'error' not in vark:
            elements.extend(self._create_vark_section(vark))

        # EQ
        if eq and 'error' not in eq:
            elements.extend(self._create_eq_section(eq))

        # Valores
        if values and 'error' not in values:
            elements.extend(self._create_values_section(values))

        # Construir PDF com header e footer
        doc.build(
            elements,
            onFirstPage=self._add_header,
            onLaterPages=self._add_header
        )

        # Adicionar footer (workaround - ReportLab não tem onFooter direto)
        # Vamos adicionar via callback personalizado

        buffer.seek(0)
        logger.info("✅ PDF gerado com sucesso")

        return buffer


# Função auxiliar para uso fácil
def generate_psychometric_pdf(
    user_name: str,
    total_conversations: int,
    big_five: dict,
    eq: dict,
    vark: dict,
    values: dict
) -> BytesIO:
    """
    Função auxiliar para gerar PDF rapidamente
    """
    generator = PsychometricPDFGenerator()
    return generator.generate_pdf(
        user_name=user_name,
        total_conversations=total_conversations,
        big_five=big_five,
        eq=eq,
        vark=vark,
        values=values
    )
