#!/usr/bin/env python3
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


def verify_admission_gate():
  print("=" * 85)
  print("🛡️  ZERO-TRUST ADMISSION VERIFICATION GATE: EVALUATING ARTIFACT")
  print("=" * 85)

  artifact_path = "dist/production_service.bin"
  sig_path = "dist/production_service.bin.sig"
  provenance_path = "dist/provenance.json"
  pub_key = "cosign.pub"

  if not all(
      os.path.exists(p) for p in [artifact_path, sig_path, provenance_path]
  ):
    print("❌ [GATE BLOCKED] Deployment rejected: Missing security artifacts.")
    sys.exit(1)

  # Check 1: Cryptographic Digital Signature Verification via Cosign
  print("🔍 Step 1: Verifying digital signature against cosign.pub...")
  cmd = [
      "cosign",
      "verify-blob",
      "--key",
      pub_key,
      "--signature",
      sig_path,
      artifact_path,
  ]
  res = subprocess.run(cmd, capture_output=True, text=True)

  if res.returncode != 0:
    print("🚨 [SECURITY BREACH] CRYPTOGRAPHIC SIGNATURE CHECK FAILED!")
    print(f"   Reason: Signature does not match payload or public key.")
    print("🚫 [GATE ENFORCEMENT] DEPLOYMENT PERMANENTLY BLOCKED.")
    print("=" * 85)
    return False

  print("🟢 [PASSED] Valid digital signature verified by Cosign.")

  # Check 2: SLSA Provenance Digest Match
  print(
      "🔍 Step 2: Validating SLSA Level 4 Provenance digest and builder"
      " identity..."
  )
  with open(provenance_path, "r") as f:
    prov_data = json.load(f)

  expected_hash = prov_data["subject"][0]["digest"]["sha256"]
  actual_hash = compute_sha256(artifact_path)

  if expected_hash != actual_hash:
    print(
        "🚨 [SECURITY BREACH] TAMPER DETECTED: Binary hash does not match SLSA"
        " provenance!"
    )
    print(f"   Expected: {expected_hash}")
    print(f"   Actual:   {actual_hash}")
    print("🚫 [GATE ENFORCEMENT] DEPLOYMENT BLOCKED.")
    print("=" * 85)
    return False

  builder_id = prov_data["predicate"]["builder"]["id"]
  print(f"🟢 [PASSED] Provenance hash match verified.")
  print(f"🏢 [ATTESTATION] Authenticated Builder ID: {builder_id}")
  print("=" * 85)
  print(
      "🚀 [ZERO-TRUST ADMISSION GRANTED] Artifact approved for production"
      " deployment!"
  )
  print("=" * 85)
  return True


if __name__ == "__main__":
  success = verify_admission_gate()
  if not success:
    sys.exit(1)