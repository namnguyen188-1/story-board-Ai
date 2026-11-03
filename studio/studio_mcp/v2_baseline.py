"""Pinned V2 0.3.1 runtime verifier.

The original V2 folder is NOT accessed during Studio runtime.
Any accidental core drift or unreviewed adapter change fails closed.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path


class BaselineDriftError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda:stream.read(1024*1024),b""):
            digest.update(data)
    return digest.hexdigest()


def verify_v2_baseline(node_dir=None, manifest_path=None):
    base=Path(node_dir) if node_dir else Path(__file__).resolve().parent/"node"
    manifest=Path(manifest_path) if manifest_path else Path(__file__).with_name("MCP_V2_PINNED_BASELINE.json")
    try:
        data=json.loads(manifest.read_text(encoding="utf-8"))
        if data["schema_version"] != 1 or data["upstream_version"]!="0.3.1":
            raise BaselineDriftError("STORYBOARD_MCP_V2_BASELINE_SCHEMA_INVALID")
        core=data["core_files"]
        adapters=data["intentional_studio_adapters"]
        expected=set(core)|set(adapters)
        current={str(p.relative_to(base)).replace("\\","/")
                 for p in (base/"dist").rglob("*")
                 if p.is_file() and p.suffix in (".js",".mjs",".json")}
        if current!=expected or len(core)!=38 or len(adapters)!=4:
            raise BaselineDriftError("STORYBOARD_MCP_V2_BASELINE_FILESET_DRIFT")
        if _sha(base/"package.json")!=data["package_sha256"]:
            raise BaselineDriftError("STORYBOARD_MCP_V2_PACKAGE_DRIFT")
        if _sha(base/"package-lock.json")!=data["package_lock_sha256"]:
            raise BaselineDriftError("STORYBOARD_MCP_V2_DEPENDENCY_LOCK_DRIFT")
        for name, digest in core.items():
            if _sha(base/name)!=digest:
                raise BaselineDriftError("STORYBOARD_MCP_V2_CORE_DRIFT:"+name)
        for name, digest in adapters.items():
            if _sha(base/name)!=digest["studio_sha256"]:
                raise BaselineDriftError("STORYBOARD_MCP_V2_ADAPTER_DRIFT:"+name)
        for pkg, version in data["dependency_versions"].items():
            location=base/"node_modules"/pkg/"package.json"
            observed=json.loads(location.read_text(encoding="utf-8"))
            if observed.get("version")!=version:
                raise BaselineDriftError("STORYBOARD_MCP_V2_INSTALLED_DEPENDENCY_DRIFT:"+pkg)
        return {"verified":True,"version":data["upstream_version"],
                "v2_identical":len(core),"reviewed_studio_adapters":len(adapters),
                "dependency_lock_sha256":data["package_lock_sha256"]}
    except BaselineDriftError:
        raise
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as exc:
        raise BaselineDriftError("STORYBOARD_MCP_V2_BASELINE_INCOMPLETE") from exc


if __name__=="__main__":
    print(json.dumps(verify_v2_baseline(),ensure_ascii=False))
