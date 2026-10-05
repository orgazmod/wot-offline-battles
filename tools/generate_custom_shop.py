"""Generate custom_shop.json from the client's own vehicle roster.

Reads prices the client itself publishes, so no value is invented.
Vehicles with no published price are skipped; add them by hand if needed.

Usage:
    python tools/generate_custom_shop.py GAME_ROOT OUTPUT.json
"""
import json
import os
import sys
import zipfile

sys.path.insert(0, 'launcher')
from vehicle_overlays import _require_target, _vehicle_roster_from_archive

CLONE_SUFFIXES = ('_bot', '_bootcamp', '_training', '_fallout')
NON_BATTLE_NAMES = ('Env_Artillery',)


def main():
    if len(sys.argv) < 2:
        print('usage: generate_custom_shop.py GAME_ROOT [OUTPUT]')
        return 2
    game_root = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else 'custom_shop_all.json'

    status, package_path = _require_target(game_root)
    with zipfile.ZipFile(package_path) as archive:
        counts = {}
        for info in archive.infolist():
            counts[info.filename] = counts.get(info.filename, 0) + 1
        roster = _vehicle_roster_from_archive(archive, counts)

    vehicles = {}
    skipped_clones = 0
    skipped_no_price = 0
    for r in roster:
        name = r['vehicle']
        if name.endswith(CLONE_SUFFIXES) or name in NON_BATTLE_NAMES:
            skipped_clones += 1
            continue
        full_name = '%s:%s' % (r['nation'], name)
        credits = int(r.get('credits', 0) or 0)
        gold = int(r.get('gold', 0) or 0)
        if gold > 0:
            vehicles[full_name] = {'gold': gold}
        elif credits > 0:
            vehicles[full_name] = {'credits': credits}
        else:
            skipped_no_price += 1
            continue

    payload = {'enabled': True, 'vehicles': vehicles}
    with open(output, 'w') as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False,
                  sort_keys=True)
    print('Wrote %d vehicles to %s' % (len(vehicles), os.path.abspath(output)))
    print('Skipped %d clones, %d without published price' %
          (skipped_clones, skipped_no_price))
    return 0


if __name__ == '__main__':
    sys.exit(main())