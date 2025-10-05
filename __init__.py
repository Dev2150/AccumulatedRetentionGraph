from anki.utils import pointVersion
from .src.main_screen_integration import init_main_screen_hooks

# ===== INÍCIO DA INTEGRAÇÃO COM TELA PRINCIPAL =====

# Verificação de versão do Anki
anki_version = pointVersion()
print(f"Accumulated Retention Graph: Anki version detected - {anki_version}")

# Verificar se é uma versão compatível
if anki_version >= 256000:  # Anki 25.6+
    print("Accumulated Retention Graph: Running on Anki 25.6+ (new versioning)")
elif anki_version >= 231000:  # Anki 23.10+
    print("Accumulated Retention Graph: Running on Anki 23.10+ (new versioning)")
elif anki_version >= 45:  # Anki 2.1.45+
    print("Accumulated Retention Graph: Running on Anki 2.1.45+ (legacy versioning)")
else:
    print(f"Accumulated Retention Graph: Warning - Running on older Anki version {anki_version}. This addon may not work properly.")

# Inicializar hooks da tela principal
try:
	init_main_screen_hooks()
except Exception as e:
	print(f"Card Evolution: Erro ao inicializar hooks da tela principal: {e}")

# ===== FIM DA INTEGRAÇÃO COM TELA PRINCIPAL =====
