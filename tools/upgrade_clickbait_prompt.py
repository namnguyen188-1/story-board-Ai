"""Patch studio/seo_packager.py with the aggressive high-CTR Valor Estoico title formula."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
sp_p = ROOT / "studio" / "seo_packager.py"
sp_text = sp_p.read_text(encoding="utf-8")

old_title_rules = """CRITICAL TITLE RULES:
1. DO NOT copy hashtags (#shorts, #estoicismo) or emoji icons (👆, 🔺, 🔥, 💀) into titles.
2. Produce 3 distinct, high-CTR, scroll-stopping viral titles in {ctx['language']} reflecting the actual lesson/story:
   - Style 1: Curiosity Gap & Brutal Truth (Psychological scroll-stopper that exposes a costly mistake or hidden truth).
   - Style 2: Wake-up Call & Warning (Urgent existential warning or powerful counter-intuitive realization).
   - Style 3: The Actionable Rule / Secret (Timeless rule or mental framework from masters like Marcus Aurelius, Seneca, or Epictetus).
   - Keep episode branding short or at the end. Maximum 95 characters.
3. Topic Guidance: {clean_ref} (Reference only; NEVER copy blindly)."""

new_title_rules = """CRITICAL TITLE RULES:
1. FORMULA MANDATE: YouTube titles MUST follow the aggressive viral formula from top competitor channels like 'Valor Estoico':
   [PROVOCATIVE EMOTIONAL HOOK IN ALL CAPS] | [X LECCIONES / BÀI HỌC VỀ] [KEYWORD IN ALL CAPS]
   Real million-view reference formulas to replicate:
   - "SUELTA LO QUE NO PUEDES CONTROLAR Y LA ANSIEDAD SE IRÁ SOLA | 10 LECCIONES DE ESTOICISMO"
   - "ALÉJATE EN SILENCIO Y QUIEN TE TRATÓ COMO UNA OPCIÓN VOLVERÁ A BUSCARTE | ESTOICISMO"
   - "DEJA DE DAR EXPLICACIONES A TODO EL MUNDO Y EMPEZARÁN A RESPETARTE | ESTOICISMO"
   - "CUANTO MENOS TE PREOCUPES, MEJOR TE IRÁ | 12 LECCIONES DE ESTOICISMO"
   - "MANTÉN LA CALMA Y LA VIDA TE TRAERÁ TODO LO QUE ES TUYO | ESTOICISMO"
2. Produce 3 distinct, high-CTR viral titles matching this exact formula in {ctx['language']}:
   - Style 1: Brutal Truth & Detachment Hook (e.g. SUELTA Y DEJA BRILLAR / ALÉJATE EN SILENCIO...)
   - Style 2: Existential Boundary & Respect Hook (e.g. TU SILENCIO IMPONE RESPETO / DEJA DE JUSTIFICARTE...)
   - Style 3: Calm & Mastery Hook (e.g. CUANTO MENOS TE PREOCUPES, MEJOR TE IRÁ...)
   - NEVER output soft, academic, passive, or textbook titles (no boring colons or weak phrases).
   - Maximum 90 characters for full mobile visibility.
3. Topic Guidance: {clean_ref} (Reference only; adapt with viral power)."""

assert old_title_rules in sp_text, "old_title_rules not found in seo_packager.py"
sp_text = sp_text.replace(old_title_rules, new_title_rules, 1)

sp_p.write_text(sp_text, encoding="utf-8")
print("seo_packager.py successfully upgraded with aggressive Valor Estoico clickbait prompt!")
