BR-Access-NER
Refatoração e evolução do projeto desenvolvido no Hackathon da CGDF — acesso à informação.

O BR-Access-NER dá continuidade ao trabalho iniciado no Hackathon da Controladoria-Geral do Distrito Federal (CGDF), cujo contexto é o acesso à informação. Este repositório não representa um projeto criado do zero: ele organiza e refatora tecnicamente a solução do hackathon, separando o código em etapas mais claras e preparando a base para evolução, experimentação e manutenção.

A refatoração também incorpora uma frente de Processamento de Linguagem Natural (PLN) para reconhecer entidades que podem estar relacionadas a dados pessoais em solicitações administrativas de acesso à informação. A versão 1 utiliza NER (Named Entity Recognition) com BERTimbau e uma regra derivada para classificação binária de documentos.
Escopo da v1: identificar e sinalizar possíveis dados pessoais para apoiar a triagem. O modelo não substitui análise humana, não realiza anonimização automática e não decide se uma informação deve ou não ser divulgada.

Origem e objetivo da refatoração
O ponto de partida deste trabalho foi o projeto desenvolvido no Hackathon da CGDF, relacionado ao tema de acesso à informação. A proposta desta etapa é transformar a implementação inicial em uma estrutura de projeto mais organizada e reproduzível, com responsabilidades separadas para:
- preparação e transformação dos dados;
- treinamento e avaliação do modelo de NER;
- inferência sobre novas solicitações;
- experimentos e relatórios separados do código reutilizável.
Assim, o BR-Access-NER preserva o contexto do hackathon e desenvolve tecnicamente uma parte da solução, com foco na identificação de possíveis dados pessoais em textos de pedidos e-SIC. A refatoração não deve ser interpretada como uma validação institucional, homologação ou implantação oficial pela CGDF.
Como funciona
A versão 1 utiliza o BERTimbau Base (neuralmind/bert-base-portuguese-cased) ajustado para classificação de tokens no formato BIO, tarefa utilizada para reconhecimento de entidades nomeadas.

O treinamento utiliza o conjunto EliMC/esic-ner, composto por documentos sintéticos em português e anotações de 13 tipos de entidade. O fluxo de preparação converte as anotações para BIO, divide os documentos em treino, validação e teste e prepara os arquivos para o fine-tuning.

Na inferência, o modelo identifica entidades no texto. Em seguida, uma regra transforma as entidades previstas em uma classificação binária:
- COM DADO PESSOAL: pelo menos uma entidade de uma das 11 categorias tratadas pelo projeto como potencialmente pessoais foi identificada;
- SEM DADO PESSOAL IDENTIFICADO: nenhuma entidade dessas categorias foi identificada pelo modelo.
A segunda classe não comprova que o documento esteja livre de dados pessoais. Ela indica somente que o modelo não identificou uma entidade contemplada pela regra binária.
Resultados da versão 1
Avaliação no conjunto de teste
O conjunto de teste possui 975 documentos sintéticos, mantidos separados dos dados utilizados no treinamento e na validação.
Métrica	Resultado
Precision (entidade)	89,90%
Recall (entidade)	91,07%
F1 (entidade)	90,48%
Acurácia por token	99,03%


A avaliação de NER considera a correspondência exata das entidades previstas com as anotações de referência. A acurácia por token não deve ser interpretada como F1 de entidades.
Experimento exploratório com 99 solicitações
Também foi executada uma inferência sobre uma amostra de 99 solicitações reais fornecida em uma planilha local:
Classificação prevista	Quantidade	Percentual
COM DADO PESSOAL	67	67,7%
SEM DADO PESSOAL IDENTIFICADO	32	32,3%
Total	99	100%


Essa amostra não possui rótulos de referência revisados por pessoas. Portanto, os valores representam a distribuição das previsões do modelo, não a quantidade de acertos. Não é possível calcular acurácia, precision, recall ou F1 para essas 99 solicitações.

A análise exploratória indicou situações que merecem atenção em versões futuras, como números de processos e referências a estatísticas agregadas. Dependendo do contexto, esses trechos podem não identificar uma pessoa natural. Também existem solicitações cujo contexto está em anexos ou em descrições indiretas, o que pode limitar uma análise baseada apenas no texto disponível.

Privacidade: a planilha utilizada nesse experimento e os arquivos de previsões derivados dela não fazem parte do repositório público. Textos de solicitações podem conter dados pessoais ou sensíveis, mesmo quando a planilha ou coluna de origem utiliza a expressão “texto mascarado”.
Categorias reconhecidas
O conjunto de treinamento contém 13 categorias:

ORG_JURIDICA, NOME_PESSOA, ID_PROCESSUAL, CONTATO, DOC_PESSOAL, DADO_SAUDE, ENDERECO, DOC_EMPRESA, DOC_PROFISSIONAL, ID_VEICULO, QUASI_IDENTIFICADOR, DADO_FINANCEIRO e DATA_NASC.

Na regra binária da v1, ORG_JURIDICA e DOC_EMPRESA não acionam sozinhas a classe positiva. As outras 11 categorias são tratadas como potencialmente pessoais. Essa é uma convenção operacional baseada nas categorias do conjunto de treinamento, não uma interpretação jurídica automática da LGPD. O contexto de cada informação continua sendo relevante.
Estrutura do projeto
A organização busca separar código reutilizável, experimentos e artefatos locais:
src/
  preprocessing/   # consolidação e preparação dos dados; conversão para BIO e split
  training/        # treinamento do modelo NER
  inference/       # carregamento do modelo, reconhecimento e classificação
experiments/       # inspeções, testes e experimentos reproduzíveis
data/
  raw/             # dados originais locais
  external/        # conjuntos externos locais
  interim/         # dados intermediários
  processed/       # dados processados
models/            # checkpoints e pesos locais
reports/
  metrics/         # métricas selecionadas para documentação
  predictions/    # previsões locais, não versionadas
  private/         # relatórios e amostras privadas, não versionados
Os dados, checkpoints, planilhas e resultados locais não devem ser enviados ao GitHub. O .gitignore protege esses caminhos, mas é necessário conferir se algum arquivo já está sendo rastreado pelo Git antes de realizar um commit.
Instalação e execução
O projeto foi desenvolvido em Python e utiliza PyTorch e Transformers. A instalação do PyTorch deve ser compatível com o sistema operacional e, quando aplicável, com a versão do CUDA e a GPU disponíveis.

Crie e ative um ambiente virtual e instale as dependências:
python -m venv .venv
No Windows PowerShell:
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Para ambientes com GPU NVIDIA, instale a versão do PyTorch apropriada ao seu ambiente seguindo o seletor oficial: https://pytorch.org/get-started/locally/ . A versão CUDA não deve ser presumida apenas pela presença de uma GPU NVIDIA.
Executar a inferência
Para executar src/inference/predict.py, disponibilize:
1. o checkpoint treinado em models/bertimbau_esic_ner/;
2. a planilha de entrada AMOSTRA_e-SIC.xlsx na raiz do projeto, com as colunas ID e Texto Mascarado.
Execute:
python -u src/inference/predict.py
O script gera arquivos de classificação em reports/predictions/. Não publique a planilha de entrada nem as previsões derivadas dela.

O fluxo completo de preparação e treinamento utiliza os scripts de src/preprocessing/ e src/training/. Os experimentos e verificações ficam em experiments/.
Limitações e uso responsável
- O F1 de 90,48% foi medido em documentos sintéticos do conjunto EliMC/esic-ner. Não demonstra o mesmo desempenho em solicitações reais do Fala.BR ou do e-SIC.
- As 99 solicitações reais formam um experimento exploratório sem rótulos de referência; não constituem uma avaliação quantitativa de desempenho em dados reais.
- A inferência descrita analisa o texto fornecido. Anexos, imagens e documentos externos não são analisados pelo script.
- Uma entidade identificada incorretamente pode gerar falso positivo; uma entidade não identificada pode gerar falso negativo.
- A regra binária não determina, por si só, se existe dado pessoal em sentido jurídico nem se uma solicitação deve ser restringida ou divulgada.
- A saída não deve ser usada isoladamente para negar acesso à informação, decidir sobre divulgação, aplicar sanções ou afirmar que um documento está anonimizado.
- Antes de qualquer uso operacional, é necessária avaliação com dados reais adequadamente protegidos e um conjunto de referência construído por pessoas autorizadas.
Fontes e atribuições
- Projeto de origem: trabalho desenvolvido no Hackathon da CGDF, no contexto de acesso à informação. Este repositório apresenta uma refatoração e evolução técnica desse trabalho.
- Conjunto de dados: EliMC/esic-ner, conjunto sintético em português disponibilizado sob licença CC-BY-4.0.
- Modelo base: BERTimbau Base, de neuralmind.
Consulte as páginas originais para os termos completos de uso e atribuição dos materiais de terceiros.
Licenças
- Código-fonte deste repositório: MIT License.
- Checkpoint publicado do modelo: CC-BY-4.0, com as atribuições indicadas no model card.
As licenças do código, do checkpoint e dos materiais de terceiros são distintas. A licença do repositório não altera as condições aplicáveis aos conjuntos de dados ou modelos de terceiros.
Próximos passos
A v1 estabelece uma base técnica organizada a partir do projeto do Hackathon da CGDF. A evolução planejada inclui reduzir falsos positivos em identificadores administrativos, diferenciar melhor informação pessoal de estatísticas agregadas, ampliar a avaliação com dados reais protegidos e aprimorar a regra de classificação binária.