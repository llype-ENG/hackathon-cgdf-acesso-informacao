from services.regex_service import detect_regex

texto = """
Boa tarde! Gostaria de consultar o andamento do processo nº 589642/2018-58 realizado em 02/09/2018, solicitando a isenção da TFE ref. o ano 2018 da empresa CARLA PATRICIA GONÇALVES LTDA CNPJ: 25.598.301/0001-68. Solicitação realizada presencialmente na unidade da Terracap na Adm. do Jardim Botânico/DF.   Desde já agradeço.
"""
r = detect_regex(texto)
print(r.keys())
print(r)
