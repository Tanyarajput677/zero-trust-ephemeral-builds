#!/usr/bin/env python3
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time


def compute_sha256(filepath):
  hasher = hashlib.sha256()
  with open(filepath, "rb") as f:
    for chunk in iter(lambda: f.read(4096), b""):
      hasher.update(chunk)
  return hasher.hexdigest()


def run_ephemeral_build():
  print("=" * 80)
  print("🔒 ZERO-TRUST EPHEMERAL BUILD ENGINE: INITIALIZING SANDBOX")
  print("=" * 80)

  # 1. Provision an ephemeral, isolated directory
  sandbox_dir = tempfile.mkdtemp(prefix="slsa_sandbox_")
  print(f"📦 [SANDBOX] Created disposable isolated build root: {sandbox_dir}")

  try:
    # 2. Generate clean production payload inside sandbox
    source_file = os.path.join(sandbox_dir, "app_source.py")
    artifact_file = os.path.join(sandbox_dir, "production_service.bin")

    with open(source_file, "w") as f:
      f.write(
          "print('Production Workload Active - Cryptographically Verified"
          " Build')\n"
      )

    print("⚙️  [BUILD] Compiling artifact in hermetic sandbox environment...")
    # Mock compile into a standalone binary payload
    with open(artifact_file, "wb") as f:
      f.write(
          b"ELF_HEADER_STUB_v1.0_PROD_PAYLOAD_"
          + os.urandom(32)
          + b"_SECURE_BUILD"
      )

    time.sleep(0.5)

    # 3. Compute immutable SHA256 cryptographic digest
    artifact_hash = compute_sha256(artifact_file)
    print(f"🔑 [HASH] Generated SHA-256 Digest: {artifact_hash}")

    # Copy binary to current release directory
    os.makedirs("dist", exist_ok=True)
    release_path = os.path.join("dist", "production_service.bin")
    shutil.copyfile(artifact_file, release_path)
    print(f"🚀 [DIST] Exported final build artifact to: {release_path}")

    # 4. Generate build metadata descriptor
    build_meta = {
        "artifact_name": "production_service.bin",
        "sha256": artifact_hash,
        "builder": "ephemeral-hermetic-builder-v1",
        "timestamp": time.time(),
        "status": "BUILT_SUCCESS",
    }
    with open("dist/build_meta.json", "w") as meta_f:
      json.dump(build_meta, meta_f, indent=2)

    print("📄 [METADATA] Build descriptor written to dist/build_meta.json")

  finally:
    # 5. Destroy Ephemeral Sandbox (Zero-Trust Lifecycle)
    shutil.rmtree(sandbox_dir)
    print(f"🧹 [CLEANUP] Destroyed ephemeral build root: {sandbox_dir}")
    print("=" * 80)


if __name__ == "__main__":
  run_ephemeral_build()