from services.regex_service import detect_regex

texto = """
Bom dia,   Eu ja tenho a viabilidade aprovada. porém a junta me pede para eu fazer uma nova viabilidade alegando o nome da empresa!  neste caso o número protocolo integrado vai mudar e a taxa foi paga como faço para aproveitamento a viabilidade aprovada e só atualizar o nome e as exigência da junta comercial. Pois pelo que eu entendo para eu fazer uma nova viabilidade tenho que cancelar a que está vigente, fazer uma nova com certeza terá outro número e como vou fazer com a taxa paga.  motivo pendência nota explicativa 1. corrigir nire: 7893214568-7 89- prezado senhor usuário, orientamos fazer uma nova viabilidade de nome empresarial e retirar o ( 01 ) constante após a natureza jurídica do nome empresarial  CO S DE E Ltda  Preciso de orientação em referencia a taxa que foi pago com o protocolo DFP4568523652, COMO MANTER ENTE NUMERO"""
r = detect_regex(texto)
print(r.keys())
print(r)
