from pathlib import Path
p = Path("studio/thumbnail_studio.py")
txt = p.read_text(encoding="utf-8")

old_prompt = """        "subject_prompt": (

            "Monumental heroic live-action chest-up cinematic portrait of a chiseled Roman Emperor philosopher ({char_desc}), "

            "weathered sun-kissed bronze skin, intense piercing expressive eyes with alive pupils, muscular neck and detailed salt-and-pepper curly beard, "

            "wearing a vibrant royal crimson red draped toga (chlamys) over one shoulder, golden rim lighting outlining sculpted features and curls, "

            "magnificent illuminated ancient Athens Acropolis and Parthenon on distant rocky hill in deep starry night sky with glowing emerald teal aurora borealis and floating golden embers, "

            "subject strictly occupying 50% on the RIGHT half facing towards the left, leaving the entire LEFT 50% open deep twilight atmospheric sky for bold typography, "

            "never full body, never standing on pedestal, never distant figure, never lifeless stone statue, hyper-realistic 8k masterpiece film still, cinematic lighting, no text, no watermark."

        ),"""

new_prompt = """        "subject_prompt": (
            "Monumental heroic classical sculpted dark marble and antique bronze statue of a Stoic philosopher god ({char_desc}), "
            "deeply chiseled stone anatomy, massive sculpted bare shoulder and pectoral chest, thick muscular neck, deeply carved curly stone beard and hair, sculpted classical statue eyes, "
            "wearing a vibrant royal crimson red draped toga (chlamys) over one shoulder, warm golden firelight rim lighting outlining sculpted rock muscles, "
            "magnificent illuminated ancient Athens Acropolis and Parthenon on distant rocky hill in deep starry night sky with glowing emerald teal aurora borealis and floating golden embers, "
            "sculpture strictly occupying 50% on the RIGHT half facing towards the left, leaving the entire LEFT 50% open deep twilight atmospheric sky for bold typography, "
            "chest-up low-angle framing, never full body, never standing on distant pedestal, photorealistic 8k render of a monumental classical sculpture, cinematic lighting, no text, no watermark."
        ),"""

assert old_prompt in txt, "old_prompt not found in thumbnail_studio.py"
p.write_text(txt.replace(old_prompt, new_prompt, 1), encoding="utf-8")
print("Updated thumbnail_studio.py subject_prompt to classical sculpted statue!")
