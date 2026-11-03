"""Reject ASR phantom duplicated tail only when SILERO confirms silence.
Do not synthesize word timestamps or make silence look like speech.
"""
from pathlib import Path
p=Path(r"D:\STORYBOARD_AI\studio\cinematic_engine\native_audio_subtitles.py")
s=p.read_text(encoding="utf-8")
marker='def validate_words(words, duration):'
func='''def strip_vad_proven_repeated_silence_tail(data):
    """Trim an exact repeated ASR phrase wholly outside VAD speech, never a real utterance.

    Stable Whisper may hallucinate a repeated phrase after all speech has ended,
    returning several words with the same zero-length timestamp. Reject these
    only when the repeated tail exactly matches already transcribed speech,
    starts beyond a VAD-confirmed silent boundary, and the earlier phrase has
    valid spoken anchors. All other bad alignments still fail closed.
    """
    words = list(data.get("words") or [])
    intervals = list(data.get("speech_intervals") or [])
    if len(words) < 4 or not intervals:
        return data
    last_speech_end = max(float(v["end"]) for v in intervals)
    boundary = last_speech_end + 0.12
    cut = next((i for i, w in enumerate(words)
                if float(w.get("start", 0)) > boundary),len(words))
    head, tail = words[:cut], words[cut:]
    if len(head) < 2 or len(tail) < 2 or len(tail) > len(head):
        return data
    if any(float(w.get("start", 0)) <= boundary for w in tail):
        return data
    def normalized(items):
        return [str(w.get("word", "")).casefold().strip(".,?!…;: ") for w in items]
    if normalized(tail) != normalized(head[-len(tail):]):
        return data
    # Confirm the source phrase overlaps a VAD speech interval, not another
    # hallucination. VAD timestamps are in original clip seconds.
    if not all(any(float(v["start"])-0.12 <=
                   (float(w["start"])+float(w["end"]))/2 <= float(v["end"])+0.12
                   for v in intervals) for w in head[-len(tail):]):
        return data
    data["raw_recognized_transcript"] = data.get("transcript", "")
    data["words"] = head
    data["transcript"] = " ".join(str(w["word"]) for w in head)
    expected = str(data.get("expected_text") or "")
    if expected:
        data["script_mismatch"] = tokens(data["transcript"]) != tokens(expected)
    data["asr_silence_tail_filtered"] = {
        "reason":"Exact repeated ASR tokens outside the last VAD speech interval",
        "discarded_phantom_word_count":len(tail),
        "source_speech_end":last_speech_end
    }
    return data

'''
assert marker in s
s=s.replace(marker,func+marker,1)
needle='''        data = json.loads(output.read_text(encoding="utf-8"))
        try:
            data["words"] = validate_words(data.get("words", []), duration)'''
rep='''        data = json.loads(output.read_text(encoding="utf-8"))
        data = strip_vad_proven_repeated_silence_tail(data)
        try:
            data["words"] = validate_words(data.get("words", []), duration)'''
assert needle in s
s=s.replace(needle,rep,1)
p.write_text(s,encoding="utf-8")
print("VAD_GATED_DUPLICATE_HALLUCINATION_FIX_INSTALLED",flush=True)
