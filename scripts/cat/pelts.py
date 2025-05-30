import random
from random import choice
from re import sub

import i18n

from scripts.cat.sprites import sprites
from scripts.game_structure.game_essentials import game
from scripts.game_structure.localization import get_lang_config
from scripts.utility import adjust_list_text


class Pelt:
    sprites_names = {
        "SingleColour": 'single',
        'TwoColour': 'single',
        'Tabby': 'tabby',
        'Marbled': 'marbled',
        'Rosette': 'rosette',
        'Smoke': 'smoke',
        'Ticked': 'ticked',
        'Speckled': 'speckled',
        'Bengal': 'bengal',
        'Mackerel': 'mackerel',
        'Duotone': 'duotone',
        'Braided': 'braided',
        'Pinstripe': 'pinstripe',
        'Classic': 'classic',
        'Sokoke': 'sokoke',
        'Agouti': 'agouti',
        'Singlestripe': 'singlestripe',
        'Masked': 'masked',
        'Tortie': None,
        'Calico': None,
    }

    species = ['bird cat', 'earth cat']

    extra_traits_dict = {
    "wing_shape": ["elliptical", "high-speed", "hovering", "passive soaring", "active soaring"],

    "cat_size": ["tiny", "short", "small", "average", "tall", "large", "massive"],

    "scent": ["flowers", "poppies", "lilies", "rocks", "dirt", "mud", "fish", "salt", "lavendar", "catnip", "twolegs", "cobwebs", "crowfood", "rain", "snow", "frost", "cold air", "mist", "wood", "trees", "leaves", "grass", "corn", "smoke", "ash", "fire", "dog", "mildew", "eggs", "tar", "fog", "hot air", "citrus", "vanilla", "lemongrass", "blood", "honey", "milk", "eucalyptus", "pine needles", "oranges", "apples", "berries", "popcorn", "cinnamon", "oregano", "sage", "nutmeg", "orange blossom", "honeysuckle", "peaches", "jasmine", "grapefruit", "daffodils", "apricot", "cardamom", "bread", "gravel", "dust", "cheese", "raw chicken", "forests", "tomatoes", "marinara sauce", "chocolate", "lilies", "lint", "paint", "cat food", "hamburgers", "beef", "paprika", "rosemary", "cilantro", "sulfur", "cat breath", "mustard", "mayonnaise", "steel", "metal", "copper", "static electricity", "wires", "oil", "plastic", "toothpaste", "sugar", "clay", "sand", "butter", "toast", "feathers", "lettuce", "onions", "garlic", "violets", "clover", "cherries", "soybeans", "sweet peas", "black pepper", "paper", "olives", "olive oil", "gravy"],

    "body_type": ["average", "stocky", "lithe", "slender", "petite", "lanky", "delicate", "dainty", "ample", "plump", "muscular", "frail", "round"],

    "fur": ["well-kept", "messy", "well-kept", "groomed", "scraggly", "untidy", "sleek", "shaggy", "tangled", "wild", "sloppy", "well-groomed", "tidy", "neat", "stylish", "lustrous", "well-maintained"],

    "fur_texture": ["coarse", "smooth", "soft", "feathery", "thin", "thick", "wiry", "double coated", "fine", "prickly", "rough", "sleek", "silky"]
    }

    bird_wing_marks = ['FLECKS', 'TIPS', 'STRIPES', 'STREAKS', 'COVERTS', 'PRIMARIES', 'SPOTS', 'NONE']

    mane_marks_list = ['NONE', 'FULL', 'FADE', 'INVERTFADE', 'STRIPES', 'SPOTS', 'SMOKE']
    
    # ATTRIBUTES, including non-pelt related
    pelt_colours = [
        'WHITE', 'PALEGREY', 'SILVER', 'GREY', 'DARKGREY', 'GHOST', 'BLACK', 'CREAM', 'PALEGINGER',
        'GOLDEN', 'GINGER', 'DARKGINGER', 'SIENNA', 'LIGHTBROWN', 'LILAC', 'BROWN', 'GOLDEN-BROWN', 'DARKBROWN',
        'CHOCOLATE', 'ASH', 'LAVENDER', 'PALECREAM', 
        'BEIGE', 'DUST', 'DARKLAVENDER', 'SUNSET', 'OLDLILAC', 'GLASS', 'COPPER', 'GHOSTBROWN', 'GHOSTRED'
    ]
    pelt_c_no_white = [
        'SILVER', 'PALEGREY', 'SILVER', 'GREY', 'DARKGREY', 'GHOST', 'BLACK', 'CREAM', 'PALEGINGER',
        'GOLDEN', 'GINGER', 'DARKGINGER', 'SIENNA', 'LIGHTBROWN', 'LILAC', 'BROWN', 'GOLDEN-BROWN', 'DARKBROWN',
        'CHOCOLATE', 'ASH', 'LAVENDER'
        'BEIGE', 'DUST', 'DARKLAVENDER', 'SUNSET', 'OLDLILAC', 'COPPER', 'GHOSTBROWN', 'GHOSTRED'
    ]
    pelt_c_no_bw = [
        'PALEGREY', 'SILVER', 'GREY', 'DARKGREY', 'CREAM', 'PALEGINGER',
        'GOLDEN', 'GINGER', 'DARKGINGER', 'SIENNA', 'LIGHTBROWN', 'LILAC', 'BROWN', 'GOLDEN-BROWN', 'DARKBROWN',
        'CHOCOLATE', 'LAVENDER'
        'BEIGE', 'DUST', 'DARKLAVENDER', 'SUNSET', 'OLDLILAC', 'COPPER', 'GHOSTBROWN', 'GHOSTRED'
    ]

    tortiepatterns = ['ONE', 'TWO', 'THREE', 'FOUR', 'REDTAIL', 'DELILAH', 'MINIMALONE', 'MINIMALTWO', 'MINIMALTHREE',
                      'MINIMALFOUR', 'HALF',
                      'OREO', 'SWOOP', 'MOTTLED', 'SIDEMASK', 'EYEDOT', 'BANDANA', 'PACMAN', 'STREAMSTRIKE', 'ORIOLE',
                      'CHIMERA', 'DAUB', 'EMBER', 'BLANKET',
                      'ROBIN', 'BRINDLE', 'PAIGE', 'ROSETAIL', 'SAFI', 'SMUDGED', 'DAPPLENIGHT', 'STREAK', 'MASK',
                      'CHEST', 'ARMTAIL', 'SMOKE', 'GRUMPYFACE',
                      'BRIE', 'BELOVED', 'BODY', 'SHILOH', 'FRECKLED', 'HEARTBEAT']
    tortiebases = ['single', 'tabby', 'bengal', 'marbled', 'ticked', 'smoke', 'rosette', 'speckled', 'mackerel',
                   'classic', 'sokoke', 'agouti', 'singlestripe', 'masked',
                   'braided', 'duotone', 'pinstripe']

    pelt_length = ["short", "medium", "long"]
    eye_colours = ['YELLOW', 'AMBER', 'HAZEL', 'PALEGREEN', 'GREEN', 'BLUE', 'DARKBLUE', 'GREY', 'CYAN', 'EMERALD',
                   'PALEBLUE',
                   'PALEYELLOW', 'GOLD', 'HEATHERBLUE', 'COPPER', 'SAGE', 'COBALT', 'SUNLITICE', 'GREENYELLOW', 'ORANGE',
                   'BRONZE', 'SILVER', 
                   'DUST', 'PEBBLE', 
                   'OBSIDIAN', 'DARKHAZEL', 'OLIVE', 'SEAFOAM',
                   'SALMON', 'CRYSTAL', 'ROSEWOOD', 'LILAC',
                   'LAVENDER', 'PLUM', 'VIOLET']
    yellow_eyes = ['YELLOW', 'AMBER', 'PALEYELLOW', 'GOLD', 'COPPER', 'GREENYELLOW', 'BRONZE', 'SILVER', 'DUST', 'PEBBLE', 'HONEY', 'DARKAMBER', 'ORANGE']
    blue_eyes = ['BLUE', 'DARKBLUE', 'CYAN', 'PALEBLUE', 'HEATHERBLUE', 'COBALT', 'SUNLITICE', 'GREY']
    green_eyes = ['PALEGREEN', 'GREEN', 'EMERALD', 'SAGE', 'HAZEL', 'OBSIDIAN', 'DARKHAZEL', 'OLIVE', 'SEAFOAM']
    purple_eyes = ['GLASS', 'INDIGO', 'LAVENDER', 'PLUM', 'VIOLET', 'SALMON', 'CRYSTAL', 'ROSEWOOD', 'LILAC']

    # bite scars by @wood pank on discord

    # scars from other cats, other animals
    scars1 = [
        "ONE",
        "TWO",
        "THREE",
        "TAILSCAR",
        "SNOUT",
        "CHEEK",
        "SIDE",
        "THROAT",
        "TAILBASE",
        "BELLY",
        "LEGBITE",
        "NECKBITE",
        "FACE",
        "MANLEG",
        "BRIGHTHEART",
        "MANTAIL",
        "BRIDGE",
        "RIGHTBLIND",
        "LEFTBLIND",
        "BOTHBLIND",
        "BEAKCHEEK",
        "BEAKLOWER",
        "CATBITE",
        "RATBITE",
        "QUILLCHUNK",
        "QUILLSCRATCH",
        "HINDLEG",
        "BACK",
        "QUILLSIDE",
        "SCRATCHSIDE",
        "BEAKSIDE",
        "CATBITETWO",
        "FOUR",
    ]

    # missing parts
    scars2 = [
        "LEFTEAR",
        "RIGHTEAR",
        "NOTAIL",
        "HALFTAIL",
        "NOPAW",
        "NOLEFTEAR",
        "NORIGHTEAR",
        "NOEAR",
    ]

    # "special" scars that could only happen in a special event
    scars3 = [
        "SNAKE",
        "TOETRAP",
        "BURNPAWS",
        "BURNTAIL",
        "BURNBELLY",
        "BURNRUMP",
        "FROSTFACE",
        "FROSTTAIL",
        "FROSTMITT",
        "FROSTSOCK",
        "TOE",
        "SNAKETWO",
    ]

    # make sure to add plural and singular forms of new accs to acc_display.json so that they will display nicely
    plant_accessories = [
        "MAPLE LEAF",
        "HOLLY",
        "BLUE BERRIES",
        "FORGET ME NOTS",
        "RYE STALK",
        "CATTAIL",
        "POPPY",
        "ORANGE POPPY",
        "CYAN POPPY",
        "WHITE POPPY",
        "PINK POPPY",
        "BLUEBELLS",
        "LILY OF THE VALLEY",
        "SNAPDRAGON",
        "HERBS",
        "PETALS",
        "NETTLE",
        "HEATHER",
        "GORSE",
        "JUNIPER",
        "RASPBERRY",
        "LAVENDER",
        "OAK LEAVES",
        "CATMINT",
        "MAPLE SEED",
        "LAUREL",
        "BULB WHITE",
        "BULB YELLOW",
        "BULB ORANGE",
        "BULB PINK",
        "BULB BLUE",
        "CLOVER",
        "DAISY",
        "DRY HERBS",
        "DRY CATMINT",
        "DRY NETTLES",
        "DRY LAURELS",
    ]
    wild_accessories = [
        "RED FEATHERS",
        "BLUE FEATHERS",
        "JAY FEATHERS",
        "GULL FEATHERS",
        "SPARROW FEATHERS",
        "MOTH WINGS",
        "ROSY MOTH WINGS",
        "MORPHO BUTTERFLY",
        "MONARCH BUTTERFLY",
        "CICADA WINGS",
        "BLACK CICADA",
    ]

    tail_accessories = [
        "RED FEATHERS",
        "BLUE FEATHERS",
        "JAY FEATHERS",
        "GULL FEATHERS",
        "SPARROW FEATHERS",
        "CLOVER",
        "DAISY",
    ]
    collars = [
        "CRIMSON",
        "BLUE",
        "YELLOW",
        "CYAN",
        "RED",
        "LIME",
        "GREEN",
        "RAINBOW",
        "BLACK",
        "SPIKES",
        "WHITE",
        "PINK",
        "PURPLE",
        "MULTI",
        "INDIGO",
        "CRIMSONBELL",
        "BLUEBELL",
        "YELLOWBELL",
        "CYANBELL",
        "REDBELL",
        "LIMEBELL",
        "GREENBELL",
        "RAINBOWBELL",
        "BLACKBELL",
        "SPIKESBELL",
        "WHITEBELL",
        "PINKBELL",
        "PURPLEBELL",
        "MULTIBELL",
        "INDIGOBELL",
        "CRIMSONBOW",
        "BLUEBOW",
        "YELLOWBOW",
        "CYANBOW",
        "REDBOW",
        "LIMEBOW",
        "GREENBOW",
        "RAINBOWBOW",
        "BLACKBOW",
        "SPIKESBOW",
        "WHITEBOW",
        "PINKBOW",
        "PURPLEBOW",
        "MULTIBOW",
        "INDIGOBOW",
        "CRIMSONNYLON",
        "BLUENYLON",
        "YELLOWNYLON",
        "CYANNYLON",
        "REDNYLON",
        "LIMENYLON",
        "GREENNYLON",
        "RAINBOWNYLON",
        "BLACKNYLON",
        "SPIKESNYLON",
        "WHITENYLON",
        "PINKNYLON",
        "PURPLENYLON",
        "MULTINYLON",
        "INDIGONYLON",
    ]

    head_accessories = [
        "MOTH WINGS",
        "ROSY MOTH WINGS",
        "MORPHO BUTTERFLY",
        "MONARCH BUTTERFLY",
        "CICADA WINGS",
        "BLACK CICADA",
        "MAPLE LEAF",
        "HOLLY",
        "BLUE BERRIES",
        "FORGET ME NOTS",
        "RYE STALK",
        "CATTAIL",
        "POPPY",
        "ORANGE POPPY",
        "CYAN POPPY",
        "WHITE POPPY",
        "PINK POPPY",
        "BLUEBELLS",
        "LILY OF THE VALLEY",
        "SNAPDRAGON",
        "NETTLE",
        "HEATHER",
        "GORSE",
        "JUNIPER",
        "RASPBERRY",
        "LAVENDER",
        "OAK LEAVES",
        "CATMINT",
        "MAPLE SEED",
        "LAUREL",
        "BULB WHITE",
        "BULB YELLOW",
        "BULB ORANGE",
        "BULB PINK",
        "BULB BLUE",
        "DRY CATMINT",
        "DRY NETTLES",
        "DRY LAURELS",
    ]

    body_accessories = [
        "HERBS",
        "PETALS",
        "DRY HERBS"
    ]

    tabbies = ["Tabby", "Ticked", "Mackerel", "Classic", "Sokoke", "Agouti"]
    spotted = ["Speckled", "Rosette", "Pinstripe"]
    plain = ["SingleColour", "TwoColour", "Smoke", "Singlestripe"]
    exotic = ["Bengal", "Marbled", "Masked", "Braided", "Duotone"]
    torties = ["Tortie", "Calico"]
    # bird = ["Owl", "Corvid", "Fowl", "Cardinal", "Falcon"]
    # birdexotic = ["Parrot", "Paradise", "Mythical"]
    # bat = ["BatPelt"]
    # bug = ["Butterfly", "Exoticbutterfly"]
    pelt_categories = [tabbies, spotted, plain, exotic, torties] #, bird, bat, bug]
    
    # SPRITE NAMES
    single_colours = [
        'WHITE', 'GLASS', 'PALEGREY', 'SILVER', 'GREY', 'DARKGREY', 'GHOST', 'BLACK', 'CREAM', 'PALEGINGER',
        'GOLDEN', 'GINGER', 'DARKGINGER', 'SIENNA', 'LIGHTBROWN', 'LILAC', 'BROWN', 'GOLDEN-BROWN', 'DARKBROWN',
        'CHOCOLATE', 'LAVENDER', 'ASH', 'PALECREAM', 'COPPER', 'GHOSTBROWN', 'GHOSTRED'
    ]
    ginger_colours = ['PALECREAM', 'CREAM', 'PALEGINGER', 'GOLDEN', 'GINGER', 'DARKGINGER', 'SIENNA', 'GHOSTRED', 'COPPER']
    black_colours = ['SILVER', 'GREY', 'DARKGREY', 'GHOST', 'BLACK', 'ASH', 'LAVENDER']
    white_colours = ['WHITE', 'PALEGREY', 'GLASS']
    brown_colours = ['LIGHTBROWN', 'LILAC', 'BROWN', 'GOLDEN-BROWN', 'DARKBROWN', 'CHOCOLATE', 'GHOSTBROWN']
    colour_categories = [ginger_colours, black_colours, white_colours, brown_colours]
    eye_sprites = [
        "YELLOW",
        "AMBER",
        "HAZEL",
        "PALEGREEN",
        "GREEN",
        "BLUE",
        "DARKBLUE",
        "BLUEYELLOW",
        "BLUEGREEN",
        "GREY",
        "CYAN",
        "EMERALD",
        "PALEBLUE",
        "PALEYELLOW",
        "GOLD",
        "HEATHERBLUE",
        "COPPER",
        "SAGE",
        "COBALT",
        "SUNLITICE",
        "GREENYELLOW",
        "BRONZE",
        "SILVER",
        "ORANGE",
    ]
    little_white = [
        "LITTLE",
        "LIGHTTUXEDO",
        "BUZZARDFANG",
        "TIP",
        "BLAZE",
        "BIB",
        "VEE",
        "PAWS",
        "BELLY",
        "TAILTIP",
        "TOES",
        "BROKENBLAZE",
        "LILTWO",
        "SCOURGE",
        "TOESTAIL",
        "RAVENPAW",
        "HONEY",
        "LUNA",
        "EXTRA",
        "MUSTACHE",
        "REVERSEHEART",
        "SPARKLE",
        "RIGHTEAR",
        "LEFTEAR",
        "ESTRELLA",
        "REVERSEEYE",
        "BACKSPOT",
        "EYEBAGS",
        "LOCKET",
        "BLAZEMASK",
        "TEARS",
    ]
    mid_white = [
        "TUXEDO",
        "FANCY",
        "UNDERS",
        "DAMIEN",
        "SKUNK",
        "MITAINE",
        "SQUEAKS",
        "STAR",
        "WINGS",
        "DIVA",
        "SAVANNAH",
        "FADESPOTS",
        "BEARD",
        "DAPPLEPAW",
        "TOPCOVER",
        "WOODPECKER",
        "MISS",
        "BOWTIE",
        "VEST",
        "FADEBELLY",
        "DIGIT",
        "FCTWO",
        "FCONE",
        "MIA",
        "ROSINA",
        "PRINCESS",
        "DOUGIE",
    ]
    high_white = [
        "ANY",
        "ANYTWO",
        "BROKEN",
        "FRECKLES",
        "RINGTAIL",
        "HALFFACE",
        "PANTSTWO",
        "GOATEE",
        "PRINCE",
        "FAROFA",
        "MISTER",
        "PANTS",
        "REVERSEPANTS",
        "HALFWHITE",
        "APPALOOSA",
        "PIEBALD",
        "CURVED",
        "GLASS",
        "MASKMANTLE",
        "MAO",
        "PAINTED",
        "SHIBAINU",
        "OWL",
        "BUB",
        "SPARROW",
        "TRIXIE",
        "SAMMY",
        "FRONT",
        "BLOSSOMSTEP",
        "BULLSEYE",
        "FINN",
        "SCAR",
        "BUSTER",
        "HAWKBLAZE",
        "CAKE",
    ]
    mostly_white = [
        "VAN",
        "ONEEAR",
        "LIGHTSONG",
        "TAIL",
        "HEART",
        "MOORISH",
        "APRON",
        "CAPSADDLE",
        "CHESTSPECK",
        "BLACKSTAR",
        "PETAL",
        "HEARTTWO",
        "PEBBLESHINE",
        "BOOTS",
        "COW",
        "COWTWO",
        "LOVEBUG",
        "SHOOTINGSTAR",
        "EYESPOT",
        "PEBBLE",
        "TAILTWO",
        "BUDDY",
        "KROPKA",
    ]
    point_markings = ["COLOURPOINT", "RAGDOLL", "SEPIAPOINT", "MINKPOINT", "SEALPOINT"]
    vit = [
        "VITILIGO",
        "VITILIGOTWO",
        "MOON",
        "PHANTOM",
        "KARPATI",
        "POWDER",
        "BLEACHED",
        "SMOKEY",
    ]
    white_sprites = [
        little_white, mid_white, high_white, mostly_white, point_markings, vit, 'FULLWHITE']
    
    # list of all non-unique
    wing_white_list = ['FULLWHITE', 'WINGS', 'FRECKLES', 'TAIL', 'PEBBLESHINE', 'CAKE', 'KROPKA', 'HALFWHITE', 'GOATEE', 'PRINCE', 'PANTS', 'REVERSEPANTS', 'GLASS', 'PAINTED', 'SKUNK', 'STRIPES','UNDER', 'WOODPECKER', 'PAINTED', 'HAWKBLAZE', 'FINN', 'BULLSEYE', 'FADESPOTS', 'WINGTIPS', 'MITAINE', 'MISTER', 'WISP', 'APPALOOSA', 'INVERTEDWINGS', 'HEARTTWO', 'PEBBLE']

    # special patches that just look weird with other patches
    special_wing_white = ['WISP', 'APPALOOSA', 'INVERTEDWINGS', 'HEARTTWO', 'FULLWHITE', 'SAMMY']

    # selection dict - crying? not today
    # i love dicts
    wing_white_sel = {
        "little": ['little'],
        "mid": ['little', 'mid', 'high'],
        "high": ['high', 'mid'],
        "mostly": ['high', 'mostly'],

        "little_white": ['FADESPOTS', 'WINGTIPS', 'MITAINE', 'MISTER'],
        "mid_white": ['SKUNK', 'STRIPES', 'UNDER', 'WOODPECKER', 'PAINTED', 'HAWKBLAZE', 'FINN', 'BULLSEYE'],
        "high_white": ['HALFWHITE', 'GOATEE', 'PRINCE', 'PANTS', 'REVERSEPANTS', 'GLASS', 'PAINTED'],
        "mostly_white": ['FULLWHITE', 'WINGS', 'FRECKLES', 'TAIL', 'PEBBLESHINE', 'CAKE', 'KROPKA', 'PEBBLE']
    }

    skin_sprites = [
        "BLACK",
        "PINK",
        "DARKBROWN",
        "BROWN",
        "LIGHTBROWN",
        "DARK",
        "DARKGREY",
        "GREY",
        "DARKSALMON",
        "SALMON",
        "PEACH",
        "DARKMARBLED",
        "MARBLED",
        "LIGHTMARBLED",
        "DARKBLUE",
        "BLUE",
        "LIGHTBLUE",
        "RED",
    ]

    """Holds all appearance information for a cat. """

    def __init__(self,
                 name: str = "SingleColour",
                 length: str = "short",
                 colour: str = "WHITE",
                 white_patches: str = None,
                 wing_white_patches:str=None,
                 wing_marks: str = "NONE",
                 mane_marks: str = None,
                 mane: bool = True,
                 eye_color: str = "BLUE",
                 eye_colour2: str = None,
                 tortiebase: str = None,
                 tortiecolour: str = None,
                 pattern: str = None,
                 tortiepattern: str = None,
                 vitiligo: str = None,
                 points: str = None,
                accessory: list = None,
                 paralyzed: bool = False,
                 opacity: int = 100,
                 scars: list = None,
                 tint: str = "none",
                 skin: str = "BLACK",
                 species:str=None,
                 wing_count: int=2,
                 white_patches_tint: str = "none",
                 newborn_sprite:int=None,
                 kitten_sprite: int = None,
                 adol_sprite: int = None,
                 adult_sprite: int = None,
                 senior_sprite: int = None,
                 para_adult_sprite: int = None,
                 size: str = None,
                 wing_shape: str = None,
                 scent: str = None,
                 body_type: str = None,
                 fur: str = None,
                 fur_texture: str = None,
                 reverse: bool = False,
                 ) -> None:
        self.name = name
        self.colour = colour
        self.white_patches = white_patches
        self.wing_white_patches = wing_white_patches
        self.wing_marks = wing_marks
        self.mane_marks = mane_marks
        self.mane = mane
        self.eye_colour = eye_color
        self.eye_colour2 = eye_colour2
        self.tortiebase = tortiebase
        self.pattern = pattern
        self.tortiepattern = tortiepattern
        self.tortiecolour = tortiecolour
        self.vitiligo = vitiligo
        self.length = length
        self.points = points
        self.accessory = accessory
        self.paralyzed = paralyzed
        self.opacity = opacity
        self.scars = scars if isinstance(scars, list) else []
        self.tint = tint
        self.species = species
        self.wing_count = wing_count
        self.white_patches_tint = white_patches_tint
        self.cat_sprites = {
            "kitten": kitten_sprite if kitten_sprite is not None else 0,
            "adolescent": adol_sprite if adol_sprite is not None else 0,
            "young adult": adult_sprite if adult_sprite is not None else 0,
            "adult": adult_sprite if adult_sprite is not None else 0,
            "senior adult": adult_sprite if adult_sprite is not None else 0,
            "senior": senior_sprite if senior_sprite is not None else 0,
            "para_adult": para_adult_sprite if para_adult_sprite is not None else 0,
            "newborn": 20,
            "para_young": 17,
            "sick_kitten": 21,
            "sick adult": 18,
            "sick_young": 19
        }

        # extra traits
        self.size = size
        self.wing_shape = wing_shape
        self.scent = scent
        self.body_type = body_type
        self.fur = fur
        self.fur_texture = fur_texture
        
        self.reverse = reverse
        self.skin = skin

    @staticmethod
    def generate_new_pelt(species:str, gender:str, parents:tuple=(), age:str="adult"):
        new_pelt = Pelt()

        pelt_white = new_pelt.init_pattern_color(parents, gender)
        new_pelt.init_white_patches(pelt_white, parents)
        new_pelt.init_wing_patches()
        new_pelt.init_sprite(species)
        new_pelt.init_scars(age)
        new_pelt.init_accessories(age)
        new_pelt.init_eyes(parents)
        new_pelt.init_pattern()
        new_pelt.init_tint()
        new_pelt.init_extra_traits(parents)

        return new_pelt

    @staticmethod
    def init_species(self, parents:tuple=()):
        species_list = []
        weight = []
        
        # yeah that's right there's... 2 try statements - trust me they are both necessary
        try:
            try:
                if game.switches['cur_screen'] == "make clan screen":
                    if game.settings['earth_gen']:
                        species_list.append("earth cat")
                        weight.append(game.config["species_generation"]["earth"])
                    if game.settings['bird_gen']:
                        species_list.append("bird cat")
                        weight.append(game.config["species_generation"]["bird"])
                    if game.settings['bat_gen']:
                        species_list.append("bat cat")
                        weight.append(game.config["species_generation"]["bat"])
                else:
                    if game.clan.clan_settings['earth_gen__clan']:
                        species_list.append("earth cat")
                        weight.append(game.config["species_generation"]["earth"])
                    if game.clan.clan_settings['bird_gen__clan']:
                        species_list.append("bird cat")
                        weight.append(game.config["species_generation"]["bird"])
                    if game.clan.clan_settings['bat_gen__clan']:
                        species_list.append("bat cat")
                        weight.append(game.config["species_generation"]["bat"])
            except:
                    if game.settings['earth_gen']:
                        species_list.append("earth cat")
                        weight.append(game.config["species_generation"]["earth"])
                    if game.settings['bird_gen']:
                        species_list.append("bird cat")
                        weight.append(game.config["species_generation"]["bird"])
                    if game.settings['bat_gen']:
                        species_list.append("bat cat")
                        weight.append(game.config["species_generation"]["bat"])

            # species_list = ["earth cat", "bird cat", "bat cat"] #, "bug cat"
            if self.species is None:
                if parents:
                    species = Pelt.species_inheritance(species_list, parents, weight)
                    return species
                else:
                    species = choice(
                        random.choices(species_list, weights=weight, k=1)
                    )
                    return species
            else:
                return self.species
        except:
            return "ERROR"
        
    @staticmethod
    def randomize_species(species_list:list=[], species_weights:list=[]):
        chosen_species = choice(
            random.choices(species_list, weights=species_weights, k = 1)
        )
        return chosen_species
    
    @staticmethod
    def species_inheritance(species_list, parents:tuple=(), species_weights:list=[]): # guys I cried while making this because what the hell-
        par_species = []
        for p in parents:
            if p:
                if p.species:
                    par_species.append(p.species)
        
        if not par_species:
            print("Warning - no parents: species randomized")
            chosen_species = Pelt.randomize_species(species_list, species_weights)
            return chosen_species

        chosen_species = random.choice(par_species)
        return chosen_species
    
    @staticmethod 
    def wing_count_inheritance(species, parents:tuple=()):
        par_wing_count = []
        p_count = 0
        for p in parents:
            if p:
                if p.wing_count:
                    p_count += 1 # count parents
                    par_wing_count.append(p.wing_count)
        
        try:
            if (par_wing_count[0] == 2 and par_wing_count[1] == 2):
                weights = [200, 1, 0] # extremely rare chance of hereditary one wing - 2 wing x 2 wing
            elif (par_wing_count[0] == 2 and par_wing_count[1] == 1) or (par_wing_count[1] == 2 and par_wing_count[0] == 1):
                weights = [50, 10, 0] # winged cat x winged cat 1 wing
            elif (par_wing_count[0] == 2 and par_wing_count[1] == 0) or (par_wing_count[1] == 2 and par_wing_count[0] == 0):
                weights = [95, 35, 1] # earth cat/0 wing x winged cat
            elif (par_wing_count[0] == 1 and par_wing_count[1] == 1):
                weights = [60, 70, 5] # 1 winged cat x 1 winged cat
            elif (par_wing_count[0] == 1 and par_wing_count[1] == 0) or (par_wing_count[1] == 1 and par_wing_count[0] == 0):
                weights = [20, 80, 5] # 1 winged cat x 0 winged
            else:
                weights = [0, 1, 120] # 0 wing x 0 wing
        except: # if there is only one parent (or none)
            if not par_wing_count:
                selected = Pelt.randomize_wing_count(species)
                return selected
            else:
                if par_wing_count[0] == 2:
                    weights = [200, 1, 0] # extremely rare chance of hereditary one wing
                elif par_wing_count[0] == 1:
                    weights = [70, 50, 1]
                else:
                    weights = [0, 1, 120]
        
        if species != "earth cat":
            selected = choice(
                random.choices([2, 1, 0], weights=weights, k = 1)
            )
            return selected
        else:
            return 0

    @staticmethod 
    def randomize_wing_count(species):
        if species == "earth cat":
            chosen_count = 0
        else:
            chosen_count = choice(
            random.choices([2, 1, 0], weights=[90, 2, 0], k = 1)
            )
        return chosen_count
    
    @staticmethod
    def init_wing_count(self, parents:tuple=()):
        if self.wing_count is None:
            if parents:
                chosen_count = Pelt.wing_count_inheritance(self.species, parents)
                return chosen_count
            else:
                if self.species == "earth cat":
                    chosen_count = 0
                else:
                    chosen_count = choice(
                random.choices([2, 1, 0], weights=[90, 2, 0], k = 1)
            )
                if chosen_count == 1:
                    print("One wing!")
                return chosen_count
        else:
            return self.wing_count

            
    def init_extra_traits(self, parents:tuple=()):
        if parents:
            Pelt.extra_traits_inheritance(self, parents)
        else:
            if self.wing_shape is None:
                self.wing_shape = random.choices(Pelt.extra_traits_dict["wing_shape"], weights=[20, 15, 1, 25, 5])[0]
            if self.size is None:
                self.size = random.choices(Pelt.extra_traits_dict["cat_size"], weights=[1, 3, 5, 20, 5, 3, 1])[0]
            if self.body_type is None:
                self.body_type = random.choice(Pelt.extra_traits_dict["body_type"])
            if self.fur_texture is None:
                self.fur_texture = random.choice(Pelt.extra_traits_dict["fur_texture"])
            if self.fur is None:
                self.fur = random.choice(Pelt.extra_traits_dict["fur"])
            if self.scent is None:
                self.scent = random.choice(Pelt.extra_traits_dict["scent"])

    def extra_traits_inheritance(self, parents:tuple=()):
        par_fur_texture = []
        par_body_type = []
        par_size = []
        add_weights = []

        # init base weights
        wing_shape_weights = [5, 3, 1, 5, 1]
        cat_size_weights = [1, 3, 5, 10, 5, 3, 1]
        
        # append parent traits
        for p in parents:
            par_fur_texture.append(p.pelt.fur_texture)
            par_size.append(p.pelt.size)
            par_body_type.append(p.pelt.body_type)

            if p.pelt.wing_shape == "elliptical":
                add_weights = [25, 0, 0, 5, 0]
            elif p.pelt.wing_shape == "high-speed":
                add_weights = [0, 25, 0, 5, 0]
            elif p.pelt.wing_shape == "hovering":
                add_weights = [0, 0, 20, 0, 0]
            elif p.pelt.wing_shape == "passive soaring":
                add_weights = [5, 0, 0, 25, 1]
            elif p.pelt.wing_shape == "active soaring":
                add_weights = [1, 0, 0, 5, 25]

            for x in range(0, len(wing_shape_weights)):
                wing_shape_weights[x] += add_weights[x]

            if p.pelt.size == "tiny":
                add_weights = [10, 5, 3, 5, 0, 0, 0]
            elif p.pelt.size == "short":
                add_weights = [2, 10, 3, 10, 1, 0, 0]
            elif p.pelt.size == "small":
                add_weights = [1, 3, 10, 15, 1, 1, 0]
            elif p.pelt.size == "average":
                add_weights = [0, 1, 5, 20, 5, 1, 0]
            elif p.pelt.size == "tall":
                add_weights = [0, 1, 3, 15, 10, 3, 1]
            elif p.pelt.size == "large":
                add_weights = [0, 1, 1, 10, 3, 10, 2]
            elif p.pelt.size == "massive":
                add_weights = [0, 0, 0, 5, 3, 3, 10]

            for x in range(0, len(cat_size_weights)):
                cat_size_weights[x] += add_weights[x]
            
        self.wing_shape = random.choices(Pelt.extra_traits_dict["wing_shape"], weights=wing_shape_weights)[0]
        self.size = random.choices(Pelt.extra_traits_dict["cat_size"], weights=cat_size_weights)[0]
        self.body_type = random.choice(par_body_type * 20 + Pelt.extra_traits_dict["body_type"])
        self.fur_texture = random.choice(par_fur_texture * 20 + Pelt.extra_traits_dict["fur_texture"])
        self.fur = random.choice(Pelt.extra_traits_dict["fur"])
        self.scent = random.choice(Pelt.extra_traits_dict["scent"])
    
    def check_and_convert(self, convert_dict, extra_traits):
        """Checks for old-type properties for the appearance-related properties
        that are stored in Pelt, and converts them. To be run when loading a cat in. """
        
        if self.species is None:
            self.species = Pelt.init_species(self)

        if self.species in [None, "None", "none"]:
            print("self.species returned with None. Report.")

        if self.wing_count is None:
            if self.species in ["bird cat", "bat cat"]:
                self.wing_count = 2
            else:
                self.wing_count = 0

        # Extra traits
        if not extra_traits:
            Pelt.init_extra_traits(self)

        # First, convert from some old names that may be in white_patches. 
        if self.white_patches == 'POINTMARK':
            self.white_patches = "SEALPOINT"
        elif self.white_patches == "PANTS2":
            self.white_patches = "PANTSTWO"
        elif self.white_patches == "ANY2":
            self.white_patches = "ANYTWO"
        elif self.white_patches == "VITILIGO2":
            self.white_patches = "VITILIGOTWO"

        if self.vitiligo == "VITILIGO2":
            self.vitiligo = "VITILIGOTWO"

        # Move white_patches that should be in vit or points.
        if self.white_patches in Pelt.vit:
            self.vitiligo = self.white_patches
            self.white_patches = None
        elif self.white_patches in Pelt.point_markings:
            self.points = self.white_patches
            self.white_patches = None

        if self.wing_white_patches == None and self.white_patches:
            print("No wing patches when there should be.")
            self.init_wing_patches()

        if self.wing_marks == "none":
            # Gather weights depending on pelt group
            if self.name in Pelt.tabbies:
                weight = [20, 20, 20, 10, 10, 10, 10, 10]
            elif self.name in Pelt.spotted:
                weight = [30, 20, 10, 10, 10, 10, 30, 10]
            elif self.name in Pelt.plain:
                weight = [10, 15, 10, 10, 20, 20, 10, 30]
            elif self.name in Pelt.exotic:
                weight = [30, 10, 20, 15, 10, 10, 30, 10]
            else:
                weight = [1, 1, 1, 1, 1, 1, 1, 1]
            self.wing_marks = choice(
            random.choices(Pelt.bird_wing_marks, weights=weight, k=1)
            )

        # generate mane info
        if not self.mane_marks:
            # Gather weights depending on pelt group
            #'NONE', 'FULL', 'FADE', 'INVERTFADE', 'STRIPES', 'SPOTS', 'SMOKE'
            if self.name in Pelt.tabbies:
                weight = [5, 30, 30, 30, 30, 0, 0]
            elif self.name in Pelt.spotted:
                weight = [5, 30, 30, 30, 0, 30, 0]
            elif self.name is 'Smoke':
                weight = [0, 30, 20, 20, 0, 0, 30]
            elif self.name in Pelt.plain:
                weight = [30, 30, 20, 20, 0, 0, 10]
            elif self.name in Pelt.exotic:
                weight = [10, 30, 30, 30, 0, 30, 0]
            else:
                weight = [1, 1, 1, 1, 1, 1, 1]
            self.mane_marks = choice(
            random.choices(Pelt.mane_marks_list, weights=weight, k=1)
            )
        
        if self.tortiepattern and "tortie" in self.tortiepattern:
            self.tortiepattern = sub("tortie", "", self.tortiepattern.lower())
            if self.tortiepattern == "solid":
                self.tortiepattern = "single"

        if self.white_patches in convert_dict["old_creamy_patches"]:
            self.white_patches = convert_dict["old_creamy_patches"][self.white_patches]
            self.white_patches_tint = "darkcream"
        elif self.white_patches in ["SEPIAPOINT", "MINKPOINT", "SEALPOINT"]:
            self.white_patches_tint = "none"

        # Eye Color Convert Stuff
        if self.eye_colour == "BLUE2":
            self.eye_colour = "COBALT"
        if self.eye_colour2 == "BLUE2":
            self.eye_colour2 = "COBALT"

        if self.eye_colour in ["BLUEYELLOW", "BLUEGREEN"]:
            if self.eye_colour == "BLUEYELLOW":
                self.eye_colour2 = "YELLOW"
            elif self.eye_colour == "BLUEGREEN":
                self.eye_colour2 = "GREEN"
            self.eye_colour = "BLUE"
        
        # convert back to old stuff with base clangen :P
        if self.cat_sprites['newborn'] is not 20:
            self.cat_sprites['newborn'] = 20
        if self.cat_sprites['kitten'] not in [0, 1, 2]:
            self.cat_sprites['kitten'] = random.randint(0, 2)
        if self.cat_sprites['adolescent'] not in [3, 4, 5]:
            self.cat_sprites['adolescent'] = random.randint(3, 5)
        if self.length == 'long':
            if self.cat_sprites['adult'] not in [9, 10, 11]:
                if self.cat_sprites['adult'] == 0:
                    self.cat_sprites['adult'] = 9
                elif self.cat_sprites['adult'] == 1:
                    self.cat_sprites['adult'] = 10
                elif self.cat_sprites['adult'] == 3:
                    self.cat_sprites['adult'] = 11
                else:
                    self.cat_sprites['adult'] = random.randint(9, 11)
                self.cat_sprites['young adult'] = self.cat_sprites['adult']
                self.cat_sprites['senior adult'] = self.cat_sprites['adult']
                self.cat_sprites['para_adult'] = 16
        else:
            if self.cat_sprites['adult'] not in [6, 7, 8]:
                self.cat_sprites['adult'] = random.randint(6, 8)
                self.cat_sprites['young adult'] = self.cat_sprites['adult']
                self.cat_sprites['senior adult'] = self.cat_sprites['adult']
            self.cat_sprites['para_adult'] = 15
        if self.cat_sprites['senior'] not in [12, 13, 14]:
            if self.cat_sprites["senior"] == 3:
                self.cat_sprites["senior"] = 12
            elif self.cat_sprites["senior"] == 4:
                self.cat_sprites["senior"] = 13
            elif self.cat_sprites["senior"] == 5:
                self.cat_sprites["senior"] = 14
            else:
                self.cat_sprites['senior'] = random.randint(12, 14)
        
        if self.pattern in convert_dict["old_tortie_patches"]:
            old_pattern = self.pattern
            self.pattern = convert_dict["old_tortie_patches"][old_pattern][1]

            # If the pattern is old, there is also a chance the base color is stored in
            # tortiecolour. That may be different from the pelt color ("main" for torties)
            # generated before the "ginger-on-ginger" update. If it was generated after that update,
            # tortiecolour and pelt_colour will be the same. Therefore, let's also re-set the pelt color
            self.colour = self.tortiecolour
            self.tortiecolour = convert_dict["old_tortie_patches"][old_pattern][0]

        if self.pattern == "MINIMAL1":
            self.pattern = "MINIMALONE"
        elif self.pattern == "MINIMAL2":
            self.pattern = "MINIMALTWO"
        elif self.pattern == "MINIMAL3":
            self.pattern = "MINIMALTHREE"
        elif self.pattern == "MINIMAL4":
            self.pattern = "MINIMALFOUR"

        if isinstance(self.accessory, str):
            self.accessory = [self.accessory]


    def init_eyes(self, parents):
        """Sets eye color for this cat's pelt. Takes parents' eye colors into account.
        Heterochromia is possible based on the white-ness of the pelt, so the pelt color and white_patches must be
        set before this function is called.

        :param parents: List[Cat] representing this cat's parents

        :return: None
        """
        if not parents:
            self.eye_colour = choice(Pelt.eye_colours)
        else:
            self.eye_colour = choice(
                [i.pelt.eye_colour for i in parents] + [choice(Pelt.eye_colours)]
            )

        # White patches must be initalized before eye color.
        num = game.config["cat_generation"]["base_heterochromia"]
        if (
            self.white_patches in Pelt.high_white
            or self.white_patches in Pelt.mostly_white
            or self.white_patches == "FULLWHITE"
            or self.colour == "WHITE"
        ):
            num = num - 90
        if self.white_patches == "FULLWHITE" or self.colour == "WHITE":
            num -= 10
        for _par in parents:
            if _par.pelt.eye_colour2:
                num -= 10

        if num < 0:
            num = 1

        if not random.randint(0, num):
            colour_wheel = [Pelt.yellow_eyes, Pelt.blue_eyes, Pelt.green_eyes, Pelt.purple_eyes]
            for colour in colour_wheel[:]:
                if self.eye_colour in colour:
                    colour_wheel.remove(
                        colour
                    )  # removes the selected list from the options
                    self.eye_colour2 = choice(
                        choice(colour_wheel)
                    )  # choose from the remaining two lists
                    break

    def pattern_color_inheritance(self, parents: tuple = (), gender="female"):
        # setting parent pelt categories
        # We are using a set, since we don't need this to be ordered, and sets deal with removing duplicates.
        par_peltlength = set()
        par_peltcolours = set()
        par_peltnames = set()
        par_wingmarks = set()
        par_mane = []
        par_pelts = []
        par_white = []
        for p in parents:
            if p:
                # Gather pelt color.
                par_peltcolours.add(p.pelt.colour)

                # Gather pelt length
                par_peltlength.add(p.pelt.length)

                # Gather wing marks
                par_wingmarks.add(p.pelt.wing_marks)

                # Gather pelt name
                if p.pelt.name in Pelt.torties:
                    par_peltnames.add(p.pelt.tortiebase.capitalize())
                else:
                    par_peltnames.add(p.pelt.name)

                # Gather exact pelts, for direct inheritance.
                par_pelts.append(p.pelt)

                # Gather bat mane
                par_mane.append(p.pelt.mane)

                # Gather if they have white in their pelt.
                par_white.append(p.pelt.white)
            else:
                # If order for white patches to work correctly, we also want to randomly generate a "pelt_white"
                # for each "None" parent (missing or unknown parent)
                par_white.append(bool(random.getrandbits(1)))

                # Append None
                # Gather pelt color.
                par_peltcolours.add(None)
                par_peltlength.add(None)
                par_peltnames.add(None)
                par_mane.append(True)
                par_wingmarks.add("unknown")

        # If this list is empty, something went wrong.
        if not par_peltcolours:
            print("Warning - no parents: pelt randomized")
            return self.randomize_pattern_color(gender)

        # There is a 1/10 chance for kits to have the exact same pelt as one of their parents
        if not random.randint(
            0, game.config["cat_generation"]["direct_inheritance"]
        ):  # 1/10 chance
            selected = choice(par_pelts)
            self.name = selected.name
            self.length = selected.length
            self.colour = selected.colour
            self.tortiebase = selected.tortiebase
            return selected.white

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT
        # ------------------------------------------------------------------------------------------------------------#

        # Determine pelt.
        weights = [
            0,
            0,
            0,
            0,
        ]  # Weights for each pelt group. It goes: (tabbies, spotted, plain, exotic)
        for p_ in par_peltnames:
            if p_ in Pelt.tabbies:
                add_weight = (50, 10, 5, 7)
            elif p_ in Pelt.spotted:
                add_weight = (10, 50, 5, 5)
            elif p_ in Pelt.plain:
                add_weight = (5, 5, 50, 0)
            elif p_ in Pelt.exotic:
                add_weight = (15, 15, 1, 45)
            elif (
                p_ is None
            ):  # If there is at least one unknown parent, a None will be added to the set.
                add_weight = (35, 20, 30, 15)
            else:
                add_weight = (0, 0, 0, 0)

        for x in range(0, len(weights)):
            weights[x] += add_weight[x]

        # A quick check to make sure all the weights aren't 0
        if all([x == 0 for x in weights]):
            weights = [1, 1, 1, 1]

        # Now, choose the pelt category and pelt. The extra 0 is for the tortie pelts,
        chosen_pelt = choice(
            random.choices(Pelt.pelt_categories, weights=weights + [0], k=1)[0]
        )



        # Tortie chance
        tortie_chance_f = game.config["cat_generation"][
            "base_female_tortie"
        ]  # There is a default chance for female tortie
        tortie_chance_m = game.config["cat_generation"]["base_male_tortie"]
        for p_ in par_pelts:
            if p_.name in Pelt.torties:
                tortie_chance_f = int(tortie_chance_f / 2)
                tortie_chance_m = tortie_chance_m - 1
                break

        # Determine tortie:
        if gender == "female":
            torbie = random.getrandbits(tortie_chance_f) == 1
        else:
            torbie = random.getrandbits(tortie_chance_m) == 1

        chosen_tortie_base = None
        if torbie:
            # If it is tortie, the chosen pelt above becomes the base pelt.
            chosen_tortie_base = chosen_pelt
            if chosen_tortie_base in ["TwoColour", "SingleColour"]:
                chosen_tortie_base = "Single"
            chosen_tortie_base = chosen_tortie_base.lower()
            chosen_pelt = random.choice(Pelt.torties)

        # Determine Wing Markings
        weights = [0, 0, 0, 0, 0, 0, 0, 0]

        # Gather weights depending on pelt group
        if chosen_pelt in Pelt.torties:
            if chosen_tortie_base in Pelt.tabbies:
                add_w_weight = (20, 20, 20, 0, 0, 0, 0, 0)
            elif chosen_tortie_base in Pelt.spotted:
                add_w_weight = (5, 20, 0, 0, 0, 0, 20, 0)
            elif chosen_tortie_base in Pelt.plain:
                add_w_weight = (0, 5, 0, 0, 20, 20, 0, 30)
            elif chosen_tortie_base in Pelt.exotic:
                add_w_weight = (20, 0, 30, 10, 0, 0, 20, 0)
            else:
                add_w_weight = (1, 1, 1, 1, 1, 1, 1, 1)
        else:
            # Gather weights depending on pelt group
            if chosen_pelt in Pelt.tabbies:
                add_w_weight = (20, 20, 20, 0, 0, 0, 0, 0)
            elif chosen_pelt in Pelt.spotted:
                add_w_weight = (5, 20, 0, 0, 0, 0, 20, 0)
            elif chosen_pelt in Pelt.plain:
                add_w_weight = (0, 5, 0, 0, 20, 20, 0, 30)
            elif chosen_pelt in Pelt.exotic:
                add_w_weight = (20, 0, 30, 10, 0, 0, 20, 0)
            else:
                add_w_weight = (1, 1, 1, 1, 1, 1, 1, 1)

        # ['FLECKS', 'TIPS', 'STRIPES', 'STREAKS', 'COVERTS', 'PRIMARIES', 'SPOTS', None]
        for p_ in par_wingmarks:
            if p_ == "FLECKS":
                add_w_weight += (40, 20, 30, 20, 20, 20, 30, 10)
            if p_ == "TIPS":
                add_w_weight += (20, 40, 10, 15, 30, 30, 20, 10)
            if p_ == "STRIPES":
                add_w_weight += (20, 20, 40, 20, 10, 20, 30, 10)
            if p_ == "STREAKS":
                add_w_weight += (20, 20, 20, 40, 10, 20, 30, 10)
            if p_ == "COVERTS":
                add_w_weight += (10, 30, 20, 10, 40, 30, 20, 30)
            if p_ == "PRIMARIES":
                add_w_weight += (10, 30, 20, 10, 30, 40, 20, 30)
            if p_ == "SPOTS":
                add_w_weight += (25, 20, 30, 15, 30, 30, 40, 10)
            elif p_ is "unknown":
                add_w_weight += (10, 20, 10, 10, 40, 40, 10, 40)
            else:
                add_w_weight += (5, 15, 5, 5, 15, 15, 5, 40)

        for x in range(0, len(weights)):
            weights[x] += add_w_weight[x]

        # A quick check to make sure all the weights aren't 0
        if all([x == 0 for x in weights]):
            weights = [1, 1, 1, 1, 1, 1, 1, 1]

        chosen_wing_marks = choice(
            random.choices(Pelt.bird_wing_marks, weights=weights, k=1)
        )

        # Gather weights depending on pelt group
        if chosen_pelt in ["Tortie", "Calico"]:
            #'NONE', 'FULL', 'FADE', 'INVERTFADE', 'STRIPES', 'SPOTS', 'SMOKE'
            if chosen_tortie_base in Pelt.tabbies:
                weight = [5, 30, 30, 30, 30, 0, 0]
            elif chosen_tortie_base in Pelt.spotted:
                weight = [5, 30, 30, 30, 0, 30, 0]
            elif chosen_tortie_base is 'Smoke':
                weight = [0, 30, 20, 20, 0, 0, 30]
            elif chosen_tortie_base in Pelt.plain:
                weight = [30, 30, 20, 20, 0, 0, 10]
            elif chosen_tortie_base in Pelt.exotic:
                weight = [10, 30, 30, 30, 0, 30, 0]
            else:
                weight = [1, 1, 1, 1, 1, 1, 1]
        else:
            #'NONE', 'FULL', 'FADE', 'INVERTFADE', 'STRIPES', 'SPOTS', 'SMOKE'
            if chosen_pelt in Pelt.tabbies:
                weight = [5, 30, 30, 30, 30, 0, 0]
            elif chosen_pelt in Pelt.spotted:
                weight = [5, 30, 30, 30, 0, 30, 0]
            elif chosen_pelt is 'Smoke':
                weight = [0, 30, 20, 20, 0, 0, 30]
            elif chosen_pelt in Pelt.plain:
                weight = [30, 30, 20, 20, 0, 0, 10]
            elif chosen_pelt in Pelt.exotic:
                weight = [10, 30, 30, 30, 0, 30, 0]
            else:
                weight = [1, 1, 1, 1, 1, 1, 1]

        # select mane markings
        chosen_mane_marks = choice(
        random.choices(Pelt.mane_marks_list, weights=weight, k=1)
        )

        # determine mane
        chosen_mane = random.choice(par_mane)

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT COLOUR
        # ------------------------------------------------------------------------------------------------------------#
        # Weights for each colour group. It goes: (ginger_colours, black_colours, white_colours, brown_colours)
        weights = [0, 0, 0, 0]
        for p_ in par_peltcolours:
            if p_ in Pelt.ginger_colours:
                add_weight = (40, 0, 0, 10)
            elif p_ in Pelt.black_colours:
                add_weight = (0, 40, 2, 5)
            elif p_ in Pelt.white_colours:
                add_weight = (0, 5, 40, 0)
            elif p_ in Pelt.brown_colours:
                add_weight = (10, 5, 0, 35)
            elif p_ is None:
                add_weight = (40, 40, 40, 40)
            else:
                add_weight = (0, 0, 0, 0)

            for x in range(0, len(weights)):
                weights[x] += add_weight[x]

            # A quick check to make sure all the weights aren't 0
            if all([x == 0 for x in weights]):
                weights = [1, 1, 1, 1]

        chosen_pelt_color = choice(
            random.choices(Pelt.colour_categories, weights=weights, k=1)[0]
        )

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT LENGTH
        # ------------------------------------------------------------------------------------------------------------#

        weights = [0, 0, 0]  # Weights for each length. It goes (short, medium, long)
        for p_ in par_peltlength:
            if p_ == "short":
                add_weight = (50, 10, 2)
            elif p_ == "medium":
                add_weight = (25, 50, 25)
            elif p_ == "long":
                add_weight = (2, 10, 50)
            elif p_ is None:
                add_weight = (10, 10, 10)
            else:
                add_weight = (0, 0, 0)

            for x in range(0, len(weights)):
                weights[x] += add_weight[x]

        # A quick check to make sure all the weights aren't 0
        if all([x == 0 for x in weights]):
            weights = [1, 1, 1]

        chosen_pelt_length = random.choices(Pelt.pelt_length, weights=weights, k=1)[0]

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT WHITE
        # ------------------------------------------------------------------------------------------------------------#

        # There are 94 percentage points that can be added by
        # parents having white. If we have more than two, this
        # will keep that the same.
        percentage_add_per_parent = int(94 / len(par_white))
        chance = 3
        for p_ in par_white:
            if p_:
                chance += percentage_add_per_parent

        chosen_white = random.randint(1, 100) <= chance

        # Adjustments to pelt chosen based on if the pelt has white in it or not.
        if chosen_pelt in ["TwoColour", "SingleColour"]:
            if chosen_white:
                chosen_pelt = "TwoColour"
            else:
                chosen_pelt = "SingleColour"
        elif chosen_pelt == "Calico":
            if not chosen_white:
                chosen_pelt = "Tortie"

        # SET THE PELT
        self.name = chosen_pelt
        self.wing_marks = chosen_wing_marks
        self.mane_marks = chosen_mane_marks
        self.mane = chosen_mane
        self.colour = chosen_pelt_color
        self.length = chosen_pelt_length
        self.tortiebase = (
            chosen_tortie_base  # This will be none if the cat isn't a tortie.
        )
        return chosen_white

    def randomize_pattern_color(self, gender):
        # ------------------------------------------------------------------------------------------------------------#
        #   PELT
        # ------------------------------------------------------------------------------------------------------------#

        # Determine pelt.
        chosen_pelt = choice(
            random.choices(Pelt.pelt_categories, weights=(35, 20, 30, 15, 0), k=1)[0]
        )

        # Tortie chance
        # There is a default chance for female tortie, slightly increased for completely random generation.
        tortie_chance_f = game.config["cat_generation"]["base_female_tortie"] - 1
        tortie_chance_m = game.config["cat_generation"]["base_male_tortie"]
        if gender == "female":
            torbie = random.getrandbits(tortie_chance_f) == 1
        else:
            torbie = random.getrandbits(tortie_chance_m) == 1

        chosen_tortie_base = None
        if torbie:
            # If it is tortie, the chosen pelt above becomes the base pelt.
            chosen_tortie_base = chosen_pelt
            if chosen_tortie_base in ["TwoColour", "SingleColour"]:
                chosen_tortie_base = "Single"
            chosen_tortie_base = chosen_tortie_base.lower()
            chosen_pelt = random.choice(Pelt.torties)

        
        # Gather weights depending on pelt group
        if chosen_pelt in ["Tortie", "Calico"]:
            if chosen_tortie_base in Pelt.tabbies:
                wm_weight = [20, 20, 20, 10, 10, 10, 10, 10]
            elif chosen_tortie_base in Pelt.spotted:
                wm_weight = [30, 20, 10, 10, 10, 10, 30, 10]
            elif chosen_tortie_base in Pelt.plain:
                wm_weight = [10, 15, 10, 10, 20, 20, 10, 30]
            elif chosen_tortie_base in Pelt.exotic:
                wm_weight = [30, 10, 20, 15, 10, 10, 30, 10]
            else:
                wm_weight = [1, 1, 1, 1, 1, 1, 1, 1]
            
            # Gather weights depending on pelt group
            #'NONE', 'FULL', 'FADE', 'INVERTFADE', 'STRIPES', 'SPOTS', 'SMOKE'
            if chosen_tortie_base in Pelt.tabbies:
                weight = [5, 30, 30, 30, 30, 0, 0]
            elif chosen_tortie_base in Pelt.spotted:
                weight = [5, 30, 30, 30, 0, 30, 0]
            elif chosen_tortie_base is 'Smoke':
                weight = [0, 30, 20, 20, 0, 0, 30]
            elif chosen_tortie_base in Pelt.plain:
                weight = [30, 30, 20, 20, 0, 0, 10]
            elif chosen_tortie_base in Pelt.exotic:
                weight = [10, 30, 30, 30, 0, 30, 0]
            else:
                weight = [1, 1, 1, 1, 1, 1, 1]
        else:
            if chosen_pelt in Pelt.tabbies:
                wm_weight = [20, 20, 20, 10, 10, 10, 10, 10]
            elif chosen_pelt in Pelt.spotted:
                wm_weight = [30, 20, 10, 10, 10, 10, 30, 10]
            elif chosen_pelt in Pelt.plain:
                wm_weight = [10, 15, 10, 10, 20, 20, 10, 30]
            elif chosen_pelt in Pelt.exotic:
                wm_weight = [30, 10, 20, 15, 10, 10, 30, 10]
            else:
                wm_weight = [1, 1, 1, 1, 1, 1, 1, 1]
            
            # Gather weights depending on pelt group
            #'NONE', 'FULL', 'FADE', 'INVERTFADE', 'STRIPES', 'SPOTS', 'SMOKE'
            if chosen_pelt in Pelt.tabbies:
                weight = [5, 30, 30, 30, 30, 0, 0]
            elif chosen_pelt in Pelt.spotted:
                weight = [5, 30, 30, 30, 0, 30, 0]
            elif chosen_pelt is 'Smoke':
                weight = [0, 30, 20, 20, 0, 0, 30]
            elif chosen_pelt in Pelt.plain:
                weight = [30, 30, 20, 20, 0, 0, 10]
            elif chosen_pelt in Pelt.exotic:
                weight = [10, 30, 30, 30, 0, 30, 0]
            else:
                weight = [1, 1, 1, 1, 1, 1, 1]
            
        # Pick
        chosen_wing_marks = choice(
        random.choices(Pelt.bird_wing_marks, weights=wm_weight, k=1)
        )

        chosen_mane_marks = choice(
        random.choices(Pelt.mane_marks_list, weights=weight, k=1)
        )

        mane_sel = random.randint(1, 100)
        if mane_sel < 85:
            chosen_mane = True
        else:
            chosen_mane = False

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT COLOUR
        # ------------------------------------------------------------------------------------------------------------#

        chosen_pelt_color = choice(random.choices(Pelt.colour_categories, k=1)[0])

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT LENGTH
        # ------------------------------------------------------------------------------------------------------------#

        chosen_pelt_length = random.choice(Pelt.pelt_length)

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT WHITE
        # ------------------------------------------------------------------------------------------------------------#

        chosen_white = random.randint(1, 100) <= 40

        # Adjustments to pelt chosen based on if the pelt has white in it or not.
        if chosen_pelt in ["TwoColour", "SingleColour"]:
            if chosen_white:
                chosen_pelt = "TwoColour"
            else:
                chosen_pelt = "SingleColour"
        elif chosen_pelt == "Calico":
            if not chosen_white:
                chosen_pelt = "Tortie"

        self.name = chosen_pelt
        self.wing_marks = chosen_wing_marks
        self.mane_marks = chosen_mane_marks
        self.mane = chosen_mane
        self.colour = chosen_pelt_color
        self.length = chosen_pelt_length
        self.tortiebase = (
            chosen_tortie_base  # This will be none if the cat isn't a tortie.
        )
        return chosen_white

    def init_pattern_color(self, parents, gender) -> bool:
        """Inits self.name, self.colour, self.length,
        self.tortiebase and determines if the cat
        will have white patche or not.
        Return TRUE is the cat should have white patches,
        false is not."""

        if parents:
            # If the cat has parents, use inheritance to decide pelt.
            chosen_white = self.pattern_color_inheritance(parents, gender)
        else:
            chosen_white = self.randomize_pattern_color(gender)

        return chosen_white

    def init_sprite(self, species):
        self.cat_sprites = {
            'newborn': 20,
            'kitten': random.randint(0, 2),
            'adolescent': random.randint(3, 5),
            'senior': random.randint(12, 14),
            'sick_kitten': 21,
            'sick_young': 19,
            'sick_adult': 18
        }
        self.reverse = bool(random.getrandbits(1))
        # skin chances
        self.skin = choice(Pelt.skin_sprites)

        if self.length != "long":
            self.cat_sprites["adult"] = random.randint(6, 8)
            self.cat_sprites["para_adult"] = 16
        else:
            self.cat_sprites["adult"] = random.randint(9, 11)
            self.cat_sprites["para_adult"] = 15
        self.cat_sprites["young adult"] = self.cat_sprites["adult"]
        self.cat_sprites["senior adult"] = self.cat_sprites["adult"]

    def init_scars(self, age):
        if age == "newborn":
            return

        if age in ["kitten", "adolescent"]:
            scar_choice = random.randint(0, 50)  # 2%
        elif age in ["young adult", "adult"]:
            scar_choice = random.randint(0, 20)  # 5%
        else:
            scar_choice = random.randint(0, 15)  # 6.67%

        if scar_choice == 1:
            self.scars.append(choice([choice(Pelt.scars1), choice(Pelt.scars3)]))

        if "NOTAIL" in self.scars and "HALFTAIL" in self.scars:
            self.scars.remove("HALFTAIL")

    def init_accessories(self, age):
        if age == "newborn":
            self.accessory = []
            return

        acc_display_choice = random.randint(0, 80)
        if age in ["kitten", "adolescent"]:
            acc_display_choice = random.randint(0, 180)
        elif age in ["young adult", "adult"]:
            acc_display_choice = random.randint(0, 100)

        if acc_display_choice == 1:
            self.accessory = [choice(
                [choice(Pelt.plant_accessories), choice(Pelt.wild_accessories)]
            )]
        else:
            self.accessory = []

    def init_pattern(self):
        if self.name in Pelt.torties:
            if not self.tortiebase:
                self.tortiebase = choice(Pelt.tortiebases)
            if not self.pattern:
                self.pattern = choice(Pelt.tortiepatterns)

            wildcard_chance = game.config["cat_generation"]["wildcard_tortie"]
            if self.colour:
                # The "not wildcard_chance" allows users to set wildcard_tortie to 0
                # and always get wildcard torties.
                if not wildcard_chance or random.getrandbits(wildcard_chance) == 1:
                    # This is the "wildcard" chance, where you can get funky combinations.
                    # people are fans of the print message, so I'm putting it back
                    print("Wildcard tortie!")

                    # Allow any pattern:
                    self.tortiepattern = choice(Pelt.tortiebases)

                    # Allow any colors that aren't the base color.
                    possible_colors = Pelt.pelt_colours.copy()
                    possible_colors.remove(self.colour)
                    self.tortiecolour = choice(possible_colors)

                else:
                    # Normal generation
                    if self.tortiebase in ["singlestripe", "smoke", "single"]:
                        self.tortiepattern = choice(
                            [
                                "tabby",
                                "mackerel",
                                "classic",
                                "single",
                                "smoke",
                                "agouti",
                                "ticked",
                            ]
                        )
                    else:
                        self.tortiepattern = random.choices(
                            [self.tortiebase, "single"], weights=[97, 3], k=1
                        )[0]

                    if self.colour == "WHITE":
                        possible_colors = Pelt.white_colours.copy()
                        possible_colors.remove("WHITE")
                        self.colour = choice(possible_colors)

                    # Ginger is often duplicated to increase its chances
                    if (self.colour in Pelt.black_colours) or (
                        self.colour in Pelt.white_colours
                    ):
                        self.tortiecolour = choice(
                            (Pelt.ginger_colours * 2) + Pelt.brown_colours
                        )
                    elif self.colour in Pelt.ginger_colours:
                        self.tortiecolour = choice(
                            Pelt.brown_colours + Pelt.black_colours * 2
                        )
                    elif self.colour in Pelt.brown_colours:
                        possible_colors = Pelt.brown_colours.copy()
                        possible_colors.remove(self.colour)
                        possible_colors.extend(
                            Pelt.black_colours + (Pelt.ginger_colours * 2)
                        )
                        self.tortiecolour = choice(possible_colors)
                    else:
                        self.tortiecolour = "GOLDEN"

            else:
                self.tortiecolour = "GOLDEN"
        else:
            self.tortiebase = None
            self.tortiepattern = None
            self.tortiecolour = None
            self.pattern = None

    def white_patches_inheritance(self, parents: tuple):
        par_whitepatches = set()
        par_points = []
        for p in parents:
            if p:
                if p.pelt.white_patches:
                    par_whitepatches.add(p.pelt.white_patches)
                if p.pelt.points:
                    par_points.append(p.pelt.points)

        if not parents:
            print("Error - no parents. Randomizing white patches.")
            self.randomize_white_patches()
            return

        # Direct inheritance. Will only work if at least one parent has white patches, otherwise continue on.
        if par_whitepatches and not random.randint(
            0, game.config["cat_generation"]["direct_inheritance"]
        ):
            # This ensures Torties and Calicos won't get direct inheritance of incorrect white patch types
            _temp = par_whitepatches.copy()
            if self.name == "Tortie":
                for p in _temp.copy():
                    if p in Pelt.high_white + Pelt.mostly_white + ["FULLWHITE"]:
                        _temp.remove(p)
            elif self.name == "Calico":
                for p in _temp.copy():
                    if p in Pelt.little_white + Pelt.mid_white:
                        _temp.remove(p)

            # Only proceed with the direct inheritance if there are white patches that match the pelt.
            if _temp:
                self.white_patches = choice(list(_temp))

                # Direct inheritance also effect the point marking.
                if par_points and self.name != "Tortie":
                    self.points = choice(par_points)
                else:
                    self.points = None

                return

        # dealing with points
        if par_points:
            chance = 10 - len(par_points)
        else:
            chance = 40
        # Chance of point is 1 / chance.
        if self.name != "Tortie" and not int(random.random() * chance):
            self.points = choice(Pelt.point_markings)
        else:
            self.points = None

        white_list = [
            Pelt.little_white,
            Pelt.mid_white,
            Pelt.high_white,
            Pelt.mostly_white,
            ["FULLWHITE"],
        ]

        weights = [0, 0, 0, 0, 0]  # Same order as white_list
        for p_ in par_whitepatches:
            if p_ in Pelt.little_white:
                add_weights = (40, 20, 15, 5, 0)
            elif p_ in Pelt.mid_white:
                add_weights = (10, 40, 15, 10, 0)
            elif p_ in Pelt.high_white:
                add_weights = (15, 20, 40, 10, 1)
            elif p_ in Pelt.mostly_white:
                add_weights = (5, 15, 20, 40, 5)
            elif p_ == "FULLWHITE":
                add_weights = (0, 5, 15, 40, 10)
            else:
                add_weights = (0, 0, 0, 0, 0)

            for x in range(0, len(weights)):
                weights[x] += add_weights[x]

        # If all the weights are still 0, that means none of the parents have white patches.
        if not any(weights):
            if not all(
                parents
            ):  # If any of the parents are None (unknown), use the following distribution:
                weights = [20, 10, 10, 5, 0]
            else:
                # Otherwise, all parents are known and don't have any white patches. Focus distribution on little_white.
                weights = [50, 5, 0, 0, 0]

        # Adjust weights for torties, since they can't have anything greater than mid_white:
        if self.name == "Tortie":
            weights = weights[:2] + [0, 0, 0]
            # Another check to make sure not all the values are zero. This should never happen, but better
            # safe than sorry.
            if not any(weights):
                weights = [2, 1, 0, 0, 0]
        elif self.name == "Calico":
            weights = [0, 0, 0] + weights[3:]
            # Another check to make sure not all the values are zero. This should never happen, but better
            # safe than sorry.
            if not any(weights):
                weights = [2, 1, 0, 0, 0]

        chosen_white_patches = choice(
            random.choices(white_list, weights=weights, k=1)[0]
        )

        self.white_patches = chosen_white_patches
        if self.points and self.white_patches in [
            Pelt.high_white,
            Pelt.mostly_white,
            "FULLWHITE",
        ]:
            self.points = None

    def randomize_white_patches(self):
        # Points determination. Tortie can't be pointed
        if self.name != "Tortie" and not random.getrandbits(
            game.config["cat_generation"]["random_point_chance"]
        ):
            # Cat has colorpoint!
            self.points = choice(Pelt.point_markings)
        else:
            self.points = None

        # Adjust weights for torties, since they can't have anything greater than mid_white:
        if self.name == "Tortie":
            weights = (2, 1, 0, 0, 0)
        elif self.name == "Calico":
            weights = (0, 0, 20, 15, 1)
        else:
            weights = (10, 10, 10, 10, 1)

        white_list = [
            Pelt.little_white,
            Pelt.mid_white,
            Pelt.high_white,
            Pelt.mostly_white,
            ["FULLWHITE"],
        ]
        chosen_white_patches = choice(
            random.choices(white_list, weights=weights, k=1)[0]
        )

        self.white_patches = chosen_white_patches
        if self.points and self.white_patches in [
            Pelt.high_white,
            Pelt.mostly_white,
            "FULLWHITE",
        ]:
            self.points = None

    def init_white_patches(self, pelt_white, parents: tuple):
        # Vit can roll for anyone, not just cats who rolled to have white in their pelt.
        par_vit = []
        for p in parents:
            if p:
                if p.pelt.vitiligo:
                    par_vit.append(p.pelt.vitiligo)

        vit_chance = max(game.config["cat_generation"]["vit_chance"] - len(par_vit), 0)
        if not random.getrandbits(vit_chance):
            self.vitiligo = choice(Pelt.vit)

        # If the cat was rolled previously to have white patches, then determine the patch they will have
        # these functions also handle points.
        if pelt_white:
            if parents:
                self.white_patches_inheritance(parents)
            else:
                self.randomize_white_patches()
        else:
            self.white_patches = None
            self.points = None

    def init_wing_patches(self):
        """For initialising white patches n crap because I don't want to write this multiple times"""
        white_choices = []

        # find white amount
        if self.white_patches in Pelt.little_white:
            patch_amount = "little"
        elif self.white_patches in Pelt.mid_white:
            patch_amount = "mid"
        elif self.white_patches in Pelt.high_white:
            patch_amount = "high"
        elif self.white_patches in Pelt.mostly_white:
            patch_amount = "mostly"
        else:
            patch_amount = "none"

        # check if it exists
        if self.white_patches in Pelt.wing_white_list:

            # check for special
            if self.white_patches not in Pelt.special_wing_white:
                for a, i in enumerate(Pelt.wing_white_sel[f'{patch_amount}']):
                    white_choices.append(Pelt.wing_white_sel[f'{patch_amount}_white'])
                    # 50% chance for a random diff white patch or the same one
                    white_choices.append([self.white_patches] * len(i))
            else:
                white_choices.append([self.white_patches])
        else:
            # catch if there is no white patch
            if patch_amount == "none":
                return
            else:
                for a, i in enumerate(Pelt.wing_white_sel[f'{patch_amount}']):
                    white_choices.append(Pelt.wing_white_sel[f'{patch_amount}_white'])
                    if patch_amount == "little":
                        # 75% chance for no white patch on wings
                        white_choices.append(['NONE'] * len(i) * 2)

        chosen_white_patches = choice(
            random.choices(white_choices, k=1)[0]
        )
        
        self.wing_white_patches = chosen_white_patches


    def init_tint(self):
        """Sets tint for pelt and white patches"""

        # PELT TINT
        # Basic tints as possible for all colors.
        base_tints = sprites.cat_tints["possible_tints"]["basic"]
        if self.colour in sprites.cat_tints["colour_groups"]:
            color_group = sprites.cat_tints["colour_groups"].get(self.colour, "warm")
            color_tints = sprites.cat_tints["possible_tints"][color_group]
        else:
            color_tints = []

        if base_tints or color_tints:
            self.tint = choice(base_tints + color_tints)
        else:
            self.tint = "none"

        # WHITE PATCHES TINT
        if self.white_patches or self.points:
            # Now for white patches
            base_tints = sprites.white_patches_tints["possible_tints"]["basic"]
            if self.colour in sprites.cat_tints["colour_groups"]:
                color_group = sprites.white_patches_tints["colour_groups"].get(
                    self.colour, "white"
                )
                color_tints = sprites.white_patches_tints["possible_tints"][color_group]
            else:
                color_tints = []

            if base_tints or color_tints:
                self.white_patches_tint = choice(base_tints + color_tints)
            else:
                self.white_patches_tint = "none"
        else:
            self.white_patches_tint = "none"

    @property
    def white(self):
        return self.white_patches or self.points

    @white.setter
    def white(self, val):
        print("Can't set pelt.white")
        return

    def describe_eyes(self):
        return (
            adjust_list_text(
                [
                    i18n.t(f"cat.eyes.{self.eye_colour}"),
                    i18n.t(f"cat.eyes.{self.eye_colour2}"),
                ]
            )
            if self.eye_colour2
            else i18n.t(f"cat.eyes.{self.eye_colour}")
        )

    @staticmethod
    def describe_appearance(cat, short=False):
        """Return a description of a cat

        :param Cat cat: The cat to describe
        :param bool short: Whether to return a heavily-truncated description, default False
        :return str: The cat's description
        """

        config = get_lang_config()["description"]
        ruleset = config["ruleset"]
        output = []
        pelt_pattern, pelt_color = _describe_pattern(cat, short)
        for rule, args in ruleset.items():
            temp = unpack_appearance_ruleset(cat, rule, short, pelt_pattern, pelt_color)

            if args == "" or temp == "":
                output.append(temp)
                continue

            # handle args
            argpool = {
                arg: unpack_appearance_ruleset(
                    cat, arg, short, pelt_pattern, pelt_color
                )
                for arg in args
            }
            argpool["key"] = temp
            argpool["count"] = 1 if short else 2
            output.append(i18n.t(**argpool))

        # don't forget the count argument!
        groups = []
        for grouping in config["groups"]:
            temp = ""
            items = [
                i18n.t(output[i], count=1 if short else 2)
                for i in grouping["values"]
                if output[i] != ""
            ]
            if len(items) == 0:
                continue
            if "pre_value" in grouping:
                temp = grouping["pre_value"]

            if grouping["format"] == "list":
                temp += adjust_list_text(items)
            else:
                temp += grouping["format"].join(items)

            if "post_value" in grouping:
                temp += grouping["post_value"]
            groups.append(temp)

        return "".join(groups)

    def get_sprites_name(self):
        return Pelt.sprites_names[self.name]


def _describe_pattern(cat, short=False):
    color_name = [f"cat.pelts.{str(cat.pelt.colour)}"]
    pelt_name = f"cat.pelts.{cat.pelt.name.lower()}{'' if short else '_long'}"
    if cat.pelt.name in Pelt.torties:
        pelt_name, color_name = _describe_torties(cat, color_name, short)

    color_name = [i18n.t(piece, count=1) for piece in color_name]
    color_name = "".join(color_name)

    if cat.pelt.white_patches:
        if cat.pelt.white_patches == "FULLWHITE":
            # If the cat is fullwhite, discard all other information. They are just white
            color_name = i18n.t("cat.pelts.FULLWHITE")
            pelt_name = ""
        elif cat.pelt.name != "Calico":
            white = i18n.t("cat.pelts.FULLWHITE")
            if i18n.t("cat.pelts.WHITE", count=1) in color_name:
                color_name = white
            elif cat.pelt.white_patches in Pelt.mostly_white:
                color_name = adjust_list_text([white, color_name])
            else:
                color_name = adjust_list_text([color_name, white])

    if cat.pelt.points:
        color_name = i18n.t("cat.pelts.point", color=color_name)
        if "ginger point" in color_name:
            color_name.replace("ginger point", "flame point")
            # look, I'm leaving this as a quirk of the english language, if it's a problem elsewhere lmk

    return pelt_name, color_name


def _describe_torties(cat, color_name, short=False) -> [str, str]:
    # Calicos and Torties need their own desciptions
    if short:
        # If using short, don't describe the colors of calicos and torties.
        # Just call them calico, tortie, or mottled
        if (
            cat.pelt.colour
            in Pelt.black_colours + Pelt.brown_colours + Pelt.white_colours
            and cat.pelt.tortiecolour
            in Pelt.black_colours + Pelt.brown_colours + Pelt.white_colours
        ):
            return "cat.pelts.mottled", ""
        else:
            return f"cat.pelts.{cat.pelt.name.lower()}", ""

    base = cat.pelt.tortiebase.lower()

    patches_color = f"cat.pelts.{cat.pelt.tortiecolour}"
    color_name.append("/")
    color_name.append(patches_color)

    if (
        cat.pelt.colour in Pelt.black_colours + Pelt.brown_colours + Pelt.white_colours
        and cat.pelt.tortiecolour
        in Pelt.black_colours + Pelt.brown_colours + Pelt.white_colours
    ):
        return "cat.pelts.mottled_long", color_name
    else:
        if base in [tabby.lower() for tabby in Pelt.tabbies] + [
            "bengal",
            "rosette",
            "speckled",
        ]:
            base = f"cat.pelts.{cat.pelt.tortiebase.capitalize()}_long"  # the extra space is intentional
        else:
            base = ""
        return base, color_name


_scar_details = [
    "NOTAIL",
    "HALFTAIL",
    "NOPAW",
    "NOLEFTEAR",
    "NORIGHTEAR",
    "NOEAR",
]


def unpack_appearance_ruleset(cat, rule, short, pelt, color):
    if rule == "scarred":
        if not short and len(cat.pelt.scars) >= 3:
            return "cat.pelts.scarred"
    elif rule == "fur_length":
        if not short and cat.pelt.length == "long":
            return "cat.pelts.long_furred"
    elif rule == "pattern":
        return pelt
    elif rule == "color":
        return color
    elif rule == "cat":
        if cat.genderalign in ["female", "trans female"]:
            return "general.she-cat"
        elif cat.genderalign in ["male", "trans male"]:
            return "general.tom"
        else:
            return "general.cat"
    elif rule == "vitiligo":
        if not short and cat.pelt.vitiligo:
            return "cat.pelts.vitiligo"
    elif rule == "amputation":
        if not short:
            scarlist = []
            for scar in cat.pelt.scars:
                if scar in _scar_details:
                    scarlist.append(i18n.t(f"cat.pelts.{scar}"))
            return (
                adjust_list_text(list(set(scarlist))) if len(scarlist) > 0 else ""
            )  # note: this doesn't preserve order!
    else:
        raise Exception(f"Unmatched ruleset item {rule} in describe_appearance!")
    return ""
