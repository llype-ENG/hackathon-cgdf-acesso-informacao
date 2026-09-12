# hackathon-cgdf-acesso-informacao

Projeto para classificação de propostas como públicas ou não públicas, com foco em identificação de dados pessoais sensíveis.

Estrutura atual

- app/domain
  - regras de negócio e modelos de domínio
  - ClassificationResult
  - ClassificationRule
  - RegexPersonalDataRule
  - NlpRiskRule
- app/application
  - ClassificationService
- app/infrastructure
  - ModelLoader
  - ExcelClassificationRepository
- app/presentation
  - UI de seleção de planilha
- main.py
  - entrypoint do processamento de planilha
- train.py
  - treinamento do modelo
- tests/
  - testes de regressão para classificação

Instalação

pip install -r requirements.txt

Fluxo principal

1. Carrega as regras de classificação.
2. Aplica regex para detectar dados pessoais explícitos.
3. Se não houver coincidência, usa modelo NLP para risco indireto.
4. Processa planilha Excel e exporta resultado.
