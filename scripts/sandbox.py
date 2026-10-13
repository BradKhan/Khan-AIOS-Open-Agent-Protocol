#!/usr/bin/env python3
"""Minimal OCI container command boundary for offline agent and verifier tasks.

This is a hardened Docker profile, not a network allowlist or VM. Paid API
models cannot run with network=none unless a separate controlled broker exists.
"""
import os
import re
from pathlib import Path

IMAGE = re.compile(r"^[a-z0-9][a-z0-9._:/-]{0,220}@sha256:[0-9a-f]{64}$")
class SandboxError(ValueError): pass

def wrap(command, workspace, image, uid=None, gid=None):
    if not isinstance(command,list) or not command or not all(isinstance(x,str) and x for x in command):
        raise SandboxError("command must be a nonempty argv list")
    if not isinstance(image,str) or not IMAGE.fullmatch(image):
        raise SandboxError("container image must be digest-pinned")
    root=Path(workspace)
    if not root.is_dir() or root.is_symlink():
        raise SandboxError("workspace must be an existing non-symlink directory")
    if any(p.is_symlink() for p in (root,root.parent)):
        raise SandboxError("symlinked workspace parents are not allowed")
    if os.name=="nt":
        raise SandboxError("Linux Docker sandbox requires POSIX UID/GID")
    uid=os.getuid() if uid is None else uid
    gid=os.getgid() if gid is None else gid
    if type(uid)!=int or type(gid)!=int or uid<=0 or gid<=0:
        raise SandboxError("sandbox must run with a nonroot UID and GID")
    return ["docker","run","--rm","-i","--pull=never",
            "--network=none","--read-only","--cap-drop=ALL",
            "--security-opt=no-new-privileges","--pids-limit=64",
            "--memory=1g","--cpus=1","--user",f"{uid}:{gid}",
            "--tmpfs","/tmp:rw,nosuid,size=64m",
            "--mount",f"type=bind,src={root.resolve()},dst=/workspace,rw",
            "--workdir","/workspace","--env","HOME=/tmp",
            "--env","PYTHONDONTWRITEBYTECODE=1",
            image,*command]
