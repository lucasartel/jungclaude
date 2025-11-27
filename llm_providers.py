"""
llm_providers.py - Abstração de Provedores LLM
================================================

Sistema de alternância entre Grok (xAI) e Claude (Anthropic).
Permite trocar de provedor via variável de ambiente LLM_PROVIDER.

Uso:
    No .env, adicione: LLM_PROVIDER=grok  (ou claude)

    No código:
    from llm_providers import get_llm_response

    response = get_llm_response(
        prompt="Olá, como vai?",
        temperature=0.7,
        max_tokens=2000
    )

Modelos suportados:
    - Grok: grok-4-fast-reasoning (padrão atual)
    - Claude: claude-3-5-haiku-20241022 (modelo mais barato)

Autor: Sistema Jung Claude
Data: 2025-11-27
"""

import os
import logging
from typing import Optional
from abc import ABC, abstractmethod
from openai import OpenAI

logger = logging.getLogger(__name__)

# ============================================================
# ABSTRACT BASE CLASS
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
# GROK PROVIDER (xAI)
# ============================================================

class GrokProvider(LLMProvider):
    """Provedor Grok (xAI) - Atual"""

    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")

        if not self.api_key:
            raise ValueError("❌ XAI_API_KEY não encontrado no .env")

        self.model = "grok-4-fast-reasoning"

        logger.info(f"✅ GrokProvider inicializado (modelo: {self.model})")

    def get_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Gera resposta via Grok API"""

        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.x.ai/v1",
                timeout=30.0
            )

            completion = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )

            return completion.choices[0].message.content

        except Exception as e:
            logger.error(f"❌ Erro ao chamar Grok API: {e}")
            raise Exception(f"Erro ao chamar Grok API: {e}")

    def get_model_name(self) -> str:
        return f"Grok ({self.model})"


# ============================================================
# CLAUDE PROVIDER (Anthropic)
# ============================================================

class ClaudeProvider(LLMProvider):
    """Provedor Claude (Anthropic) - Alternativa"""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("❌ ANTHROPIC_API_KEY não encontrado no .env")

        # Modelo mais barato do Claude
        self.model = "claude-3-5-haiku-20241022"

        logger.info(f"✅ ClaudeProvider inicializado (modelo: {self.model})")

    def get_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Gera resposta via Claude API"""

        try:
            # Importar apenas quando necessário (para não quebrar se não tiver instalado)
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "❌ Biblioteca 'anthropic' não instalada!\n"
                    "   Execute: pip install anthropic"
                )

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
# FACTORY
# ============================================================

def create_llm_provider(provider_name: Optional[str] = None) -> LLMProvider:
    """
    Factory para criar provedor LLM baseado em variável de ambiente.

    Args:
        provider_name: Nome do provedor ("grok" ou "claude")
                      Se None, usa variável LLM_PROVIDER do .env

    Returns:
        Instância de LLMProvider (Grok ou Claude)

    Raises:
        ValueError: Se provedor não for reconhecido
    """

    if provider_name is None:
        provider_name = os.getenv("LLM_PROVIDER", "grok").lower()

    provider_name = provider_name.lower().strip()

    logger.info(f"🔧 Criando LLM Provider: {provider_name}")

    if provider_name == "grok":
        return GrokProvider()
    elif provider_name == "claude":
        return ClaudeProvider()
    else:
        raise ValueError(
            f"❌ Provedor '{provider_name}' não reconhecido.\n"
            f"   Opções válidas: 'grok' ou 'claude'\n"
            f"   Configure no .env: LLM_PROVIDER=grok (ou claude)"
        )


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
    Função auxiliar para obter resposta do LLM atual.

    Usa o provider configurado em LLM_PROVIDER (padrão: grok).
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


# ============================================================
# TESTES
# ============================================================

if __name__ == "__main__":
    """Testes básicos"""

    logging.basicConfig(level=logging.INFO)

    print("="*60)
    print("TESTE: LLM Providers")
    print("="*60)

    # Testar Grok
    print("\n[1] Testando Grok...")
    os.environ["LLM_PROVIDER"] = "grok"
    _provider_instance = None  # Reset singleton

    try:
        response = get_llm_response("Responda em uma palavra: qual a cor do céu?", max_tokens=10)
        print(f"✅ Grok respondeu: {response}")
        print(f"   Modelo: {get_current_model_name()}")
    except Exception as e:
        print(f"❌ Erro: {e}")

    # Testar Claude
    print("\n[2] Testando Claude...")
    os.environ["LLM_PROVIDER"] = "claude"
    _provider_instance = None  # Reset singleton

    try:
        response = get_llm_response("Responda em uma palavra: qual a cor do céu?", max_tokens=10)
        print(f"✅ Claude respondeu: {response}")
        print(f"   Modelo: {get_current_model_name()}")
    except Exception as e:
        print(f"❌ Erro: {e}")

    print("\n" + "="*60)
    print("✅ Testes concluídos")
    print("="*60)
