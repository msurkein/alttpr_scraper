import bps.apply
import requests
import argparse
import json
import logging

logger = logging.getLogger('alttpr_randomizer')

parser = argparse.ArgumentParser(description="Generate a randomized LTTP ROM using the LTTP randomizer", add_help=True)
parser.add_argument("--glitches", choices=["none", "overworld_glitches", "major_glitches", "no_logic"], default="none", required=False)
parser.add_argument("--item-placement", dest="item-placement", choices=["advanced", "basic"], default="advanced", required=False)
parser.add_argument("--dungeon-items", dest="dungeon-items", choices=["standard", "full", "mcs", "mc"], default="standard", required=False)
parser.add_argument("--accessibility", choices=["items", "locations", "none"], default="items", required=False)
parser.add_argument("--goal", choices=["ganon", "fast_ganon", "dungeons", "pedestal", "triforce-hunt"], default="ganon", required=False)
parser.add_argument("--crystals_ganon", choices=["0", "1", "2", "3", "4", "5", "6", "7", "random"], default="7", required=False)
parser.add_argument("--crystals_tower", choices=["0", "1", "2", "3", "4", "5", "6", "7", "random"], default="7", required=False)
parser.add_argument("--mode", choices=["open", "inverted", "retro"], default="open", required=False)
parser.add_argument("--entrances", choices=["none", "simple", "restricted", "full", "crossed", "insanity"], default="none", required=False)
parser.add_argument("--hints", choices=["on", "off"], default="on", required=False)
parser.add_argument("--weapons", choices=["randomized", "swordless", "vanilla", "assured"], default="randomized", required=False)
parser.add_argument("--item_pool", choices=["normal", "hard", "expert", "crowd_control"], default="normal", required=False)
parser.add_argument("--item_functionality", choices=["normal", "hard", "expert"], default="normal", required=False)
parser.add_argument("--tournament", action="store_true", required=False)
parser.add_argument("--spoilers", choices=["on", "off"], default="on", required=False)
parser.add_argument("--lang", choices=["en", "fr", "de", "es"], default="en", required=False)
parser.add_argument("--enemizer_boss-shuffle", choices=["none", "random", "full"], default="none", required=False)
parser.add_argument("--enemizer_enemy-shuffle", choices=["none", "random", "shuffled"], default="none", required=False)
parser.add_argument("--enemizer_enemy-damage", choices=["default", "shuffled", "random"], default="default", required=False)
parser.add_argument("--enemizer_enemy-health", choices=["default", "easy", "hard", "expert"], default="default", required=False)
parser.add_argument("--verbose", action="store_true", required=False, help="Enable verbose logging")

args = parser.parse_args()
verbose_logging = args.__dict__["verbose"]


def create_nested_args(arg_data):
    nested_args_data = dict()
    for key in arg_data.__dict__:
        if key.find("_") >= 0:
            sub_args_key = key.split("_")[0]
            sub_args_sub_key = key.replace(sub_args_key + "_", "", 1)
            if sub_args_key not in nested_args_data.keys():
                nested_args_data[sub_args_key] = dict()
            sub_dict = nested_args_data[sub_args_key]
            sub_dict[sub_args_sub_key] = arg_data.__dict__[key]
        else:
            nested_args_data[key.replace("-", "_")] = arg_data.__dict__[key]
        if verbose_logging:
            logger.warning("{} -> {}".format(key, arg_data.__dict__[key]))
    return nested_args_data


nested_args = create_nested_args(args)


def prepare_rom(rom_bytes):
    target_buf = bytearray()
    while len(target_buf) < 2097152:
        target_buf.append(0)
    with open("ecca7473031de4b4e1d9994874a3e80c.bps", "rb") as bps_file:
        ops = bps.apply.read_bps(bps_file)
        bps.apply.apply_to_bytearrays(ops, rom_bytes, target_buf)

    return target_buf


def update_checksum(rom_bytes):
    bytesum = 0
    for i in range(0, len(rom_bytes)):
        if i < 0x7fdc or i > 0x7fdf:
            bytesum += rom_bytes[i]
    checksum = (bytesum + 0x1fe) & 0xffff
    inverse = checksum ^ 0xffff
    rom_bytes[0x7fdc] = inverse & 0xff
    rom_bytes[0x7fdd] = inverse >> 8
    rom_bytes[0x7fde] = checksum & 0xff
    rom_bytes[0x7fdf] = checksum >> 8
    return rom_bytes


def set_heart_speed(rom_bytes, param):
    heart_speed = 0x20
    if param == 0.5:
        heart_speed = 0x40
    if param == 0:
        heart_speed = 0x00
    if param == 0.25:
        heart_speed = 0x80
    if param == 2:
        heart_speed = 0x10
    rom_bytes[0x180033] = heart_speed
    return rom_bytes


def generate_new_rom(posted_args):
    post_data = json.dumps(posted_args)
    with open("req_post.json", "w") as p:
        p.write(post_data)
    with requests.Session() as s:
        s.get("https://alttpr.com/en/randomizer")
        r = s.post("https://alttpr.com/api/randomizer", data=nested_args)
        result = r.json()
        with open("Zelda no Densetsu - Kamigami no Triforce (Japan).sfc", "rb") as rom_file:
            rom_bytes = rom_file.read()
        patch_and_randomize_rom(rom_bytes, result["patch"], result["hash"], result["spoiler"])


def patch_and_randomize_rom(rom_bytes, patch, seed_id=None, spoiler=None):
    rom_bytes = prepare_rom(rom_bytes)
    for patch_segment in patch:
        for patch_index in patch_segment.keys():
            for b in patch_segment[patch_index]:
                rom_bytes[int(patch_index)] = b
                patch_index = str(int(patch_index) + 1)
    rom_bytes = set_heart_speed(rom_bytes, 0.5)
    rom_bytes = update_checksum(rom_bytes)
    with open("randomized.sfc", "wb") as output_file:
        output_file.write(rom_bytes)
    if spoiler is not None:
        with open("random_hint.txt", "w") as output_hint:
            hints = spoiler
            for key in hints.keys():
                location_hint = hints[key]
                if isinstance(location_hint, dict):
                    for location in location_hint.keys():
                        output_hint.write("{},{},{}\n".format(key, location, location_hint[location]))
                if isinstance(location_hint, list):
                    for item in location_hint:
                        for location_key in item.keys():
                            output_hint.write("{},{},{}\n".format(key, location_key, item[location_key]))

            output_hint.write("raw,{}".format(str(spoiler)))
    print("https://alttpr.com/en/h/{}".format(seed_id))


generate_new_rom(nested_args)
