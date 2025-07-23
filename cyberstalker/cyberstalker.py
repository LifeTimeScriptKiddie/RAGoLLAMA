import subprocess
import sys
import os

def run_whatweb_with_proxychains(domain):
    try:
        cmd = ["proxychains4", "whatweb", domain]
        print(f"\n[+] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr

        # Print to console
        print(output)

        # Save to file
        with open("whatweb_results.txt", "a") as f:
            f.write(f"\n[+] {domain}\n{output}\n{'='*80}\n")

    except subprocess.TimeoutExpired:
        print(f"[-] Timeout for {domain}")
    except Exception as e:
        print(f"[-] Error with {domain}: {e}")

def main():
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} targets.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"[-] File not found: {input_file}")
        sys.exit(1)

    with open(input_file, "r") as f:
        targets = [line.strip() for line in f if line.strip()]

    for target in targets:
        run_whatweb_with_proxychains(target)

if __name__ == "__main__":
    main()
