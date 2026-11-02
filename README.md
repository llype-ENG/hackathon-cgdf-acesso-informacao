# BR-Access-NER

**Identificação de possíveis dados pessoais em solicitações de acesso à informação (e-SIC).**

O BR-Access-NER é um projeto de Processamento de Linguagem Natural (PLN) que utiliza reconhecimento de entidades nomeadas (NER) para localizar trechos potencialmente relacionados a dados pessoais em textos de solicitações administrativas em português.

O objetivo da versão 1 é oferecer uma ferramenta experimental de triagem: sinalizar solicitações que podem precisar de uma revisão mais cuidadosa. O modelo não substitui análise humana, não realiza anonimização automática e não determina, por si só, se uma informação deve ou não ser divulgada.

## Como funciona

A versão 1 utiliza o **BERTimbau Base** (`neuralmind/bert-base-portuguese-cased`) ajustado para uma tarefa de classificação de tokens (NER).

O treinamento utiliza o conjunto [EliMC/esic-ner](https://huggingface.co/datasets/EliMC/esic-ner), composto por documentos sintéticos em português e anotações de 13 tipos de entidade. Os textos são convertidos para o formato BIO, divididos por documento em treino, validação e teste, e usados no ajuste fino do modelo.

Na etapa de inferência, as entidades identificadas são convertidas em uma classificação binária:

- `COM DADO PESSOAL`: ao menos uma entidade pertencente às 11 categorias tratadas pelo projeto como potencialmente pessoais foi identificada.
- `SEM DADO PESSOAL IDENTIFICADO`: nenhuma entidade dessas categorias foi identificada pelo modelo.

A segunda classe não significa que o documento esteja comprovadamente livre de dados pessoais. Significa apenas que o modelo não identificou uma entidade contemplada pela regra de classificação.

## Resultados da versão 1

### Avaliação no conjunto de teste

O conjunto de teste contém 975 documentos sintéticos que não foram usados no treinamento nem na validação.

| Métrica | Resultado |
|---|---:|
| Precision (entidade) | **89,90%** |
| Recall (entidade) | **91,07%** |
| F1 (entidade) | **90,48%** |
| Acurácia por token | 99,03% |

A avaliação é feita no nível de entidade, com correspondência exata dos trechos, utilizando as anotações do conjunto de teste. A acurácia por token não deve ser confundida com a F1 de entidades.

### Experimento exploratório com 99 solicitações

O modelo também foi executado sobre uma amostra de 99 solicitações reais disponibilizada em uma planilha de teste:

| Classificação prevista | Quantidade | Percentual |
|---|---:|---:|
| COM DADO PESSOAL | 67 | 67,7% |
| SEM DADO PESSOAL IDENTIFICADO | 32 | 32,3% |
| **Total** | **99** | **100%** |

**Importante:** essa amostra não possui rótulos de referência revisados por pessoas. Portanto, os números acima representam apenas a distribuição das previsões. Não é possível calcular acurácia, precision, recall ou F1 para essas 99 solicitações, nem afirmar quantas classificações estão corretas.

A inspeção exploratória também evidenciou pontos que merecem atenção em versões futuras: números de processos ou ocorrências podem ser sinalizados mesmo quando não está claro se identificam uma pessoa natural; por outro lado, pedidos que dependem de anexos ou que descrevem uma situação pessoal sem apresentar um identificador explícito podem não ser sinalizados. A amostra contém ainda um par de textos duplicados (IDs 11 e 92), ambos com a mesma previsão.

## Categorias reconhecidas

O conjunto de dados de treinamento contém as seguintes categorias:

`ORG_JURIDICA`, `NOME_PESSOA`, `ID_PROCESSUAL`, `CONTATO`, `DOC_PESSOAL`, `DADO_SAUDE`, `ENDERECO`, `DOC_EMPRESA`, `DOC_PROFISSIONAL`, `ID_VEICULO`, `QUASI_IDENTIFICADOR`, `DADO_FINANCEIRO` e `DATA_NASC`.

Na regra binária desta versão, `ORG_JURIDICA` e `DOC_EMPRESA` não acionam sozinhas a classe positiva. As outras 11 categorias são tratadas como potencialmente pessoais. Essa é uma convenção operacional baseada nas categorias do conjunto de treinamento, não uma interpretação jurídica automática da LGPD. O contexto é importante: por exemplo, um número de processo ou uma referência a dado de saúde em estatísticas agregadas não significa necessariamente que o texto identifique uma pessoa.

## Estrutura do projeto

A organização separa código reutilizável, experimentos e artefatos locais:

```text
src/
  preprocessing/   # preparação dos dados e conversão para BIO
  training/        # treinamento e avaliação durante o ajuste
  inference/       # carregamento do modelo e predição
experiments/       # inspeções, testes e experimentos reproduzíveis
data/              # bases locais; não versionadas
models/            # checkpoints e pesos locais; não versionados
reports/
  metrics/         # métricas selecionadas para documentação
  predictions/     # previsões locais; não versionadas
```

Os diretórios e arquivos de dados, checkpoints e resultados privados são mantidos localmente e excluídos do Git por segurança e tamanho.

## Execução local

O projeto foi desenvolvido e testado em ambiente Python com PyTorch e Transformers. A instalação do PyTorch deve ser compatível com o sistema operacional, a versão do Python e, quando aplicável, a versão do CUDA instalada.

Instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

Para executar a inferência da amostra local, disponibilize o checkpoint em `models/bertimbau_esic_ner/` e a planilha de entrada `AMOSTRA_e-SIC.xlsx` na raiz do projeto. Em seguida:

```bash
python src/inference/predict.py
```

O script gera os resultados em `reports/predictions/`. **Não publique a planilha de entrada nem os arquivos de previsão derivados dela**, pois os textos podem conter dados pessoais ou sensíveis.

O fluxo de preparação e treinamento está organizado nos scripts de `src/preprocessing/` e `src/training/`. Os experimentos correspondentes estão documentados em `experiments/`.

## Limitações e uso responsável

- O desempenho de 90,48% de F1 foi medido em documentos **sintéticos** do conjunto EliMC/esic-ner. Ele não demonstra o mesmo desempenho em solicitações reais do Fala.BR ou do e-SIC.
- A amostra de 99 solicitações é exploratória e não possui rótulos de referência; não constitui uma avaliação quantitativa em dados reais.
- O modelo analisa o texto fornecido. Anexos, imagens e documentos externos não são analisados pelo script de inferência descrito aqui.
- A regra binária é sensível a erros de NER: uma entidade incorreta pode gerar um falso positivo, e uma entidade não identificada pode gerar um falso negativo.
- A saída não deve ser usada isoladamente para negar acesso à informação, decidir sobre divulgação, aplicar sanções ou afirmar que um documento está anonimizado.
- Antes de qualquer uso operacional, é necessário avaliar o modelo com dados reais adequadamente protegidos e um conjunto de referência revisado por pessoas autorizadas.

## Dados e atribuições

- **EliMC/esic-ner:** conjunto de dados sintéticos em português, disponibilizado sob licença CC-BY-4.0: https://huggingface.co/datasets/EliMC/esic-ner
- **BERTimbau Base:** modelo base `neuralmind/bert-base-portuguese-cased`: https://huggingface.co/neuralmind/bert-base-portuguese-cased

Consulte as páginas originais para os termos completos de uso e atribuição dos materiais de terceiros.

## Licenças

- **Código-fonte deste repositório:** MIT License.
- **Checkpoint publicado do modelo:** CC-BY-4.0, com atribuição às fontes e aos componentes utilizados, conforme indicado no model card do checkpoint.

As licenças do código e dos pesos do modelo são distintas. A licença de cada conjunto de dados de terceiros continua aplicável aos próprios dados.

## Próximos passos

A versão 1 estabelece uma linha de base funcional. As próximas melhorias devem priorizar a redução de falsos positivos em identificadores administrativos, a distinção entre informação pessoal e estatística agregada, a avaliação em dados reais com referência confiável e a calibração da regra de classificação binária.
