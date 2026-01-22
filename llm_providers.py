"""
llm_providers.py - Provider LLM Unificado (Claude Sonnet 4.5)
=============================================================

Sistema unificado de LLM usando exclusivamente Claude Sonnet 4.5.
OpenAI é mantido apenas para embeddings (em outros módulos).

Modelo único: claude-sonnet-4-5-20250929

Uso:
    from llm_providers import get_llm_response

    response = get_llm_response(
        prompt="Olá, como vai?",
        temperature=0.7,
        max_tokens=2000
    )

Autor: Sistema Jung Claude
Data: 2025-01-22
Versão: 2.0 (Unificado para Claude)
"""

import os
import logging
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURAÇÃO - MODELO ÚNICO
# ============================================================

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


# ============================================================
# ABSTRACT BASE CLASS (mantida para compatibilidade)
# ============================================================

class LLMProvider(ABC):
    """Interface abstrata para provedores de LLM"""

    @abstractmethod
    def get_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Gera resposta do LLM"""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Retorna nome do modelo sendo usado"""
        pass


# ============================================================
# CLAUDE PROVIDER (ÚNICO)
# ============================================================

class ClaudeProvider(LLMProvider):
    """
    Provedor Claude (Anthropic) - Único provider suportado.

    Modelo padrão: claude-sonnet-4-5-20250929
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("❌ ANTHROPIC_API_KEY não encontrado no .env")

        self.model = model
        logger.info(f"✅ ClaudeProvider inicializado (modelo: {self.model})")

    def get_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Gera resposta via Claude API"""

        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "❌ Biblioteca 'anthropic' não instalada!\n"
                "   Execute: pip install anthropic"
            )

        try:
            client = anthropic.Anthropic(api_key=self.api_key)

            message = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text

        except Exception as e:
            logger.error(f"❌ Erro ao chamar Claude API: {e}")
            raise Exception(f"Erro ao chamar Claude API: {e}")

    def get_model_name(self) -> str:
        return f"Claude ({self.model})"


# ============================================================
# FACTORY (simplificada - sempre retorna Claude)
# ============================================================

def create_llm_provider(provider_name: Optional[str] = None) -> LLMProvider:
    """
    Factory para criar provedor LLM.

    NOTA: Sempre retorna ClaudeProvider independente do parâmetro.
    O parâmetro provider_name é mantido por compatibilidade mas ignorado.

    Args:
        provider_name: Ignorado (mantido por compatibilidade)

    Returns:
        Instância de ClaudeProvider
    """
    # Ignorar provider_name - sempre usar Claude
    if provider_name and provider_name.lower() != "claude":
        logger.warning(f"⚠️ Provider '{provider_name}' solicitado, mas usando Claude (único suportado)")

    logger.info(f"🔧 Criando LLM Provider: Claude ({DEFAULT_MODEL})")
    return ClaudeProvider()


# ============================================================
# HELPER FUNCTION (compatibilidade)
# ============================================================

# Singleton global do provider (inicializado na primeira chamada)
_provider_instance: Optional[LLMProvider] = None

def get_llm_response(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> str:
    """
    Função auxiliar para obter resposta do LLM.

    Usa Claude Sonnet 4.5 como único provider.
    O provider é inicializado apenas uma vez (singleton).

    Args:
        prompt: Prompt para o LLM
        temperature: Temperatura (0.0 = determinístico, 1.0 = criativo)
        max_tokens: Máximo de tokens na resposta

    Returns:
        Resposta do LLM como string

    Example:
        response = get_llm_response("Explique arquétipos junguianos", temperature=0.8)
    """

    global _provider_instance

    if _provider_instance is None:
        _provider_instance = create_llm_provider()
        logger.info(f"✅ LLM Provider ativado: {_provider_instance.get_model_name()}")

    return _provider_instance.get_response(prompt, temperature, max_tokens)


def get_current_model_name() -> str:
    """Retorna nome do modelo LLM atualmente ativo"""

    global _provider_instance

    if _provider_instance is None:
        _provider_instance = create_llm_provider()

    return _provider_instance.get_model_name()


def reset_provider():
    """Reseta o singleton do provider (útil para testes)"""
    global _provider_instance
    _provider_instance = None
    logger.info("🔄 LLM Provider resetado")


# ============================================================
# TESTES
# ============================================================

if __name__ == "__main__":
    """Testes básicos"""

    logging.basicConfig(level=logging.INFO)

    print("="*60)
    print("TESTE: LLM Provider (Claude Sonnet 4.5)")
    print("="*60)

    print(f"\nModelo configurado: {DEFAULT_MODEL}")

    try:
        response = get_llm_response(
            "Responda em uma palavra: qual a cor do céu?",
            max_tokens=10
        )
        print(f"✅ Claude respondeu: {response}")
        print(f"   Modelo: {get_current_model_name()}")
    except Exception as e:
        print(f"❌ Erro: {e}")

    print("\n" + "="*60)
    print("✅ Teste concluído")
    print("="*60)
