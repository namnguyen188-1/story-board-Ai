import re

def patch():
    path = "D:/STORYBOARD_AI/studio/mcp_v2_batch.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    old_clean_clone = """        # STOIC SPECIFIC ENFORCEMENT: Never mix statue and living human! All Stoic scenes are 100% pure classical marble statue!
        if is_stoic:
            clean_clone = (
                "Monumental heroic classical sculpted Carrara marble and antique bronze statue of Stoic philosopher emperor Marcus Aurelius, "
                "deeply chiseled stone anatomy, massive sculpted bare stone shoulder and pectoral chest, thick muscular stone neck, "
                "deeply carved curly stone beard and hair, sculpted stone eyes, "
                "wearing royal crimson red draped toga (chlamys) carved cascading over one stone shoulder. "
                "Authentic weathered Carrara marble texture with subtle historical fissure lines and smooth chisel marks. "
                "100% pure carved classical stone sculpture throughout, never living human flesh, never real skin pores, never vascular veins, never modern clothes"
            )
            scene_desc = re.sub(r'(?i)\\b(a\\s+)?(living\\s+)?(man|person|figure)\\b', 'the classical marble statue', scene_desc)"""

    new_clean_clone = """        # STOIC SPECIFIC ENFORCEMENT: Never mix statue and living human! All Stoic scenes are 100% pure classical marble statue!
        if is_stoic:
            clean_clone = (
                "Monumental heroic classical sculpted Carrara marble and antique bronze statue of Stoic philosopher emperor Marcus Aurelius, "
                "intact complete head with deeply carved curly stone beard and hair, sculpted stone eyes, dignified stoic expression, "
                "deeply chiseled stone anatomy, massive sculpted broad stone shoulders and pectoral chest, thick muscular stone neck, "
                "intact stone arms, wearing royal crimson red draped toga (chlamys) carved cascading over one stone shoulder. "
                "Authentic weathered Carrara marble texture with subtle historical fissure lines and smooth chisel marks. "
                "100% pure carved classical stone sculpture throughout, never living human flesh, never real skin pores, never vascular veins, "
                "never headless, never severed head, never missing face, never cut off at neck, never modern clothes"
            )
            scene_desc = re.sub(r'(?i)\\b(a\\s+)?(living\\s+)?(man|person|figure)\\b', 'the classical marble statue', scene_desc)
            if rules:
                rules = re.sub(r'(?i)\\b(living|human\\s+flesh|bronze\\s+skin|real\\s+skin|skin\\s+pores|vascular|veins)\\b', '', rules).strip(', ')"""

    if old_clean_clone not in content:
        print("ERROR: old_clean_clone not found!")
        return False
    content = content.replace(old_clean_clone, new_clean_clone)

    old_pecs = "'cinematic medium shot of hyper-muscular classical Carrara marble statue with colossal broad shoulders, sculpted chest pecs, and 6-pack abs'"
    new_pecs = "'cinematic medium shot of classical Carrara marble statue of Marcus Aurelius with intact bearded head, sculpted stone eyes, colossal broad stone shoulders, and sculpted chest pecs'"
    if old_pecs not in content:
        print("ERROR: old_pecs not found!")
        return False
    content = content.replace(old_pecs, new_pecs)

    old_bust = "'hyper-muscular marble statue with sculpted pectoral chest, striated deltoids, and 6-pack abs'"
    new_bust = "'magnificent intact classical Carrara marble statue with sculpted bearded head, stone eyes, broad stone shoulders, and draped crimson toga'"
    if old_bust not in content:
        print("ERROR: old_bust not found!")
        return False
    content = content.replace(old_bust, new_bust)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: mcp_v2_batch.py patched successfully!")
    return True

if __name__ == "__main__":
    patch()
