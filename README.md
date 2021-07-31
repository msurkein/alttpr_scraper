# alttpr_scraper
### Summary
> This is a small command line script which can be used to get a randomized LTTP ROM from https://alttpr.com
.  It was created in order to be an alternative to the CLI available in the main repo.

### Options
> - All of the main randomizer options available on the website are available via this client.  
> - Some of the "quality of life" options are not yet available.  Most notably, menu speed and heart color.
> - Custom sprites will likely never be available due to the reverse engineering required.
> - See https://alttpr.com/en/options for more information on what each of the options do

### Usage
`python main.py --help`
```
usage: main.py [--glitches {none,overworld_glitches,major_glitches,no_logic}] [--item-placement {advanced,basic}] [--dungeon-items {standard,full,mcs,mc}] [--accessibility {items,locations,none}] [--goal {ganon,fast_ganon,dungeons,pedestal,triforce-hunt}] [--crystals_ganon {0,1,2,3,4,5,6,7,random}]
               [--crystals_tower {0,1,2,3,4,5,6,7,random}] [--mode {open,inverted,retro}] [--entrances {none,simple,restricted,full,crossed,insanity}] [--hints {on,off}] [--weapons {randomized,swordless,vanilla,assured}] [--item_pool {normal,hard,expert,crowd_control}]
               [--item_functionality {normal,hard,expert}] [--tournament] [--spoilers {on,off}] [--lang {en,fr,de,es}] [--enemizer_boss-shuffle {none,random,full}] [--enemizer_enemy-shuffle {none,random,shuffled}] [--enemizer_enemy-damage {default,shuffled,random}]
               [--enemizer_enemy-health {default,easy,hard,expert}] [--heart-speed {2,1,0.25,0.5,0}] [--quickswap] [-v] [--output_args] [--output_keylog] [-h]

Generate a randomized LTTP ROM using the LTTP randomizer

Configuration Options:
  --glitches {none,overworld_glitches,major_glitches,no_logic}
  --item-placement {advanced,basic}
  --dungeon-items {standard,full,mcs,mc}
  --accessibility {items,locations,none}
  --goal {ganon,fast_ganon,dungeons,pedestal,triforce-hunt}
  --crystals_ganon {0,1,2,3,4,5,6,7,random}
  --crystals_tower {0,1,2,3,4,5,6,7,random}
  --mode {open,inverted,retro}
  --entrances {none,simple,restricted,full,crossed,insanity}
  --hints {on,off}
  --weapons {randomized,swordless,vanilla,assured}
  --item_pool {normal,hard,expert,crowd_control}
  --item_functionality {normal,hard,expert}
  --tournament
  --spoilers {on,off}
  --lang {en,fr,de,es}
  --enemizer_boss-shuffle {none,random,full}
  --enemizer_enemy-shuffle {none,random,shuffled}
  --enemizer_enemy-damage {default,shuffled,random}
  --enemizer_enemy-health {default,easy,hard,expert}
  --heart-speed {2,1,0.25,0.5,0}
  --quickswap

Debug Options:
  --output_args         Output arguments to req_post.json
  --output_keylog       Outputs keylog for wireshark sniffing
  -h, --help            Display this help text then exit
  -v, --verbose         Enable verbose logging
  -q, --quiet           Suppress all logging
  ```
### Sample Usage
`python3 main.py --item_functionality expert --weapons swordless --quickswap --enemizer_enemy-health expert`

### External Dependencies
> - requests
> - python-bps-continued

Both of the above dependencies can be installed by `pip install -r requirements.txt`