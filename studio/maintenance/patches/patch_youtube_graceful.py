from pathlib import Path
import shutil,datetime,py_compile
r=Path(r"D:\STORYBOARD_AI\studio")
p=r/"studio_input_modes.py"
cp=r/"checkpoints"/("link_graceful_503_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
cp.mkdir(parents=True,exist_ok=True)
shutil.copy2(p,cp/p.name)
s=p.read_text(encoding="utf-8")
a='''    response=client.models.generate_content(
        model=model,
        contents=types.Content(parts=['''
b='''    try:
        response=client.models.generate_content(
            model=model,
            contents=types.Content(parts=['''
assert a in s
s=s.replace(a,b,1)
a='''        config={"response_mime_type":"application/json"}
    )
    try:
        result=json.loads(response.text)'''
b='''            config={"response_mime_type":"application/json"}
        )
    except Exception as exc:
        from resilient_gemini import status_code
        code=status_code(exc)
        if code in (429,500,502,503,504):
            raise RuntimeError(
                "VIDEO_REFERENCE_SERVICE_UNAVAILABLE: Gemini không phân tích "
                "được YouTube lúc này (HTTP "+str(code)+"). Hãy thử lại khi "
                "dịch vụ ổn định, hoặc chọn Kịch bản có sẵn / Ý tưởng. "
                "Studio không tự bịa nội dung từ link."
            ) from exc
        raise RuntimeError(
            "VIDEO_REFERENCE_REJECTED: không thể đọc video công khai. "
            "Kiểm tra liên kết, quyền truy cập và API key."
        ) from exc
    try:
        result=json.loads(response.text)'''
assert a in s
s=s.replace(a,b,1)
p.write_text(s,encoding="utf-8")
py_compile.compile(str(p),doraise=True)
print("YOUTUBE_ERROR_MESSAGE_COMPILE_PASS",str(cp),flush=True)
