"""
Quick script to test importability of packages listed in requirements.txt
Run after `pip install -r requirements.txt` to see which packages fail to import.
"""
import importlib
import sys

reqs = []
with open('requirements.txt') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        pkg = line.split('==')[0].split('>=')[0].strip()
        reqs.append(pkg)

failed = []
for pkg in reqs:
    try:
        importlib.import_module(pkg)
        print(f"OK: {pkg}")
    except Exception as e:
        print(f"FAIL: {pkg} -> {e}")
        failed.append((pkg, str(e)))

if failed:
    print('\nSome packages failed to import:')
    for p, err in failed:
        print(p, ' : ', err)
    sys.exit(1)
else:
    print('\nAll imports OK')
