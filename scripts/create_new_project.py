#!/usr/bin/env python3
"""
Script para criar novos projetos e conectá-los ao GitHub
Uso: python create_new_project.py <nome-do-projeto> [--type python|node|react] [--private]
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Templates de .gitignore
GITIGNORE_TEMPLATES = {
    "python": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.pytest_cache/
.coverage
htmlcov/
*.db
*.sqlite3
*.log
""",
    "node": """# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
dist/
build/
.env
.env.local
.env.*.local
*.log
.DS_Store
coverage/
.nyc_output/
""",
    "react": """# React
node_modules/
/build
/dist
.env.local
.env.development.local
.env.test.local
.env.production.local
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.DS_Store
coverage/
"""
}

# Templates de README
README_TEMPLATES = {
    "python": """# {project_name}

## Descrição
[Adicione descrição do projeto aqui]

## Instalação

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\\Scripts\\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

## Estrutura do Projeto

```
{project_name}/
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Licença
MIT
""",
    "node": """# {project_name}

## Descrição
[Adicione descrição do projeto aqui]

## Instalação

```bash
npm install
```

## Uso

```bash
npm start
```

## Scripts Disponíveis

- `npm start` - Inicia o projeto
- `npm test` - Roda os testes
- `npm run build` - Build de produção

## Estrutura do Projeto

```
{project_name}/
├── src/
├── package.json
├── README.md
└── .gitignore
```

## Licença
MIT
""",
    "react": """# {project_name}

## Descrição
[Adicione descrição do projeto aqui]

## Instalação

```bash
npm install
```

## Desenvolvimento

```bash
npm start
```

Abre [http://localhost:3000](http://localhost:3000) no navegador.

## Build

```bash
npm run build
```

## Estrutura do Projeto

```
{project_name}/
├── public/
├── src/
│   ├── components/
│   ├── App.js
│   └── index.js
├── package.json
├── README.md
└── .gitignore
```

## Licença
MIT
"""
}


def run_command(cmd, cwd=None, check=True):
    """Executa comando e retorna output"""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check
    )
    return result.stdout.strip()


def create_project_structure(project_path, project_type):
    """Cria estrutura básica do projeto"""

    # Criar diretório raiz
    project_path.mkdir(parents=True, exist_ok=True)

    # Criar .gitignore
    gitignore_path = project_path / ".gitignore"
    gitignore_path.write_text(GITIGNORE_TEMPLATES.get(project_type, GITIGNORE_TEMPLATES["python"]))

    # Criar README.md
    readme_path = project_path / "README.md"
    readme_content = README_TEMPLATES.get(project_type, README_TEMPLATES["python"])
    readme_path.write_text(readme_content.format(project_name=project_path.name))

    # Estruturas específicas por tipo
    if project_type == "python":
        (project_path / "main.py").write_text('#!/usr/bin/env python3\n\nif __name__ == "__main__":\n    print("Hello World!")\n')
        (project_path / "requirements.txt").write_text("# Adicione suas dependências aqui\n")

    elif project_type == "node":
        package_json = {
            "name": project_path.name,
            "version": "1.0.0",
            "description": "",
            "main": "index.js",
            "scripts": {
                "start": "node index.js",
                "test": "echo \"Error: no test specified\" && exit 1"
            },
            "keywords": [],
            "author": "",
            "license": "MIT"
        }
        import json
        (project_path / "package.json").write_text(json.dumps(package_json, indent=2))
        (project_path / "index.js").write_text('console.log("Hello World!");\n')
        (project_path / "src").mkdir(exist_ok=True)

    elif project_type == "react":
        print("   Para React, recomendo usar: npx create-react-app " + project_path.name)
        print("   Criando estrutura básica...")
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "public").mkdir(exist_ok=True)


def create_github_repo(project_name, is_private):
    """Cria repositório no GitHub usando gh CLI"""

    # Verificar se gh está instalado
    try:
        run_command("gh --version")
    except:
        print("❌ gh CLI não encontrado. Instale: https://cli.github.com/")
        return False

    # Criar repo
    visibility = "--private" if is_private else "--public"
    try:
        print(f"   Criando repositório GitHub ({visibility})...")
        run_command(f'gh repo create {project_name} {visibility} --source=. --remote=origin')
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar repositório: {e}")
        return False


def initialize_git(project_path):
    """Inicializa git e faz commit inicial"""

    print("   Inicializando Git...")
    run_command("git init", cwd=project_path)

    print("   Adicionando arquivos...")
    run_command("git add .", cwd=project_path)

    print("   Criando commit inicial...")
    run_command('git commit -m "Initial commit"', cwd=project_path)


def main():
    parser = argparse.ArgumentParser(description="Criar novo projeto e conectar ao GitHub")
    parser.add_argument("project_name", help="Nome do projeto")
    parser.add_argument(
        "--type",
        choices=["python", "node", "react"],
        default="python",
        help="Tipo do projeto (default: python)"
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Criar repositório privado (default: público)"
    )
    parser.add_argument(
        "--no-github",
        action="store_true",
        help="Não criar repositório no GitHub (apenas local)"
    )
    parser.add_argument(
        "--path",
        help="Caminho customizado (default: pasta atual)"
    )

    args = parser.parse_args()

    # Determinar caminho do projeto
    if args.path:
        base_path = Path(args.path)
    else:
        base_path = Path.cwd()

    project_path = base_path / args.project_name

    # Verificar se já existe
    if project_path.exists():
        print(f"❌ Projeto '{args.project_name}' já existe em {project_path}")
        sys.exit(1)

    print(f"🚀 Criando projeto: {args.project_name}")
    print(f"   Tipo: {args.type}")
    print(f"   Local: {project_path}")
    print()

    # 1. Criar estrutura do projeto
    print("📁 Criando estrutura do projeto...")
    create_project_structure(project_path, args.type)
    print("   ✅ Estrutura criada")
    print()

    # 2. Inicializar Git
    print("📦 Inicializando Git...")
    initialize_git(project_path)
    print("   ✅ Git inicializado")
    print()

    # 3. Criar repositório no GitHub (se solicitado)
    if not args.no_github:
        print("🐙 Criando repositório no GitHub...")
        os.chdir(project_path)
        if create_github_repo(args.project_name, args.private):
            print("   ✅ Repositório criado no GitHub")
            print()

            # Push inicial
            print("📤 Fazendo push inicial...")
            try:
                run_command("git push -u origin main")
                print("   ✅ Push concluído")
            except:
                try:
                    # Tentar com master se main falhar
                    run_command("git branch -M main")
                    run_command("git push -u origin main")
                    print("   ✅ Push concluído")
                except subprocess.CalledProcessError as e:
                    print(f"   ⚠️  Erro no push: {e}")
        else:
            print("   ⚠️  Repositório não foi criado no GitHub")

    print()
    print("=" * 60)
    print(f"✅ Projeto '{args.project_name}' criado com sucesso!")
    print()
    print("📝 Próximos passos:")
    print(f"   1. cd {project_path}")

    if args.type == "python":
        print("   2. python -m venv venv")
        print("   3. venv\\Scripts\\activate (Windows) ou source venv/bin/activate (Linux/Mac)")
        print("   4. pip install -r requirements.txt")
    elif args.type in ["node", "react"]:
        print("   2. npm install")
        print("   3. npm start")

    print()
    print("🔗 Links:")
    print(f"   Local: {project_path}")
    if not args.no_github:
        username = run_command("gh api user -q .login", check=False)
        if username:
            print(f"   GitHub: https://github.com/{username}/{args.project_name}")
    print("=" * 60)


if __name__ == "__main__":
    main()
