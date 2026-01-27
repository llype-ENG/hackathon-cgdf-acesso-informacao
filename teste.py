from services.regex_service import RegexService
from services.classifier import classify
import json

text = """Me chamo Thiago, sou formando em engenharia ambiental na Universidade de São Paulo e estou desenvolvendo meu projeto final em um estudo exploratório acerca da bacia hidrográfica do Ribeirão Bananal, sob orientação do professor Pablo Souza Ramos. Para dar continuidade ao projeto, preciso ter acesso aos dados monitorados pela estação de monitoramento do Lago Norte. Preciso dos dados de vazão e qualidade da água (Clorofila-a, Coliformes Termotolerantes, DBO, Fósforo Total, Nitrogênio Amoniacal, Nitrogênio Total, Oxigênio Dissolvido, pH, Sólidos Totais, Temperatura da Amostra, Turbidez), desde 2021 a data atual. Entrei em contato com o Eduardo do Setor de Recursos Hídricos e ela me orientou a enviar esse email para solicitar os dados. Me informou também que os dados estão disponíveis no Power Bi da Adasa, no entanto preciso em formato tabular, para devida manipulação dos dados."""
# =========================
# TESTE REGEX
# =========================
service = RegexService()
regex_result = service.detect(text)

print("=== REGEX RESULT ===")
print(json.dumps(regex_result, indent=2, ensure_ascii=False))

# =========================
# TESTE CLASSIFIER
# =========================
classification_result = classify(text)

print("\n=== CLASSIFIER RESULT ===")
print(json.dumps(classification_result, indent=2, ensure_ascii=False))
