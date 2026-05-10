import argparse
import sys
import os
import subprocess
import tempfile

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=['Development', 'Release'], required=True)
    parser.add_argument("--secure-boot", choices=['ON', 'OFF'], required=True)
    parser.add_argument("--pem", help="Path to public key PEM")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    is_dev = 1 if args.variant == 'Development' else 0
    is_release = 1 if args.variant == 'Release' else 0
    sig_verify = 1 if is_release else 0
    secure_boot = 1 if (args.secure_boot == 'ON' and is_release) else 0

    lines = [
        "/* Automatically generated - DO NOT EDIT MANUALLY */",
        "#ifndef BL_BUILD_CONFIG_H",
        "#define BL_BUILD_CONFIG_H",
        "",
        f"#define BOOTLOADER_DEV                   {is_dev}u",
        f"#define BOOTLOADER_RELEASE               {is_release}u",
        f"#define BL_ENABLE_SECURE_BOOT            {secure_boot}u",
        f"#define BL_ENABLE_SIGNATURE_VERIFY       {sig_verify}u",
        ""
    ]

    if sig_verify:
        if not args.pem or not os.path.exists(args.pem):
            print(f"Error: PEM file required for Release build (Signature Verification): {args.pem}")
            sys.exit(1)
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            conv_script = os.path.join(script_dir, "rsa_public_key_from_pem.py")
            
            with tempfile.NamedTemporaryFile(suffix=".h", delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                subprocess.run(
                    [sys.executable, conv_script, "--pem", args.pem, "--out", tmp_path],
                    check=True
                )
                with open(tmp_path, "r") as f:
                    pubkey_content = f.read()
                
                pubkey_content = pubkey_content.replace("#ifndef BL_RSA_PUBLIC_KEY_GENERATED_H", "")
                pubkey_content = pubkey_content.replace("#define BL_RSA_PUBLIC_KEY_GENERATED_H", "")
                pubkey_content = pubkey_content.replace("#endif /* BL_RSA_PUBLIC_KEY_GENERATED_H */", "")
                
                lines.append("/* RSA-2048 Public Key */")
                lines.append(pubkey_content.strip())
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as e:
            print(f"Failed to convert PEM: {e}")
            sys.exit(1)
    else:
        lines.append("/* Development build - Signature verification disabled */")
        lines.append("#define BL_RSA_PUBLIC_KEY_N0INV          0u")

    lines.append("")
    lines.append("#endif /* BL_BUILD_CONFIG_H */")

    with open(args.out, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated {args.out} ({args.variant}, SecureBoot={args.secure_boot})")

if __name__ == "__main__":
    main()
