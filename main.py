import argparse
import json
import logging
import os
import ssl

import bps.apply
import requests
import requests.adapters
import tempfile

logging.basicConfig(level="INFO", format="%(message)s")
logger = logging.getLogger("main.py")
logger.setLevel("INFO")

parser = argparse.ArgumentParser(description="Generate a randomized LTTP ROM using the LTTP randomizer", add_help=False)
opts = parser.add_argument_group("Configuration Options")
opts.add_argument("--glitches", choices=["none", "overworld_glitches", "major_glitches", "no_logic"], default="none", required=False)
opts.add_argument("--item-placement", dest="item-placement", choices=["advanced", "basic"], default="advanced", required=False)
opts.add_argument("--dungeon-items", dest="dungeon-items", choices=["standard", "full", "mcs", "mc"], default="standard", required=False)
opts.add_argument("--accessibility", choices=["items", "locations", "none"], default="items", required=False)
opts.add_argument("--goal", choices=["ganon", "fast_ganon", "dungeons", "pedestal", "triforce-hunt"], default="ganon", required=False)
opts.add_argument("--crystals_ganon", choices=["0", "1", "2", "3", "4", "5", "6", "7", "random"], default="7", required=False)
opts.add_argument("--crystals_tower", choices=["0", "1", "2", "3", "4", "5", "6", "7", "random"], default="7", required=False)
opts.add_argument("--mode", choices=["open", "inverted", "retro"], default="open", required=False)
opts.add_argument("--entrances", choices=["none", "simple", "restricted", "full", "crossed", "insanity"], default="none", required=False)
opts.add_argument("--hints", choices=["on", "off"], default="on", required=False)
opts.add_argument("--weapons", choices=["randomized", "swordless", "vanilla", "assured"], default="randomized", required=False)
opts.add_argument("--item_pool", choices=["normal", "hard", "expert", "crowd_control"], default="normal", required=False)
opts.add_argument("--item_functionality", choices=["normal", "hard", "expert"], default="normal", required=False)
opts.add_argument("--tournament", action="store_true", required=False)
opts.add_argument("--spoilers", choices=["on", "off"], default="on", required=False)
opts.add_argument("--lang", choices=["en", "fr", "de", "es"], default="en", required=False)
opts.add_argument("--enemizer_boss-shuffle", choices=["none", "random", "full"], default="none", required=False)
opts.add_argument("--enemizer_enemy-shuffle", choices=["none", "random", "shuffled"], default="none", required=False)
opts.add_argument("--enemizer_enemy-damage", choices=["default", "shuffled", "random"], default="default", required=False)
opts.add_argument("--enemizer_enemy-health", choices=["default", "easy", "hard", "expert"], default="default", required=False)
opts.add_argument("--heart-speed", dest="heart-speed", type=float, choices=[2, 1, 0.25, 0.5, 0], default=0.5, required=False)
opts.add_argument("--quickswap", action="store_true", required=False)
debug = parser.add_argument_group("Debug Options")
debug.add_argument("--output_args", action="store_true", required=False, help="Output arguments to req_post.json")
debug.add_argument("--output_keylog", action="store_true", required=False, help="Outputs keylog for wireshark sniffing")
debug.add_argument("-h", "--help", action="help", help="Display this help text then exit")
log_settings = debug.add_mutually_exclusive_group()
log_settings.add_argument("-v", "--verbose", action="store_true", required=False, help="Enable verbose logging")
log_settings.add_argument("-q", "--quiet", action="store_true", required=False, help="Suppress all logging")

args = parser.parse_args()
verbose_logging = args.__dict__["verbose"]
output_keylog = args.__dict__["output_keylog"]
quiet_logging = args.__dict__["quiet"]
if quiet_logging:
    logger.setLevel("ERROR")


class SSLContextAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *argss, **kwargs):
        context = ssl.create_default_context()
        if output_keylog:
            os.environ["SSLKEYLOGFILE"] = "{}/keys.txt".format(os.getcwd())
            context.keylog_filename = "{}/keys.txt".format(os.getcwd())
        kwargs['ssl_context'] = context
        return super(SSLContextAdapter, self).init_poolmanager(*argss, **kwargs)


def create_nested_args(arg_data):
    nested_args_data = dict()
    for key in arg_data.__dict__:
        if key in ["verbose", "output_args", "quickswap", "heart-speed", "output_keylog"]:
            continue
        if key.find("_") >= 0:
            sub_args_key = key.split("_")[0]
            sub_args_sub_key = key.replace(sub_args_key + "_", "", 1)
            if sub_args_key not in nested_args_data.keys():
                nested_args_data[sub_args_key] = dict()
            sub_dict = nested_args_data[sub_args_key]
            val = arg_data.__dict__[key]
            sub_dict[sub_args_sub_key] = val
        else:
            val = arg_data.__dict__[key]
            nested_args_data[key.replace("-", "_")] = val
        if verbose_logging:
            logger.warning("{} -> {}".format(key, arg_data.__dict__[key]))
            logging.basicConfig(level=logging.DEBUG)
    return nested_args_data


nested_args = create_nested_args(args)


def get_bps():
    resp = requests.get("https://alttpr.com/base_rom/settings")
    bps_info = resp.json()
    url = "https://alttpr.com{}".format(bps_info["base_file"])
    fname = "{}/{}.bps".format(tempfile.gettempdir(), bps_info["rom_hash"])
    if not os.path.exists(fname):
        with open(fname, "wb") as bps_output:
            data = requests.get(url)
            bps_output.write(data.content)
    return fname


def prepare_rom(rom_bytes):
    target_buf = bytearray()
    while len(target_buf) < 2097152:
        target_buf.append(0)
    patch_filename = get_bps()
    with open(patch_filename, "rb") as bps_file:
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


def set_quickswap(rom_bytes, param):
    if param:
        rom_bytes[0x18004b] = 1
    else:
        rom_bytes[0x18004b] = 0
    return rom_bytes


def generate_new_rom(posted_args):
    global args
    post_data = json.dumps(posted_args, separators=(",", ":"))
    if args.__dict__["output_args"]:
        with open("req_post.json", "w") as p:
            p.write(post_data)

    with requests.Session() as s:
        s.mount("https://alttpr.com", SSLContextAdapter())
        s.get("https://alttpr.com/en/randomizer")
        headers = {
            "Content-Type": "application/json;charset=utf-8",
            "Accept": "application/json, text/plain, */*"
        }
        r = s.post("https://alttpr.com/api/randomizer", data=post_data, headers=headers)
        result = r.json()
        with open("Zelda no Densetsu - Kamigami no Triforce (Japan).sfc", "rb") as rom_file:
            rom_bytes = rom_file.read()
        patch_and_randomize_rom(rom_bytes, result["patch"], result["hash"], result["spoiler"])


def patch_and_randomize_rom(rom_bytes, patch, seed_id=None, spoiler=None):
    global args
    rom_bytes = prepare_rom(rom_bytes)
    for patch_segment in patch:
        for patch_index in patch_segment.keys():
            for b in patch_segment[patch_index]:
                rom_bytes[int(patch_index)] = b
                patch_index = str(int(patch_index) + 1)
    rom_bytes = set_heart_speed(rom_bytes, args.__dict__["heart-speed"])
    rom_bytes = set_quickswap(rom_bytes, args.__dict__["quickswap"])
    rom_bytes = update_checksum(rom_bytes)
    filename = "alttpr - {}-{}-{}_{}".format(spoiler["meta"]["logic"], spoiler["meta"]["mode"], spoiler["meta"]["goal"], seed_id)
    with open("{}.sfc".format(filename), "wb") as output_file:
        output_file.write(rom_bytes)
    if spoiler is not None:
        with open("hint_{}.txt".format(filename), "w") as output_hint:
            hints = spoiler
            output_hint.write("hint_group, hint_subgroup, hint_value\n")
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
    logger.info("https://alttpr.com/en/h/{}".format(seed_id))


generate_new_rom(nested_args)
