from services.regex_service import detect_regex

texto = """
Prezados!
Gostaria de solicitar a declaração de exercício findo da servidora AURA Costa Mota.
Att., Rafael
"""

print(detect_regex(texto))
