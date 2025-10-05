from anki import stats
from anki.hooks import wrap
from aqt import mw
from .rendering import render_card_evolution_graph

# Tentar usar cardGraph (sem underscore)
TARGET_METHOD_NAME = "cardGraph"
BACKUP_ATTR_NAME = "_cardGraph_original_by_evolution_addon" # Manter nome do backup para consistência

def add_evolution_graph_to_card_stats(self_instance, *original_args, **original_kwargs):
    """
    Wraps the original cardGraph method to append the evolution graph.
    This version assumes the wrapper is called with only (self, *args, **kwargs) by the hook system,
    and the original method is retrieved from our backup.

    `self_instance` is the CollectionStats instance.
    `original_args` and `original_kwargs` are arguments for the original method (likely none for cardGraph).
    """
    original_card_graph_html = ""

    original_method_ref = getattr(stats.CollectionStats, BACKUP_ATTR_NAME, None)

    if original_method_ref:
        # Clean up kwargs for the original cardGraph call
        # cardGraph() typically only takes self.
        # Another addon seems to be injecting '_old' into the kwargs.
        cleaned_kwargs = original_kwargs.copy()
        if '_old' in cleaned_kwargs:
            del cleaned_kwargs['_old']

        # The original cardGraph() method does not accept *args or **kwargs beyond self.
        # So, we should call it with only self_instance if original_args and cleaned_kwargs are empty.
        # However, to be safe and pass through what was given (minus _old):
        try:
            original_card_graph_html = original_method_ref(self_instance, *original_args, **cleaned_kwargs)
        except TypeError as e:
            # This might happen if original_args is not empty or cleaned_kwargs still has unexpected items.
            try:
                original_card_graph_html = original_method_ref(self_instance)
            except Exception as e2:
                original_card_graph_html = "<!-- Original graph failed to load -->"

    else:
        original_card_graph_html = "<!-- Original graph could not be determined -->"

    evolution_graph_html = render_card_evolution_graph(self_instance)

    config = mw.addonManager.getConfig(__name__)
    show_at_beginning = config.get("show_at_beginning") # False por padrão (mostrar ao final)

    if show_at_beginning:
        # Mostrar o gráfico de evolução ANTES do gráfico original
        return evolution_graph_html + original_card_graph_html
    else:
        # Mostrar o gráfico de evolução DEPOIS do gráfico original (comportamento padrão)
        return original_card_graph_html + evolution_graph_html

# Guardar uma referência ao método original, se ainda não foi guardada por este addon
if hasattr(stats.CollectionStats, TARGET_METHOD_NAME) and not hasattr(stats.CollectionStats, BACKUP_ATTR_NAME):
	setattr(stats.CollectionStats, BACKUP_ATTR_NAME, getattr(stats.CollectionStats, TARGET_METHOD_NAME))
elif not hasattr(stats.CollectionStats, TARGET_METHOD_NAME):
	pass

# Aplicar o wrap apenas se o método original e o backup existirem
if hasattr(stats.CollectionStats, TARGET_METHOD_NAME) and hasattr(stats.CollectionStats, BACKUP_ATTR_NAME):
	current_target_method_func = getattr(stats.CollectionStats, TARGET_METHOD_NAME)
	original_backup_func = getattr(stats.CollectionStats, BACKUP_ATTR_NAME)

	# Desfazer o wrap se o método alvo não for já o original (ou seja, se já foi envolvido por nós)
	if current_target_method_func != original_backup_func:
		setattr(stats.CollectionStats, TARGET_METHOD_NAME, original_backup_func)

	# Aplicar o wrap
	setattr(stats.CollectionStats, TARGET_METHOD_NAME, wrap(
		original_backup_func, # Envolver o original que guardamos
		add_evolution_graph_to_card_stats,
		"around"
	))