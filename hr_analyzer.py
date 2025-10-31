# -*- coding: utf-8 -*-
"""
HR Analyzer Module
Módulo para análise de dados de colaboradores e geração de relatórios para o RH.
"""

from typing import Dict, List, Any
from datetime import datetime

class HRAnalyzer:
    """
    Analisa os dados de memória de um colaborador e gera relatórios
    focados em potencialidades e desenvolvimento de carreira.
    """

    def __init__(self, memory_module: Any):
        """
        Inicializa o analisador com acesso ao módulo de memória.

        Args:
            memory_module: Uma instância do MemoryModule para acessar os dados.
        """
        self.memory = memory_module
        self.debug_mode = True

    def _debug_log(self, message: str):
        if self.debug_mode:
            print(f"🔍 HR ANALYZER: {message}")

    async def generate_report(self, user_id: str) -> str:
        """
        Gera um relatório de análise de potencial para um colaborador específico.

        Args:
            user_id: O ID do colaborador a ser analisado.

        Returns:
            Uma string formatada em Markdown com o relatório completo.
        """
        self._debug_log(f"Iniciando geração de relatório para o usuário: {user_id}")

        memory_cache = self.memory.memory_cache.get(user_id, {})
        if not memory_cache:
            return f"# Relatório de Análise de Potencial\n\n**Usuário:** {user_id}\n\nNenhum dado encontrado para este colaborador."

        facts = memory_cache.get('facts_extracted', [])
        conversations = memory_cache.get('raw_conversations', [])

        report_sections = []

        # 1. Cabeçalho
        user_identity = self.memory.get_user_identity(user_id)
        report_sections.append(f"# Relatório de Análise de Potencial")
        report_sections.append(f"**Colaborador:** {user_identity.full_name} (`{user_id}`)")
        report_sections.append(f"**Data do Relatório:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_sections.append(f"**Período Analisado:** {len(conversations)} interações registradas.")
        report_sections.append("---")

        # 2. Análise de Potencialidades
        potential_analysis = self._analyze_potentialities(facts)
        report_sections.append("## 💡 Análise de Potencialidades")
        report_sections.append(potential_analysis)
        report_sections.append("---")

        # 3. Nível de Engajamento
        engagement_analysis = self._analyze_engagement(conversations)
        report_sections.append("## 📊 Nível de Engajamento")
        report_sections.append(engagement_analysis)
        report_sections.append("---")

        # 4. Trajetória de Carreira
        career_analysis = self._analyze_career_trajectory(facts, conversations)
        report_sections.append("## 🚀 Trajetória de Carreira")
        report_sections.append(career_analysis)
        report_sections.append("---")

        # 5. Sugestões de Ação para o RH
        recommendations = self._generate_recommendations(facts, conversations)
        report_sections.append("## ✅ Sugestões de Ação para o RH")
        report_sections.append(recommendations)
        report_sections.append("---")

        self._debug_log(f"Relatório gerado com sucesso para o usuário: {user_id}")
        return "\n\n".join(report_sections)

    def _analyze_potentialities(self, facts: List[str]) -> str:
        """Analisa e resume as potencialidades extraídas."""
        skills = [f.split(':')[-1].strip() for f in facts if 'HABILIDADE_MENCIONADA' in f]
        aspirations = [f.split(':')[-1].strip() for f in facts if 'ASPIRACAO' in f]
        interests = [f.split(':')[-1].strip() for f in facts if 'INTERESSE_INOVACAO' in f]

        if not any([skills, aspirations, interests]):
            return "Nenhuma potencialidade específica foi extraída das conversas até o momento."

        analysis = []
        if skills:
            analysis.append(f"**Habilidades Mencionadas:** {', '.join(list(set(skills)))}")
        if aspirations:
            analysis.append(f"**Aspirações de Carreira:** {', '.join(list(set(aspirations)))}")
        if interests:
            analysis.append(f"**Interesses em Inovação/Colaboração:** {', '.join(list(set(interests)))}")

        return "\n".join(analysis)

    def _analyze_engagement(self, conversations: List[Dict]) -> str:
        """Faz uma análise qualitativa do nível de engajamento."""
        engagement_keywords = ['motivado', 'engajado', 'gosto do projeto', 'aprendendo muito', 'bom desafio']
        disengagement_keywords = ['desmotivado', 'frustrado', 'estagnado', 'sobrecarregado', 'pensando em sair']

        engagement_score = 0
        for conv in conversations[-10:]: # Foco nas conversas recentes
            content = conv.get('full_document', '').lower()
            for key in engagement_keywords:
                if key in content:
                    engagement_score += 1
            for key in disengagement_keywords:
                if key in content:
                    engagement_score -= 1.5 # Penalidade maior para desengajamento

        if engagement_score > 3:
            return "**Nível de Engajamento: Alto.** O colaborador demonstra entusiasmo e motivação com seus projetos e desafios atuais."
        elif engagement_score >= 0:
            return "**Nível de Engajamento: Médio.** O colaborador parece estável, com momentos de engajamento, mas sem picos notáveis de entusiasmo ou frustração."
        else:
            return "**Nível de Engajamento: Baixo.** Foram detectados sinais de frustração, desmotivação ou sobrecarga. Recomenda-se uma conversa de alinhamento."

    def _analyze_career_trajectory(self, facts: List[str], conversations: List[Dict]) -> str:
        """Analisa a percepção do colaborador sobre sua carreira."""
        stagnation_keywords = ['mesma coisa', 'não aprendo nada novo', 'carreira parada', 'sem desafios']
        growth_keywords = ['novo desafio', 'quero crescer', 'próximo passo', 'aprender mais']

        stagnation_mentions = 0
        growth_mentions = 0
        for conv in conversations[-10:]:
            content = conv.get('full_document', '').lower()
            if any(key in content for key in stagnation_keywords):
                stagnation_mentions += 1
            if any(key in content for key in growth_keywords):
                growth_mentions += 1

        analysis = []
        if stagnation_mentions > 1:
            analysis.append("- **Sinais de Estagnação:** O colaborador mencionou repetidamente sentir-se estagnado ou sem novos desafios.")
        if growth_mentions > 1:
            analysis.append("- **Desejo de Crescimento:** O colaborador expressa um forte desejo por novos aprendizados e pelo próximo passo em sua carreira.")
        if not analysis:
            return "A percepção sobre a trajetória de carreira parece estável, sem fortes indicadores de estagnação ou desejo iminente de mudança."

        return "\n".join(analysis)

    def _generate_recommendations(self, facts: List[str], conversations: List[Dict]) -> str:
        """Gera recomendações acionáveis para o RH."""
        recommendations = []

        # Recomendação baseada em aspiração de liderança
        if any('LIDERANCA' in f for f in facts):
            recommendations.append("- **Explorar Potencial de Liderança:** O colaborador demonstrou interesse em liderança. Considere incluí-lo em programas de desenvolvimento de líderes ou oferecer pequenas oportunidades de liderança de projetos.")

        # Recomendação baseada em habilidades e interesses
        skills = [f.split(':')[-1].strip() for f in facts if 'HABILIDADE_MENCIONADA' in f]
        if skills:
            recommendations.append(f"- **Alavancar Habilidades:** O colaborador mencionou habilidades em {', '.join(list(set(skills)))}. Avalie se essas competências estão sendo plenamente utilizadas na função atual ou se podem ser aproveitadas em outras áreas da empresa.")

        # Recomendação baseada em engajamento
        engagement_level = self._analyze_engagement(conversations)
        if "Baixo" in engagement_level:
            recommendations.append("- **Plano de Ação de Engajamento:** Devido aos sinais de baixo engajamento, agende uma conversa de feedback e alinhamento para entender as causas e traçar um plano de ação.")

        # Recomendação baseada em estagnação
        career_trajectory = self._analyze_career_trajectory(facts, conversations)
        if "Estagnação" in career_trajectory:
            recommendations.append("- **Discutir Plano de Carreira:** O colaborador pode estar se sentindo estagnado. Uma conversa sobre o plano de desenvolvimento individual (PDI) e futuras oportunidades pode ser muito benéfica.")

        if not recommendations:
            return "Nenhuma ação prioritária foi identificada neste momento. Continue monitorando o desenvolvimento e engajamento do colaborador."

        return "\n".join(recommendations)
