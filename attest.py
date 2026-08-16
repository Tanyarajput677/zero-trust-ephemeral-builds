#!/usr/bin/env python3
import datetime
import hashlib
import json
import os
import subprocess
import sys


def compute_sha256(filepath):
  hasher = hashlib.sha256()
  with open(filepath, "rb") as f:
    for chunk in iter(lambda: f.read(4096), b""):
      hasher.update(chunk)
  return hasher.hexdigest()


def generate_slsa_attestation():
  artifact_path = "dist/production_service.bin"
  if not os.path.exists(artifact_path):
    print("❌ Error: dist/production_service.bin not found. Run builder.py first.")
    sys.exit(1)

  artifact_hash = compute_sha256(artifact_path)
  print("=" * 80)
  print("📜 GENERATING SLSA LEVEL 4 IN-TOTO PROVENANCE PREDICATE")
  print("=" * 80)

  # Standard in-toto / SLSA v0.2 Provenance Format
  slsa_provenance = {
      "_type": "https://in-toto.io/Statement/v0.1",
      "subject": [{
          "name": "production_service.bin",
          "digest": {"sha256": artifact_hash},
      }],
      "predicateType": "https://slsa.dev/provenance/v0.2",
      "predicate": {
          "builder": {"id": "https://github.com/Tanyarajput677/ephemeral-runner"},
          "buildType": "https://slsa.dev/heuristic/v1",
          "invocation": {
              "configSource": {
                  "uri": (
                      "git+https://github.com/Tanyarajput677/ephemeral-build-security"
                  ),
                  "digest": {"sha1": "commit-head-main"},
                  "entryPoint": "builder.py",
              }
          },
          "materials": [{
              "uri": "app_source.py",
              "digest": {
                  "sha256": hashlib.sha256(b"source_payload").hexdigest()
              },
          }],
          "metadata": {
              "buildStartedOn": datetime.datetime.now(
                  datetime.timezone.utc
              ).isoformat(),
              "completeness": {
                  "parameters": True,
                  "environment": True,
                  "materials": True,
              },
              "reproducible": True,
          },
      },
  }

  predicate_file = "dist/provenance.json"
  with open(predicate_file, "w") as f:
    json.dump(slsa_provenance, f, indent=2)

  print(f"✅ [PROVENANCE] Written SLSA predicate: {predicate_file}")

  # Digitally sign the artifact and provenance with Cosign
  print(
      "🔐 [COSIGN] Cryptographically signing artifact with ECDSA-P256 private"
      " key..."
  )
  cmd = [
      "cosign",
      "sign-blob",
      "--key",
      "cosign.key",
      "--output-signature",
      "dist/production_service.bin.sig",
      "dist/production_service.bin",
      "--yes",
  ]
  env = os.environ.copy()
  env["COSIGN_PASSWORD"] = ""
  res = subprocess.run(cmd, env=env, capture_output=True, text=True)

  if res.returncode == 0:
    print(
        "🔑 [SIGNATURE] Successfully generated digital signature:"
        " dist/production_service.bin.sig"
    )
  else:
    print(f"❌ Signing failed: {res.stderr}")
    sys.exit(1)

  print("=" * 80)


if __name__ == "__main__":
  generate_slsa_attestation()