#!/usr/bin/env python3
"""
FinSight Encryption Key Generator
Generates a cryptographically secure 256-bit Fernet key for transparent at-rest database encryption.

Usage:
    python scripts/generate_key.py

To activate encryption:
    # Linux / macOS:
    export FINSIGHT_ENCRYPTION_KEY="<GENERATED_KEY>"

    # Windows PowerShell:
    $env:FINSIGHT_ENCRYPTION_KEY="<GENERATED_KEY>"

    # Windows CMD:
    set FINSIGHT_ENCRYPTION_KEY=<GENERATED_KEY>

CRITICAL KEY-LOSS RISK NOTICE:
    If this key is lost or deleted, any encrypted statement records in the SQLite database
    CANNOT be decrypted or recovered by anyone, including the FinSight team.
    Store your key securely in your password manager or secrets vault.
"""

from cryptography.fernet import Fernet

def main():
    key = Fernet.generate_key().decode("utf-8")
    print("=" * 75)
    print("FINSIGHT SECURE FERNET ENCRYPTION KEY GENERATED")
    print("=" * 75)
    print(f"\nGenerated Key:\n{key}\n")
    print("Configuration Instructions:")
    print("  1. Copy this key into your environment or .env file:")
    print(f"     FINSIGHT_ENCRYPTION_KEY={key}\n")
    print("  2. Start the FinSight backend server:")
    print("     python -m uvicorn app.main:app --reload\n")
    print("WARNING - KEY LOSS RISK:")
    print("  FinSight performs zero-telemetry hardware-local encryption.")
    print("  Keys are NEVER transmitted to external servers or cloud backups.")
    print("  If you lose this key, previously encrypted SQLite data cannot be decrypted.")
    print("=" * 75)

if __name__ == "__main__":
    main()
