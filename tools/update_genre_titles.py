"""Update titles_es and titles_vi in seo_genre_profiles.py."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
gp_p = ROOT / "studio" / "seo_genre_profiles.py"
gp_text = gp_p.read_text(encoding="utf-8")

old_es_chunk = """        "titles_es": [
            "El hábito brutal de Marco Aurelio que destruirá tu pereza (Episodio {episode_num})",
            "Estás desperdiciando tu vida y no te das cuenta: Lección de {subj}",
            "La regla estoica de los 3 segundos para no volver a posponer nada jamás",
            "Por qué los sabios estoicos nunca pierden la calma | La verdad de {subj}",
            "Deja de regalar tu tiempo a quien no le importa: Sabiduría de {subj} (Capítulo {episode_num})",
        ],"""

new_es_chunk = """        "titles_es": [
            "SUELTA LO QUE NO PUEDES CONTROLAR Y LA ANSIEDAD SE IRÁ SOLA | 10 LECCIONES DE ESTOICISMO",
            "ALÉJATE EN SILENCIO Y QUIEN TE TRATÓ COMO UNA OPCIÓN VOLVERÁ A BUSCARTE | ESTOICISMO",
            "DEJA DE DAR EXPLICACIONES A TODO EL MUNDO Y EMPEZARÁN A RESPETARTE | ESTOICISMO",
            "CUANTO MENOS TE PREOCUPES, MEJOR TE IRÁ | 12 LECCIONES DE ESTOICISMO",
            "MANTÉN LA CALMA Y LA VIDA TE TRAERÁ TODO LO QUE ES TUYO | ESTOICISMO",
            "TU SILENCIO IMPONE RESPETO: LA VERDAD QUE NADIE TE DICE | ESTOICISMO",
        ],"""

if old_es_chunk in gp_text:
    gp_text = gp_text.replace(old_es_chunk, new_es_chunk, 1)
    print("Updated titles_es in seo_genre_profiles.py")
else:
    print("[WARN] old_es_chunk not found")

gp_p.write_text(gp_text, encoding="utf-8")
print("Finished updating seo_genre_profiles.py!")
