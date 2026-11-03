# Storyboard Studio — MCP V2 real-image smoke test (2026-10-11)

STATUS: LIVE_IMAGE_QC_PASS (ONE IMAGE)

- Used existing Google Flow Storyboard Director MCP from D:\FLOW_MCP_SERVER, accessed via V2 read-only adapter.
- Model: Nano Banana 2 Lite (fallback disabled); scene from Episode 1 "The City That Lost Time".
- Health: native=true, sdk_image=true, image_capability=true, queue_count=1, running=false.
- MCP validation required output directory under D:\YOUTUBE_SEO_PRO_V2\outputs\projects; first isolated Studio-root attempt was rejected before generation.
- Set bounded approval flags only in the independent test process: one image.
- Real job submitted and receipt generated. Source file was placed in a NEW, isolated canary subfolder under V2 outputs/projects; no V2 source or configuration edits.
- Result copied to D:\STORYBOARD_AI\studio\mcp_image_test_result\city_lost_time_mcp_scene_001.jpg.
- Model response: 1376x768 JPEG, 365560 bytes. PIL verify PASS.
- Python V2 backend _verify completed receipt and SHA256 integrity check PASS; source/copy hashes match. Journal state completed. Only one job exists in successful test scope.
- The test command printed a UnicodeEncodeError when trying to display the banana emoji on a CP1252 console AFTER the image had already been successfully generated and copied. Separate QC-only command returned exit code 0 and validated all media.
- DO NOT repeat generation for this canary; receipt is already complete.
- No overall film pipeline was tested with MCP image as a GUI-selected provider yet. Integration into Storyboard AI Studio remains a separate engineering task.
- Cost/credit: The current actual credit deduction was NOT observed. Prior V2 UI metadata suggested 0 credit for image generation but this has NOT been independently revalidated in this run.
