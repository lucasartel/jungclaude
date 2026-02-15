"""
user_profile_writer.py - Camada de memória textual do JungAgent

Mantém dois níveis de memória em arquivos .md:
  data/users/{user_id}/sessions/YYYY-MM-DD.md  ← log bruto do dia (append-only)
  data/users/{user_id}/profile.md              ← perfil psicológico consolidado
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "users")


def _user_dir(user_id: str) -> str:
    path = os.path.join(DATA_DIR, user_id)
    os.makedirs(os.path.join(path, "sessions"), exist_ok=True)
    return path


def write_session_entry(
    user_id: str,
    user_name: str,
    user_input: str,
    ai_response: str,
    metadata: Optional[Dict] = None,
    tag: str = "",
) -> None:
    """
    Appenda uma entrada de conversa no log diário do usuário.
    tag: string opcional ex. '[FLUSH]' para marcar entradas de flush de contexto.
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        session_path = os.path.join(_user_dir(user_id), "sessions", f"{today}.md")

        meta = metadata or {}
        tension = meta.get("tension_level", 0.0)
        charge = meta.get("affective_charge", 0.0)
        ts = datetime.now().strftime("%H:%M")

        tag_str = f" {tag}" if tag else ""
        entry = (
            f"\n## {ts}{tag_str}\n"
            f"**Usuário:** {user_input}\n\n"
            f"**Jung:** {ai_response}\n\n"
            f"_tensão={tension:.1f} | carga_afetiva={charge:.1f}_\n"
        )

        is_new_file = not os.path.exists(session_path)
        with open(session_path, "a", encoding="utf-8") as f:
            if is_new_file:
                f.write(f"# Sessão {today} — {user_name}\n")
            f.write(entry)

    except Exception as e:
        logger.warning(f"⚠️ user_profile_writer: erro ao gravar sessão de {user_id}: {e}")


def rebuild_profile_md(
    user_id: str,
    user_name: str,
    facts: List[Dict],
    psychometrics: Optional[Dict] = None,
    patterns: Optional[List[Dict]] = None,
) -> None:
    """
    Reescreve o profile.md do usuário com todos os dados atuais.
    Chamado após cada consolidação de memória.
    """
    try:
        profile_path = os.path.join(_user_dir(user_id), "profile.md")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = [f"# Perfil: {user_name} — atualizado em {now}\n"]

        # ── Fatos pessoais ──────────────────────────────────────────────
        pessoais = [f for f in facts if f.get("category") == "RELACIONAMENTO"]
        if pessoais:
            lines.append("\n## Fatos Pessoais\n")
            for f in pessoais:
                lines.append(
                    f"- {f['fact_type']} / {f['attribute']}: {f['fact_value']}\n"
                )

        # ── Vida profissional ────────────────────────────────────────────
        trabalho = [f for f in facts if f.get("category") == "TRABALHO"]
        if trabalho:
            lines.append("\n## Vida Profissional\n")
            for f in trabalho:
                lines.append(
                    f"- {f['fact_type']} / {f['attribute']}: {f['fact_value']}\n"
                )

        # ── Padrões comportamentais ──────────────────────────────────────
        if patterns:
            lines.append("\n## Padrões Comportamentais\n")
            for p in patterns:
                name = p.get("pattern_name", "")
                desc = p.get("pattern_description", "")
                freq = p.get("frequency_count", 1)
                lines.append(f"- **{name}** (freq={freq}): {desc}\n")

        # ── Psicometria ──────────────────────────────────────────────────
        if psychometrics:
            lines.append("\n## Psicometria\n")
            big5 = (
                f"Abertura={psychometrics.get('openness_score', '?')} | "
                f"Conscienciosidade={psychometrics.get('conscientiousness_score', '?')} | "
                f"Extroversão={psychometrics.get('extraversion_score', '?')} | "
                f"Amabilidade={psychometrics.get('agreeableness_score', '?')} | "
                f"Neuroticismo={psychometrics.get('neuroticism_score', '?')}"
            )
            lines.append(f"**Big Five:** {big5}\n\n")

            eq_overall = psychometrics.get("eq_overall")
            if eq_overall:
                lines.append(f"**Inteligência Emocional (geral):** {eq_overall}/100\n\n")

            schwartz = psychometrics.get("schwartz_top_3")
            if schwartz:
                lines.append(f"**Valores (Schwartz top 3):** {schwartz}\n\n")

            summary = psychometrics.get("executive_summary")
            if summary:
                lines.append(f"### Resumo Executivo\n{summary}\n")

        with open(profile_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        logger.info(f"✅ profile.md atualizado para {user_id} ({len(facts)} fatos)")

    except Exception as e:
        logger.warning(f"⚠️ user_profile_writer: erro ao reconstruir profile.md de {user_id}: {e}")
