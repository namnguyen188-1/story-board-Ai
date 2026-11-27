"""Interactive sign-in uses this bundle's Muse copy only."""
import json
from common import STATE, api_key, rebase_muse_profiles
from store import Store


def main():
    rebase_muse_profiles()
    if any(j["provider"] == "muse" and j["state"] in {"running", "queued"} for j in Store(STATE / "jobs.sqlite").list(10000)):
        raise RuntimeError("MUSE_JOBS_ACTIVE_FINISH_THEM_FIRST")
    from muse_video_provider import start_muse_login, finish_muse_login
    result = start_muse_login()
    print("Dang nhap Muse trong cua so vua mo, sau do quay lai day.")
    input("Nhan Enter khi da dang nhap xong: ")
    result = finish_muse_login(result["login_id"], result.get("account_id"))
    print("MUSE_READY" if result.get("ready") else "MUSE_LOGIN_NOT_FINISHED")


if __name__ == "__main__":
    main()
