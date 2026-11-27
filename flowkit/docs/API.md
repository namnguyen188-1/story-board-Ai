# Flow + Muse Orchestrator

Independent Windows bundle, inside `FlowKit_Test/FlowMuse_Orchestrator`.
Storyboard AI is a read-only copy source. The running bundle does not load its
code, runtime, registry, or account profiles from the installed Storyboard app.

## Start and connect

Run `START.cmd`, or `Start_API.vbs` for a hidden start.
Default base URL: `http://127.0.0.1:18110`; interactive API docs: `/docs`.
Read your local API key from `state/api.key` and send it in `X-API-Key`.
The key protects both requests and artifact downloads. Never give clients Muse
cookies or Google cookies. No provider key or cookie appears in job responses.

## Submit

`POST /v1/jobs` returns HTTP 202 immediately. Send a stable `Idempotency-Key`
header for each intended operation. Reusing it returns the same job; using it
with a different payload returns 409. This survives service restarts.

```json
{"provider":"flow","kind":"image","prompt":"A chef slices a carrot naturally.","aspect_ratio":"9:16","image_model":"NANO_BANANA_PRO"}
```

```json
{"provider":"flow","kind":"video","prompt":"0-3s: A chef places salmon in a pan. 3-6s: Butter sizzles. 6-8s: The chef tilts the pan.","duration_seconds":8,"aspect_ratio":"9:16"}
```

```json
{"provider":"muse","kind":"scene","prompt":"A chef slowly slices carrots, natural body movement and camera motion, clearly lit kitchen.","duration_seconds":8,"aspect_ratio":"9:16"}
```

Provider capabilities are explicit. Flow `image` produces one image; Flow `video`
uses Omni Flash text-to-video; Flow `scene` produces an image and then a Veo
image-to-video clip. The copied Muse worker supports `scene`, producing one image
and one video. Muse image-only/video-only calls are rejected, rather than creating
additional media without telling the client. Duration is currently 8 seconds.

To use a different Flow project, pass its UUID as `project_id`. Muse can choose
an account by `account_id`; otherwise the active copied account is used and is
bound to the job for recovery. No automatic cross-provider fallback occurs.

Submit multiple jobs to `POST /v1/jobs/batch` as `{"requests":[...]}`. Give every
item a stable `request_id`. Flow and Muse each have one worker; different providers
can run concurrently. Provider credit/quota consumption is unchanged.

## Check and download

`GET /v1/jobs/{job_id}` returns `queued`, `running`, `succeeded`, `failed`,
`cancelled`, or `recovery_needed`. Only `succeeded` means verified files exist.
Use the protected `artifacts[].download_url` to download the PNG/MP4. Every
artifact includes its dimensions, video duration, byte count and SHA-256 checksum.
Muse downloads may have a longer native duration; the delivery MP4 is normalized
to the requested 8 seconds while the original download and receipt stay intact.

`GET /v1/providers?live=true` checks Flow's extension and verifies the selected
Muse session with a read-only gateway request. Local READY alone is not a live
authentication check. `GET /v1/accounts/muse` returns safe account metadata only.

## Interrupted jobs

The service preserves accepted handles and Muse receipts. After a crash, a
running job becomes `recovery_needed`; it is never automatically submitted again.
`POST /v1/jobs/{id}/resume` continues only when a known remote operation/session
exists. An ambiguous submit returns 409 and requires inspection.
Cancellation is available for queued local jobs only. It does not promise to
cancel an accepted upstream generation.

## Copying the bundle

Copy the whole folder, including `engines`, `bin`, `app`, and configuration. The
bundled Python and provider dependencies remove the need for Storyboard AI or a
system Python installation. Paths are rebased inside the copied folder.

On another Windows account/computer, Chrome/Google sessions may need sign-in.
The launcher automatically installs the included extension through Chrome
Extensions CDP API (tested with Chrome 156), or reuses an enabled copy with the
same packaged files. No manual Load unpacked step is needed. Windows browser credentials
are not guaranteed transferable. The Flow extension is in `extensions/flow`.
Muse session expiry also requires normal sign-in; saved READY is not a guarantee.
The API can be copied as software, but it cannot manufacture account access.

The default listener is loopback. If intentionally connecting another device,
set `api_host` in `settings.json` to its LAN interface and configure that machine's
network access. This bundle does not change the firewall or expose an Internet
endpoint automatically. Clients still need `X-API-Key`.

`COPY_MANIFEST.json` records protected source hashes for read-only verification.

## Fresh projects and sign-in

Run `NEW_PROJECT.cmd` and give a separate folder path. It copies the runtime and
provider sessions, creates an empty job database/output folder, generates a new
API key on first start, and chooses a separate API port. It does not change this
kit or Storyboard. Change `flow_project_id` in the new copy's `settings.json`, or
pass each job's `project_id`, to target a different existing Flow project.
Several copies on one PC share the local Flow bridge and browser; their API keys,
jobs and output folders stay separate. This is not multiple independent Google
sessions. Concurrent copies using the same Muse account share upstream quota;
avoid running that account from several copies at once.

`SETUP_FLOW.cmd` explicitly shows the dedicated Flow Chrome for sign-in; it also
automatically prepares `extensions/flow` on a new profile. `LOCK_FLOW.cmd`
hides and locks that window again; normal `START.cmd` keeps it hidden.
A bridge connection alone is insufficient: provider preflight also checks the
signed-in Flow project tab. `SETUP_MUSE.cmd` performs normal Muse sign-in using
only the copied modules and copied account profiles.

`state/machine.json` is a local browser profile preference. If its profile path
is absent on another PC, the bundle uses its own `runtime/flow_profile` instead.
It never loads code or credentials from the installed Storyboard application.
