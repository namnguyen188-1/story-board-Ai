from pathlib import Path
import datetime,hashlib,json
root=Path(r"D:\STORYBOARD_AI\studio")
source=root/"seo_packager.py"
orig=source.read_bytes()
assert orig.count(b"\r\n")==orig.count(b"\n")
s=orig.decode("utf8").replace("\r\n","\n")
old='''    # Generate once through MCP V2. Never switch providers/models after denial.
    try:
        from mcp_v2_images import make_image
        make_image(prompt, out_base, series=series_name or ep_title, episode=1,
                   scene=9999 if is_short else 9998, max_new_images=1,
                   model_index=0, fallback=False, aspect_ratio=target_ratio)
        backend_used = "mcp_v2"
    except Exception as exc:
        return {"ok": False, "error": str(exc), "backend": "mcp_v2",
                "aspect_ratio": target_ratio, "is_short": is_short}'''
new='''    # Prepare a verified, pinned production session for each thumbnail.
    # The Web Tool may still show the last completed image; health alone does
    # not reserve/clear that old queue, and direct render_batch would be refused.
    pinned_target = None
    receipt_ok = False
    try:
        from mcp_v2_images import make_image
        from studio_mcp.accounts import active_account, account_tool_url
        from studio_mcp.production_tab import prepare, close_completed, abandon_fresh
        from studio_mcp.transport import LocalFlowMcpTransport
        from studio_mcp.image_backend import StoryboardImageTransport, validate_image_tool_readiness
        account = active_account()
        url = account_tool_url(account)
        if not url:
            raise RuntimeError("THUMBNAIL_MCP_TOOL_URL_MISSING")
        pinned_target = prepare(account, url)
        transport = StoryboardImageTransport(
            mcp=LocalFlowMcpTransport(target_id=pinned_target), tool_url=url)
        validate_image_tool_readiness(
            transport("health"), require_queue=True,
            scoped_production_target=pinned_target)
        # One job, one model, no fallback, no automatic resubmission.
        make_image(prompt, out_base, series=series_name or ep_title, episode=1,
                   scene=9999 if is_short else 9998, max_new_images=1,
                   model_index=0, fallback=False, aspect_ratio=target_ratio,
                   transport=transport)
        receipt_ok = True
        backend_used = "mcp_v2"
        try:
            close_completed(account, url, pinned_target)
        except Exception as release_exc:
            # Verified asset is already downloaded. Keep the original tab and
            # allow the next prepare() to check queue state independently.
            print(f"[FLOW_THUMBNAIL] Completed tab retained: {type(release_exc).__name__}", flush=True)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "backend": "mcp_v2",
                "aspect_ratio": target_ratio, "is_short": is_short}
    finally:
        if pinned_target and not receipt_ok:
            try:
                abandon_fresh(account, url, pinned_target)
            except Exception:
                # In-flight or uncertain work must remain untouched.
                pass'''
if s.count(old)!=1:raise RuntimeError("PATCH_SCOPE_MISMATCH "+str(s.count(old)))
cp=root/"runtime"/("thumbnail_session_qa_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
cp.mkdir(parents=True,exist_ok=False)
(cp/"seo_packager.py.original").write_bytes(orig)
s=s.replace(old,new,1)
tmp=source.with_name(source.name+".thumbnail-session-tmp")
tmp.write_bytes(s.replace("\n","\r\n").encode("utf8"))
tmp.replace(source)
print(json.dumps({"state":"PATCHED","cp":str(cp),
"before_sha256":hashlib.sha256(orig).hexdigest(),
"after_sha256":hashlib.sha256(source.read_bytes()).hexdigest()},ensure_ascii=False))
