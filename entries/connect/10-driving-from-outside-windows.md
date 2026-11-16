---
id: connect-10-driving-from-outside-windows
title: Driving Windows SolidWorks from WSL or another host
status: verified
verified_on: WSL2 to SolidWorks 2026; launching hidden processes and a file-queue worker, WSL2 to SolidWorks 2024 SP5 (32.5.0)
language: [shell, typescript, python]
api: [cscript, wslpath, powershell Start-Process]
keywords: [wsl, cross platform, cscript, wslpath, path translation, remote drive, python.exe, windows python from wsl, pywin32 from wsl, ext4, \\wsl.localhost, UNC path, carriage return, tr -d, Start-Process, WindowStyle Hidden, PassThru, cmd.exe start title, Windows cannot find, 127.0.0.1 from WSL, localhost unreachable, NAT mode, connection refused, file queue, persistent worker, hidden launch, dialog from WSL launch]
answers: "My code runs on Linux or a Mac. How do I still drive SolidWorks?"
---

# Driving Windows SolidWorks from WSL or another host

## The shape of the answer

You cannot call COM from Linux. What you can do is **generate a script on the
Linux side, translate the paths, and run it through the Windows script host.**
The whole automation stays a text file until the last moment.

```
your program (Linux)  ->  write files + a .vbs  ->  wslpath -w  ->  cscript.exe
```

This is why VBScript, and not a compiled binary, is the right target for
generated automation. See [connect/01](01-attach-from-vbscript.md).

## Path translation

Everything you hand SolidWorks must be a Windows path. From WSL:

```bash
wslpath -w /mnt/c/Users/you/Desktop/Planes/exports/trainer40
# C:\Users\you\Desktop\Planes\exports\trainer40
```

In code:

```typescript
export function toWindowsDir(dir: string): string {
  const r = spawnSync("wslpath", ["-w", dir], { encoding: "utf8" });
  if (r.status !== 0) throw new Error(`wslpath failed for ${dir}`);
  const win = r.stdout.trim();
  return win.endsWith("\\") ? win : win + "\\";
}
```

Append the trailing backslash once, at the boundary, so the generated script
can concatenate filenames without thinking about it.

## Running the script

```typescript
const r = spawnSync("cscript.exe", ["//nologo", winScriptPath], {
  encoding: "utf8",
});
```

`//nologo` suppresses the Windows Script Host banner so your parser only sees
your own output. The script's `WScript.Echo` lines come back on stdout and its
`WScript.Quit` code becomes the exit status, which is what makes this composable
with the rest of a build.

## Where files live

Keep the repository on the Linux filesystem and write **exports to the Windows
side**, under `/mnt/c/...`. Two reasons: SolidWorks reads them faster from a
native NTFS path, and a file written to the Linux filesystem is reachable from
Windows only over a network path that some dialogs refuse. A PyInstaller build of a
tool kept this way ran from a copy of the checkout under `%USERPROFILE%`; see
[connect/02](02-attach-from-python.md).

## Running Windows Python from WSL, with the checkout on ext4

The same shape works for Python with pywin32, which cannot run in WSL either.
Call the **Windows** interpreter from the WSL shell, and hand it the script
through the path Windows sees the Linux filesystem by. From a repository that
lives on ext4 (`/home/...`), this is the whole launcher:

```bash
#!/usr/bin/env bash
# Probe the SolidWorks API from WSL, through the Windows Python beside SolidWorks.
#
# The repo stays on ext4; Windows reads it through \\wsl.localhost. Every path
# handed to SolidWorks itself is under C:\, and the results come back through
# the same UNC path as plain file I/O. Carriage returns are stripped so the
# report reads cleanly here.
set -o pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python.exe "$(wslpath -w "$here/probe.py")" --out "$(wslpath -w "$here/probe/results")" "$@" | tr -d '\r'
exit "${PIPESTATUS[0]}"
```

- `python.exe` is the Windows Python that has pywin32, found on the Windows
  `PATH` through WSL interop. The `.exe` is what makes WSL run the Windows one.
- `wslpath -w` on an ext4 path gives a UNC path,
  `\\wsl.localhost\Ubuntu\home\...`. Windows Python imports the code and writes
  its results there as ordinary file I/O.
- `tr -d '\r'` strips the carriage returns of Windows console output.
  `set -o pipefail` and `exit "${PIPESTATUS[0]}"` keep Python's exit code
  rather than `tr`'s.
- **Every path handed to SolidWorks is under `C:\`.** Files the probe saved
  went to `%USERPROFILE%\Documents\...`, and the probe that saves refuses any
  folder that is not a drive path. Whether SolidWorks will save to a
  `\\wsl.localhost` path was not tested.

The script it runs puts the checkout's `src` on the import path, so nothing is
installed on the Windows side except Python and pywin32:

```python
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from gear_generator.probe.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
```

And the equivalent for a Windows shell, which works whether the repository is
on `C:` or inside WSL, because `pushd` maps a UNC path to a temporary drive
letter:

```bat
@echo off
REM Probe the SolidWorks API on the running session and write the results into
REM probe\results. SolidWorks must already be open; nothing is launched.
REM
REM pushd maps the \\wsl.localhost path of a WSL checkout to a drive letter, so
REM this works whether the repo sits on C: or inside WSL.
pushd "%~dp0"
python "%~dp0probe.py" --out "%~dp0probe\results" %*
set CODE=%ERRORLEVEL%
popd
exit /b %CODE%
```

**Verified, WSL2 to SolidWorks 2026 (revision 34.0.0).** The run recorded its
own arguments as
`['--out', '\\\\wsl.localhost\\Ubuntu\\home\\<user>\\Gear-Generator\\probe\\results', '--tier', '5', '--timeout', '400']`:
launched from WSL through the script above, it attached to SolidWorks, ran 33
probes (all passed, exit code 0), saved parts under `C:\Users\...\Documents`,
and wrote its report and JSON back into the ext4 checkout through the UNC
path. The `.bat` was not the launcher for that run. See
[connect/11](11-probe-an-api-member-on-a-live-session.md).

### Starting SolidWorks from WSL

`cmd.exe /c start "" "C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS (2)\SLDWORKS.exe"`
started the visible application (SolidWorks 2024 SP5, 2026-11-15), but the WSL
command that ran it did not return within 450 s, so the shell call had to be
moved to the background and stopped afterwards; stopping it left SolidWorks
running. A script polling `find_candidates()` every few seconds attached once
the welcome screen was up. Why `start` did not detach here was not looked into.

PowerShell's `Start-Process` with `-PassThru` returned, unlike `start` above,
and printed the new process's id, which is what an attach by process id needs:

```bash
powershell.exe -NoProfile -Command "\$p = Start-Process -FilePath 'C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS (2)\SLDWORKS.exe' -PassThru; \$p.Id" | tr -d '\r'
```

It printed the id; a script polling `find_candidates()` for that id every 5 s
found the session (revision 32.5.0) on its second try, 5 s in, with the welcome
screen up. SolidWorks 2024 SP5, 2026-11-15.

### Launching a hidden helper from WSL: not `cmd.exe start "title"`

`cmd.exe /c start "worker" /min python.exe worker.py …`, run from a WSL
shell, put up a Windows error box on the user's screen: **"Windows cannot find
'worker'. Make sure you typed the name correctly"**. The quotes round the
window title did not survive the trip from WSL to `cmd.exe`, so `start` took
the title for the program to run. The process never started.
What replaced it, from Python in WSL (paths are placeholders):

```python
ps = ("Start-Process -FilePath python.exe -ArgumentList 'worker.py','%s','%d' "
      "-WorkingDirectory '%s' -WindowStyle Hidden" % (SRC, PID, WINHERE))
subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
```

It started the worker with no console window and no dialog (tried first on a
harmless `python.exe -c pass`), and the WSL call returned. See
[GOTCHAS §120](../../GOTCHAS.md).

## A persistent worker on the Windows side, and why it is a file queue

Every `python.exe script.py` from WSL starts a Windows Python, imports pywin32
and attaches again. A worker that stays attached and runs jobs sent to it was
tried on SolidWorks 2024 SP5 (2026-11-16), with these findings:

- **WSL could not reach a socket on Windows.** A Windows Python listening on
  `127.0.0.1` refused the connection from WSL (`[Errno 111] Connection
  refused`; WSL2 with a private 172.18.x address behind the Windows host, the
  networking mode itself not read). Listening on the WSL default gateway's
  address instead, the
  connection from WSL timed out. The Windows firewall is the likely cause; it
  was not checked.
- **So the transport is files** in a folder both sides see (`/mnt/c/...`).
  The client writes `jobs/<id>.json` through a temporary name and
  `os.replace`, so the worker never reads half a file; the worker polls the
  folder every 30 ms, runs the job on its one COM thread, and writes
  `results/<id>.json` the same way:

  ```python
  def submit(job, timeout):
      os.makedirs(JOBS, exist_ok=True); os.makedirs(RESULTS, exist_ok=True)
      jid = "%d-%s" % (time.time() * 1000, uuid.uuid4().hex[:6])
      tmp = os.path.join(JOBS, jid + ".tmp")
      with open(tmp, "w", encoding="utf-8") as f:
          json.dump(job, f)
      os.replace(tmp, os.path.join(JOBS, jid + ".json"))
      rp = os.path.join(RESULTS, jid + ".json")
      end = time.time() + timeout
      while time.time() < end:
          if os.path.exists(rp):
              try:
                  with open(rp, encoding="utf-8") as f:
                      r = json.load(f)
              except Exception:
                  time.sleep(0.01); continue
              os.remove(rp)
              return r
          time.sleep(0.01)
  ```

  A ping (the worker reading `ISldWorks.RevisionNumber`) took 0.08–0.10 s from
  WSL and back.
- **It was not faster for the job measured.** One small read (an 18-component
  assembly's components and every mate's error code), five runs each way:
  a fresh `python.exe` per run took a median of 0.72 s (0.33–1.73 s); through
  the worker, medians of 1.48 s, then 4.21 s and 3.24 s in two later sets. The
  job's own time inside the worker was 1.1–3.4 s, so the COM work, not the
  start-up, dominated, and it varied with another program using the same
  SolidWorks at the time. A Windows Python started quickly on this machine.
  Measure before building one.
- The worker kept every SolidWorks call on its own thread
  ([connect/06](06-one-apartment-thread.md)) and returned only plain data,
  never COM objects; a job that raised (a deliberate division by zero) came
  back as an error and the worker carried on.

## Structuring the output so it can be parsed

The generated script should emit one line per operation with a fixed-width
status token:

```
attach  SldWorks.Application.34
part    trainer40
  ok      S1
  ok      S2
  MISSING S9 - import it by hand, or run with --insert
rebuild True
done    2 refreshed, 1 failed
```

Lowercase for success, uppercase for anything the caller must act on. It reads
fine to a person and parses with a `startsWith`.

## From macOS

There is no equivalent of `wslpath`, and no local Windows to run `cscript`. The
practical options are a shared folder plus running the script by hand on the
Windows machine, or SSH into the Windows box with OpenSSH Server enabled and
`cscript` invoked over that. The generation side is unchanged either way, which
is the point of keeping the automation textual.

## See also

- [connect/01 — Attach from VBScript](01-attach-from-vbscript.md)
- [curves/04 — Reload a curve in place](../curves/04-reload-curve-in-place.md)
- [connect/02 — Attach from Python](02-attach-from-python.md) — what the Windows Python then does
- [connect/11 — Probe an API member on a live session](11-probe-an-api-member-on-a-live-session.md) — the run launched this way
- [documents/02 — Save as, and close](../documents/02-save-as-and-close.md) — saving under `C:\`
- [connect/12 — Read the API help offline](12-read-the-api-help-offline.md) — `hh.exe` from WSL
- [appearance/01 — Read and remove a part's appearance](../appearance/01-read-and-remove-a-part-appearance.md) — another run launched this way, on SolidWorks 2024
- [connect/06 — One apartment thread](06-one-apartment-thread.md) — why the worker keeps every call on one thread
- [GOTCHAS §120](../../GOTCHAS.md) — `cmd.exe start "title"` from WSL
