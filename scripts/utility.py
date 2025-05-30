# pylint: disable=line-too-long
"""

TODO: Docs


"""  # pylint: enable=line-too-long

import logging
import os
import re
from itertools import combinations
from math import floor
from random import choice, choices, randint, random, sample, randrange, getrandbits
from sys import exit as sys_exit
from typing import List, Tuple, TYPE_CHECKING, Type, Union

import i18n
import pygame
import ujson
from pygame_gui.core import ObjectID

from scripts.game_structure.localization import (
    load_lang_resource,
    determine_plural_pronouns,
    get_lang_config,
)

logger = logging.getLogger(__name__)
from scripts.game_structure import image_cache, localization
from scripts.cat.enums import CatAgeEnum
from scripts.cat.history import History
from scripts.cat.names import names
from scripts.cat.sprites import sprites
from scripts.game_structure.game_essentials import game
import scripts.game_structure.screen_settings  # must be done like this to get updates when we change screen size etc

if TYPE_CHECKING:
    from scripts.cat.cats import Cat


# ---------------------------------------------------------------------------- #
#                               Getting Cats                                   #
# ---------------------------------------------------------------------------- #


def get_alive_clan_queens(living_cats):
    living_kits = [
        cat
        for cat in living_cats
        if not (cat.dead or cat.outside) and cat.status in ["kitten", "newborn"]
    ]

    queen_dict = {}
    for cat in living_kits.copy():
        parents = cat.get_parents()
        # Fetch parent object, only alive and not outside.
        parents = [
            cat.fetch_cat(i)
            for i in parents
            if cat.fetch_cat(i)
               and not (cat.fetch_cat(i).dead or cat.fetch_cat(i).outside)
        ]
        if not parents:
            continue

        if (
                len(parents) == 1
                or len(parents) > 2
                or all(i.gender == "male" for i in parents)
                or parents[0].gender == "female"
        ):
            if parents[0].ID in queen_dict:
                queen_dict[parents[0].ID].append(cat)
                living_kits.remove(cat)
            else:
                queen_dict[parents[0].ID] = [cat]
                living_kits.remove(cat)
        elif len(parents) == 2:
            if parents[1].ID in queen_dict:
                queen_dict[parents[1].ID].append(cat)
                living_kits.remove(cat)
            else:
                queen_dict[parents[1].ID] = [cat]
                living_kits.remove(cat)
    return queen_dict, living_kits


def get_alive_status_cats(
        Cat: Union["Cat", Type["Cat"]],
        get_status: list,
        working: bool = False,
        sort: bool = False,
) -> list:
    """
    returns a list of cat objects for all living cats of get_status in Clan
    :param Cat Cat: Cat class
    :param list get_status: list of statuses searching for
    :param bool working: default False, set to True if you would like the list to only include working cats
    :param bool sort: default False, set to True if you would like list sorted by descending moon age
    """

    alive_cats = [
        i
        for i in Cat.all_cats.values()
        if i.status in get_status and not i.dead and not i.outside
    ]

    if working:
        alive_cats = [i for i in alive_cats if not i.not_working()]

    if sort:
        alive_cats = sorted(alive_cats, key=lambda cat: cat.moons, reverse=True)

    return alive_cats


def get_living_cat_count(Cat):
    """
    Returns the int of all living cats, both in and out of the Clan
    :param Cat: Cat class
    """
    count = 0
    for the_cat in Cat.all_cats.values():
        if the_cat.dead:
            continue
        count += 1
    return count


def get_living_clan_cat_count(Cat):
    """
    Returns the int of all living cats within the Clan
    :param Cat: Cat class
    """
    count = 0
    for the_cat in Cat.all_cats.values():
        if the_cat.dead or the_cat.exiled or the_cat.outside:
            continue
        count += 1
    return count


def get_cats_same_age(Cat, cat, age_range=10):
    """
    Look for all cats in the Clan and returns a list of cats which are in the same age range as the given cat.
    :param Cat: Cat class
    :param cat: the given cat
    :param int age_range: The allowed age difference between the two cats, default 10
    """
    cats = []
    for inter_cat in Cat.all_cats.values():
        if inter_cat.dead or inter_cat.outside or inter_cat.exiled:
            continue
        if inter_cat.ID == cat.ID:
            continue

        if inter_cat.ID not in cat.relationships:
            cat.create_one_relationship(inter_cat)
            if cat.ID not in inter_cat.relationships:
                inter_cat.create_one_relationship(cat)
            continue

        if (
                inter_cat.moons <= cat.moons + age_range
                and inter_cat.moons <= cat.moons - age_range
        ):
            cats.append(inter_cat)

    return cats


def get_free_possible_mates(cat):
    """Returns a list of available cats, which are possible mates for the given cat."""
    cats = []
    for inter_cat in cat.all_cats.values():
        if inter_cat.dead or inter_cat.outside or inter_cat.exiled:
            continue
        if inter_cat.ID == cat.ID:
            continue

        if inter_cat.ID not in cat.relationships:
            cat.create_one_relationship(inter_cat)
            if cat.ID not in inter_cat.relationships:
                inter_cat.create_one_relationship(cat)
            continue

        if inter_cat.is_potential_mate(cat, for_love_interest=True):
            cats.append(inter_cat)
    return cats


def get_random_moon_cat(
        Cat, main_cat, parent_child_modifier=True, mentor_app_modifier=True
):
    """
    returns a random cat for use in moon events
    :param Cat: Cat class
    :param main_cat: cat object of main cat in event
    :param parent_child_modifier: increase the chance of the random cat being a
    parent of the main cat. Default True
    :param mentor_app_modifier: increase the chance of the random cat being a mentor or
    app of the main cat. Default True
    """
    random_cat = None

    # grab list of possible random cats
    possible_r_c = list(
        filter(
            lambda c: not c.dead
                      and not c.exiled
                      and not c.outside
                      and (c.ID != main_cat.ID),
            Cat.all_cats.values(),
        )
    )

    if possible_r_c:
        random_cat = choice(possible_r_c)
        if parent_child_modifier and not int(random() * 3):
            possible_parents = []
            if main_cat.parent1:
                if Cat.fetch_cat(main_cat.parent1) in possible_r_c:
                    possible_parents.append(main_cat.parent1)
            if main_cat.parent2:
                if Cat.fetch_cat(main_cat.parent2) in possible_r_c:
                    possible_parents.append(main_cat.parent2)
            if main_cat.adoptive_parents:
                for parent in main_cat.adoptive_parents:
                    if Cat.fetch_cat(parent) in possible_r_c:
                        possible_parents.append(parent)
            if possible_parents:
                random_cat = Cat.fetch_cat(choice(possible_parents))
        if mentor_app_modifier:
            if (
                    main_cat.status
                    in ["apprentice", "mediator apprentice", "medicine cat apprentice"]
                    and main_cat.mentor
                    and not int(random() * 3)
            ):
                random_cat = Cat.fetch_cat(main_cat.mentor)
            elif main_cat.apprentice and not int(random() * 3):
                random_cat = Cat.fetch_cat(choice(main_cat.apprentice))

    if isinstance(random_cat, str):
        print(f"WARNING: random cat was {random_cat} instead of cat object")
        random_cat = Cat.fetch_cat(random_cat)
    return random_cat


def get_warring_clan():
    """
    returns enemy clan if a war is currently ongoing
    """
    enemy_clan = None
    if game.clan.war.get("at_war", False):
        for other_clan in game.clan.all_clans:
            if other_clan.name == game.clan.war["enemy"]:
                enemy_clan = other_clan

    return enemy_clan


# ---------------------------------------------------------------------------- #
#                          Handling Outside Factors                            #
# ---------------------------------------------------------------------------- #


def get_current_season():
    """
    function to handle the math for finding the Clan's current season
    :return: the Clan's current season
    """

    if game.config["lock_season"]:
        game.clan.current_season = game.clan.starting_season
        return game.clan.starting_season

    modifiers = {"Newleaf": 0, "Greenleaf": 3, "Leaf-fall": 6, "Leaf-bare": 9}
    index = game.clan.age % 12 + modifiers[game.clan.starting_season]

    if index > 11:
        index = index - 12

    game.clan.current_season = game.clan.seasons[index]

    return game.clan.current_season


def change_clan_reputation(difference):
    """
    will change the Clan's reputation with outsider cats according to the difference parameter.
    """
    game.clan.reputation += difference
    if game.clan.reputation < 0:
        game.clan.reputation = 0 # clamp to 0
    elif game.clan.reputation > 100:
        game.clan.reputation = 100 # clamp to 100

def change_clan_relations(other_clan, difference):
    """
    will change the Clan's relation with other clans according to the difference parameter.
    """
    # grab the clan that has been indicated
    other_clan = other_clan
    # grab the relation value for that clan
    y = game.clan.all_clans.index(other_clan)
    clan_relations = int(game.clan.all_clans[y].relations)
    # change the value
    clan_relations += difference
    # making sure it doesn't exceed the bounds
    if clan_relations > 30:
        clan_relations = 30
    elif clan_relations < 0:
        clan_relations = 0
    # setting it in the Clan save
    game.clan.all_clans[y].relations = clan_relations


def create_new_cat_block(
        Cat, Relationship, event, in_event_cats: dict, i: int, attribute_list: List[str]
) -> list:
    """
    Creates a single new_cat block and then generates and returns the cats within the block
    :param Cat Cat: always pass Cat class
    :param Relationship Relationship: always pass Relationship class
    :param event: always pass the event class
    :param dict in_event_cats: dict containing involved cats' abbreviations as keys and cat objects as values
    :param int i: index of the cat block
    :param list[str] attribute_list: attribute list contained within the block
    """

    thought = i18n.t("hardcoded.thought_new_cat")
    new_cats = None

    # gather parents
    parent1 = None
    parent2 = None
    adoptive_parents = []
    for tag in attribute_list:
        parent_match = re.match(r"parent:([,0-9]+)", tag)
        adoptive_match = re.match(r"adoptive:(.+)", tag)
        if not parent_match and not adoptive_match:
            continue

        parent_indexes = parent_match.group(1).split(",") if parent_match else []
        adoptive_indexes = adoptive_match.group(1).split(",") if adoptive_match else []
        if not parent_indexes and not adoptive_indexes:
            continue

        parent_indexes = [int(index) for index in parent_indexes]
        for index in parent_indexes:
            if index >= i:
                continue

            if parent1 is None:
                parent1 = event.new_cats[index][0]
            else:
                parent2 = event.new_cats[index][0]

        adoptive_indexes = [
            int(index) if index.isdigit() else index for index in adoptive_indexes
        ]
        for index in adoptive_indexes:
            if in_event_cats[index].ID not in adoptive_parents:
                adoptive_parents.append(in_event_cats[index].ID)
                adoptive_parents.extend(in_event_cats[index].mate)

    # gather mates
    give_mates = []
    for tag in attribute_list:
        match = re.match(r"mate:([_,0-9a-zA-Z]+)", tag)
        if not match:
            continue

        mate_indexes = match.group(1).split(",")

        # TODO: make this less ugly
        for index in mate_indexes:
            if index in in_event_cats:
                if in_event_cats[index] in [
                    "apprentice",
                    "medicine cat apprentice",
                    "mediator apprentice",
                ]:
                    print("Can't give apprentices mates")
                    continue

                give_mates.append(in_event_cats[index])

            try:
                index = int(index)
            except ValueError:
                print(f"mate-index not correct: {index}")
                continue

            if index >= i:
                continue

            give_mates.extend(event.new_cats[index])

    # determine gender
    if "male" in attribute_list:
        gender = "male"
    elif "female" in attribute_list:
        gender = "female"
    elif (
            "can_birth" in attribute_list and not game.clan.clan_settings["same sex birth"]
    ):
        gender = "female"
    else:
        gender = None

    # will the cat get a new name?
    if "new_name" in attribute_list:
        new_name = True
    elif "old_name" in attribute_list:
        new_name = False
    else:
        new_name = bool(getrandbits(1))

    # STATUS - must be handled before backstories
    status = None
    for _tag in attribute_list:
        match = re.match(r"status:(.+)", _tag)
        if not match:
            continue

        if match.group(1) in [
            "newborn",
            "kitten",
            "elder",
            "apprentice",
            "warrior",
            "mediator apprentice",
            "mediator",
            "medicine cat apprentice",
            "medicine cat",
        ]:
            status = match.group(1)
            break

    # SET AGE
    age = None
    for _tag in attribute_list:
        match = re.match(r"age:(.+)", _tag)
        if not match:
            continue

        if match.group(1) in Cat.age_moons:
            min_age, max_age = Cat.age_moons[CatAgeEnum(match.group(1))]
            age = randint(min_age, max_age)
            break

        # Set same as first mate
        if match.group(1) == "mate" and give_mates:
            min_age, max_age = Cat.age_moons[give_mates[0].age]
            age = randint(min_age, max_age)
            break

        if match.group(1) == "has_kits":
            age = randint(19, 120)
            break

    if status and not age:
        if status in ["apprentice", "mediator apprentice", "medicine cat apprentice"]:
            age = randint(
                Cat.age_moons[CatAgeEnum.ADOLESCENT][0],
                Cat.age_moons[CatAgeEnum.ADOLESCENT][1],
            )
        elif status in ["warrior", "mediator", "medicine cat"]:
            age = randint(
                Cat.age_moons["young adult"][0], Cat.age_moons["senior adult"][1]
            )
        elif status == "elder":
            age = randint(Cat.age_moons["senior"][0], Cat.age_moons["senior"][1])

    if "kittypet" in attribute_list:
        cat_type = "kittypet"
    elif "rogue" in attribute_list:
        cat_type = "rogue"
    elif "loner" in attribute_list:
        cat_type = "loner"
    elif "clancat" in attribute_list:
        cat_type = "former Clancat"
    else:
        cat_type = choice(["kittypet", "loner", "former Clancat"])

    # LITTER
    litter = False
    if "litter" in attribute_list:
        litter = True
        if status not in ["kitten", "newborn"]:
            status = "kitten"

    # CHOOSE DEFAULT BACKSTORY BASED ON CAT TYPE, STATUS
    if status in ("kitten", "newborn"):
        chosen_backstory = choice(
            BACKSTORIES["backstory_categories"]["abandoned_backstories"]
        )
    elif status == "medicine cat" and cat_type == "former Clancat":
        chosen_backstory = choice(["medicine_cat", "disgraced1"])
    elif status == "medicine cat":
        chosen_backstory = choice(["wandering_healer1", "wandering_healer2"])
    else:
        if cat_type == "former Clancat":
            x = "former_clancat"
        else:
            x = cat_type
        chosen_backstory = choice(
            BACKSTORIES["backstory_categories"].get(f"{x}_backstories", ["outsider1"])
        )

    # OPTION TO OVERRIDE DEFAULT BACKSTORY
    bs_override = False
    stor = []
    for _tag in attribute_list:
        match = re.match(r"backstory:(.+)", _tag)
        if match:
            bs_list = [x for x in re.split(r", ?", match.group(1))]
            stor = []
            for story in bs_list:
                if story in set(
                        [
                            backstory
                            for backstory_block in BACKSTORIES[
                            "backstory_categories"
                        ].values()
                            for backstory in backstory_block
                        ]
                ):
                    stor.append(story)
                elif story in BACKSTORIES["backstory_categories"]:
                    stor.extend(BACKSTORIES["backstory_categories"][story])
            bs_override = True
            break
    if bs_override:
        chosen_backstory = choice(stor)

    # KITTEN THOUGHT
    if status in ["kitten", "newborn"]:
        thought = i18n.t("hardcoded.thought_new_kitten")

    # MEETING - DETERMINE IF THIS IS AN OUTSIDE CAT
    outside = False
    if "meeting" in attribute_list:
        outside = True
        status = cat_type
        new_name = False
        thought = i18n.t("hardcoded.thought_meeting")
        if age is not None and age <= 6 and not bs_override:
            chosen_backstory = "outsider1"

    # IS THE CAT DEAD?
    alive = True
    if "dead" in attribute_list:
        alive = False
        thought = i18n.t("hardcoded.thought_new_dead")

    # check if we can use an existing cat here
    chosen_cat = None
    if "exists" in attribute_list:
        existing_outsiders = [
            i for i in Cat.all_cats.values() if i.outside and not i.dead
        ]
        possible_outsiders = []
        for cat in existing_outsiders:
            if stor and cat.backstory not in stor:
                continue
            if cat_type != cat.status:
                continue
            if gender and gender != cat.gender:
                continue
            if age and age not in Cat.age_moons[cat.age]:
                continue
            possible_outsiders.append(cat)

        if possible_outsiders:
            chosen_cat = choice(possible_outsiders)
            game.clan.add_to_clan(chosen_cat)
            chosen_cat.status = status
            chosen_cat.outside = outside
            if not alive:
                chosen_cat.die()

            if new_name:
                name = f"{chosen_cat.name.prefix}"
                spaces = name.count(" ")
                if bool(getrandbits(1)) and spaces > 0:  # adding suffix to OG name
                    # make a list of the words within the name, then add the OG name back in the list
                    words = name.split(" ")
                    words.append(name)
                    new_prefix = choice(words)  # pick new prefix from that list
                    name = new_prefix
                    chosen_cat.name.prefix = name
                    chosen_cat.name.give_suffix(
                        pelt=chosen_cat.pelt,
                        biome=game.clan.biome,
                        tortiepattern=chosen_cat.pelt.tortiepattern,
                    )
                else:  # completely new name
                    chosen_cat.name.give_prefix(
                        eyes=chosen_cat.pelt.eye_colour,
                        colour=chosen_cat.pelt.colour,
                        biome=game.clan.biome,
                    )
                    chosen_cat.name.give_suffix(
                        pelt=chosen_cat.pelt.colour,
                        biome=game.clan.biome,
                        tortiepattern=chosen_cat.pelt.tortiepattern,
                    )

            new_cats = [chosen_cat]
    # Now we generate the new cat
    if not chosen_cat:
        new_cats = create_new_cat(
            Cat,
            new_name=new_name,
            loner=cat_type in ["loner", "rogue"],
            kittypet=cat_type == "kittypet",
            other_clan=cat_type == "former Clancat",
            kit=False if litter else status in ["kitten", "newborn"],
            # this is for singular kits, litters need this to be false
            litter=litter,
            backstory=chosen_backstory,
            status=status,
            age=age,
            gender=gender,
            thought=thought,
            alive=alive,
            outside=outside,
            parent1=parent1.ID if parent1 else None,
            parent2=parent2.ID if parent2 else None,
            adoptive_parents=adoptive_parents if adoptive_parents else None,
        )

        # NEXT
        # add relations to bio parents, if needed
        # add relations to cats generated within the same block, as they are littermates
        # add mates
        # THIS DOES NOT ADD RELATIONS TO CATS IN THE EVENT, those are added within the relationships block of the event

        for n_c in new_cats:
            # SET MATES
            for inter_cat in give_mates:
                if n_c == inter_cat or n_c.ID in inter_cat.mate:
                    continue

                # this is some duplicate work, since this triggers inheritance re-calcs
                # TODO: optimize
                n_c.set_mate(inter_cat)

            # LITTERMATES
            for inter_cat in new_cats:
                if n_c == inter_cat:
                    continue

                y = randrange(0, 20)
                start_relation = Relationship(n_c, inter_cat, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                n_c.relationships[inter_cat.ID] = start_relation

            # BIO PARENTS
            for par in (parent1, parent2):
                if not par:
                    continue

                y = randrange(0, 20)
                start_relation = Relationship(par, n_c, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                par.relationships[n_c.ID] = start_relation

                y = randrange(0, 20)
                start_relation = Relationship(n_c, par, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                n_c.relationships[par.ID] = start_relation

            # ADOPTIVE PARENTS
            for par in adoptive_parents:
                if not par:
                    continue

                par = Cat.fetch_cat(par)

                y = randrange(0, 20)
                start_relation = Relationship(par, n_c, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                par.relationships[n_c.ID] = start_relation

                y = randrange(0, 20)
                start_relation = Relationship(n_c, par, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                n_c.relationships[par.ID] = start_relation

            # UPDATE INHERITANCE
            n_c.create_inheritance_new_cat()

    return new_cats


def get_other_clan(clan_name):
    """
    returns the clan object of given clan name
    """
    for clan in game.clan.all_clans:
        if clan.name == clan_name:
            return clan


def create_new_cat(
        Cat: Union["Cat", Type["Cat"]],
        new_name: bool = False,
        loner: bool = False,
        kittypet: bool = False,
        kit: bool = False,
        litter: bool = False,
        other_clan: bool = None,
        backstory: bool = None,
        status: str = None,
        age: int = None,
        gender: str = None,
        thought: str = None,
        alive: bool = True,
        outside: bool = False,
        parent1: str = None,
        parent2: str = None,
        adoptive_parents: list = None,
) -> list:
    """
    This function creates new cats and then returns a list of those cats
    :param Cat Cat: pass the Cat class
    :params Relationship Relationship: pass the Relationship class
    :param bool new_name: set True if cat(s) is a loner/rogue receiving a new Clan name - default: False
    :param bool loner: set True if cat(s) is a loner or rogue - default: False
    :param bool kittypet: set True if cat(s) is a kittypet - default: False
    :param bool kit: set True if the cat is a lone kitten - default: False
    :param bool litter: set True if a litter of kittens needs to be generated - default: False
    :param bool other_clan: if new cat(s) are from a neighboring clan, set true
    :param bool backstory: a list of possible backstories.json for the new cat(s) - default: None
    :param str status: set as the rank you want the new cat to have - default: None (will cause a random status to be picked)
    :param int age: set the age of the new cat(s) - default: None (will be random or if kit/litter is true, will be kitten.
    :param str gender: set the gender (BIRTH SEX) of the cat - default: None (will be random)
    :param str thought: if you need to give a custom "welcome" thought, set it here
    :param bool alive: set this as False to generate the cat as already dead - default: True (alive)
    :param bool outside: set this as True to generate the cat as an outsider instead of as part of the Clan - default: False (Clan cat)
    :param str parent1: Cat ID to set as the biological parent1
    :param str parent2: Cat ID to set as the biological parent2
    :param list adoptive_parents: Cat IDs to set as adoptive parents
    """

    if thought is None:
        thought = i18n.t("hardcoded.thought_new_cat")

    # TODO: it would be nice to rewrite this to be less bool-centric
    accessory = None
    if isinstance(backstory, list):
        backstory = choice(backstory)

    if backstory in (
            BACKSTORIES["backstory_categories"]["former_clancat_backstories"]
            or BACKSTORIES["backstory_categories"]["otherclan_categories"]
    ):
        other_clan = True

    created_cats = []

    if not litter:
        number_of_cats = 1
    else:
        number_of_cats = choices([2, 3, 4, 5], [5, 4, 1, 1], k=1)[0]

    if not isinstance(age, int):
        if status == "newborn":
            age = 0
        elif litter or kit:
            age = randint(1, 5)
        elif status in ("apprentice", "medicine cat apprentice", "mediator apprentice"):
            age = randint(6, 11)
        elif status == "warrior":
            age = randint(23, 120)
        elif status == "medicine cat":
            age = randint(23, 140)
        elif status == "elder":
            age = randint(120, 130)
        else:
            age = randint(6, 120)

    # setting status
    if not status:
        if age == 0:
            status = "newborn"
        elif age < 6:
            status = "kitten"
        elif 6 <= age <= 11:
            status = "apprentice"
        elif age >= 12:
            status = "warrior"
        elif age >= 120:
            status = "elder"

    # cat creation and naming time
    for index in range(number_of_cats):
        # setting gender
        if not gender:
            _gender = choice(["female", "male"])
        else:
            _gender = gender

        # other Clan cats, apps, and kittens (kittens and apps get indoctrinated lmao no old names for them)
        if other_clan or kit or litter or age < 12 and not (loner or kittypet):
            new_cat = Cat(
                moons=age,
                status=status,
                gender=_gender,
                backstory=backstory,
                parent1=parent1,
                parent2=parent2,
                adoptive_parents=adoptive_parents if adoptive_parents else [],
            )
        else:
            # grab starting names and accs for loners/kittypets
            if kittypet:
                name = choice(names.names_dict["loner_names"])
                if bool(getrandbits(1)):
                    # TODO: refactor this entire function to remove this call amongst other things
                    from scripts.cat.pelts import Pelt

                    accessory = choice(Pelt.collars)
            elif loner and bool(
                    getrandbits(1)
            ):  # try to give name from full loner name list
                name = choice(names.names_dict["loner_names"])
            else:
                name = choice(
                    names.names_dict["normal_prefixes"]
                )  # otherwise give name from prefix list (more nature-y names)

            # now we make the cats
            if new_name:  # these cats get new names
                if bool(getrandbits(1)):  # adding suffix to OG name
                    spaces = name.count(" ")
                    if spaces > 0:
                        # make a list of the words within the name, then add the OG name back in the list
                        words = name.split(" ")
                        words.append(name)
                        new_prefix = choice(words)  # pick new prefix from that list
                        name = new_prefix
                    new_cat = Cat(
                        moons=age,
                        prefix=name,
                        status=status,
                        gender=_gender,
                        backstory=backstory,
                        parent1=parent1,
                        parent2=parent2,
                        adoptive_parents=adoptive_parents if adoptive_parents else [],
                    )
                else:  # completely new name
                    new_cat = Cat(
                        moons=age,
                        status=status,
                        gender=_gender,
                        backstory=backstory,
                        parent1=parent1,
                        parent2=parent2,
                        adoptive_parents=adoptive_parents if adoptive_parents else [],
                    )
            # these cats keep their old names
            else:
                new_cat = Cat(
                    moons=age,
                    prefix=name,
                    suffix="",
                    status=status,
                    gender=_gender,
                    backstory=backstory,
                    parent1=parent1,
                    parent2=parent2,
                    adoptive_parents=adoptive_parents if adoptive_parents else [],
                )

        # give em a collar if they got one
        if accessory:
            new_cat.pelt.accessory = [accessory]

        # give apprentice aged cat a mentor
        if new_cat.age == "adolescent":
            new_cat.update_mentor()

        # Remove disabling scars, if they generated.
        not_allowed = [
            "NOPAW",
            "NOTAIL",
            "HALFTAIL",
            "NOEAR",
            "BOTHBLIND",
            "RIGHTBLIND",
            "LEFTBLIND",
            "BRIGHTHEART",
            "NOLEFTEAR",
            "NORIGHTEAR",
            "MANLEG",
        ]
        for scar in new_cat.pelt.scars:
            if scar in not_allowed:
                new_cat.pelt.scars.remove(scar)

        # chance to give the new cat a permanent condition, higher chance for found kits and litters
        if kit or litter:
            chance = int(
                game.config["cat_generation"]["base_permanent_condition"] / 11.25
            )
        else:
            chance = game.config["cat_generation"]["base_permanent_condition"] + 10
        if not int(random() * chance):
            possible_conditions = []
            for condition in PERMANENT:
                if (kit or litter) and PERMANENT[condition]["congenital"] not in [
                    "always",
                    "sometimes",
                ]:
                    continue
                # next part ensures that a kit won't get a condition that takes too long to reveal
                age = new_cat.moons
                leeway = 5 - (PERMANENT[condition]["moons_until"] + 1)
                if age > leeway:
                    continue
                possible_conditions.append(condition)

            if possible_conditions:
                chosen_condition = choice(possible_conditions)
                born_with = False
                if PERMANENT[chosen_condition]["congenital"] in [
                    "always",
                    "sometimes",
                ]:
                    born_with = True

                    new_cat.get_permanent_condition(chosen_condition, born_with)
                    if (
                            new_cat.permanent_condition[chosen_condition]["moons_until"]
                            == 0
                    ):
                        new_cat.permanent_condition[chosen_condition][
                            "moons_until"
                        ] = -2

                # assign scars
                if chosen_condition in ["lost a leg", "born without a leg"]:
                    new_cat.pelt.scars.append("NOPAW")
                elif chosen_condition in ["lost their tail", "born without a tail"]:
                    new_cat.pelt.scars.append("NOTAIL")

        if outside:
            new_cat.outside = True
        if not alive:
            new_cat.die()

        # newbie thought
        new_cat.thought = thought

        # and they exist now
        created_cats.append(new_cat)
        game.clan.add_cat(new_cat)
        history = History()
        history.add_beginning(new_cat)

        # create relationships
        new_cat.create_relationships_new_cat()
        # Note - we always update inheritance after the cats are generated, to
        # allow us to add parents.
        # new_cat.create_inheritance_new_cat()

    return created_cats


# ---------------------------------------------------------------------------- #
#                             Cat Relationships                                #
# ---------------------------------------------------------------------------- #


def get_highest_romantic_relation(
        relationships, exclude_mate=False, potential_mate=False
):
    """Returns the relationship with the highest romantic value."""
    max_love_value = 0
    current_max_relationship = None
    for rel in relationships:
        if rel.romantic_love < 0:
            continue
        if exclude_mate and rel.cat_from.ID in rel.cat_to.mate:
            continue
        if potential_mate and not rel.cat_to.is_potential_mate(
                rel.cat_from, for_love_interest=True
        ):
            continue
        if rel.romantic_love > max_love_value:
            current_max_relationship = rel
            max_love_value = rel.romantic_love

    return current_max_relationship


def check_relationship_value(cat_from, cat_to, rel_value=None):
    """
    returns the value of the rel_value param given
    :param cat_from: the cat who is having the feelings
    :param cat_to: the cat that the feelings are directed towards
    :param rel_value: the relationship value that you're looking for,
    options are: romantic, platonic, dislike, admiration, comfortable, jealousy, trust
    """
    if cat_to.ID in cat_from.relationships:
        relationship = cat_from.relationships[cat_to.ID]
    else:
        relationship = cat_from.create_one_relationship(cat_to)

    if rel_value == "romantic":
        return relationship.romantic_love
    elif rel_value == "platonic":
        return relationship.platonic_like
    elif rel_value == "dislike":
        return relationship.dislike
    elif rel_value == "admiration":
        return relationship.admiration
    elif rel_value == "comfortable":
        return relationship.comfortable
    elif rel_value == "jealousy":
        return relationship.jealousy
    elif rel_value == "trust":
        return relationship.trust


def get_personality_compatibility(cat1, cat2):
    """Returns:
    True - if personalities have a positive compatibility
    False - if personalities have a negative compatibility
    None - if personalities have a neutral compatibility
    """
    personality1 = cat1.personality.trait
    personality2 = cat2.personality.trait

    if personality1 == personality2:
        if personality1 is None:
            return None
        return True

    lawfulness_diff = abs(cat1.personality.lawfulness - cat2.personality.lawfulness)
    sociability_diff = abs(cat1.personality.sociability - cat2.personality.sociability)
    aggression_diff = abs(cat1.personality.aggression - cat2.personality.aggression)
    stability_diff = abs(cat1.personality.stability - cat2.personality.stability)
    list_of_differences = [
        lawfulness_diff,
        sociability_diff,
        aggression_diff,
        stability_diff,
    ]

    running_total = 0
    for x in list_of_differences:
        if x <= 4:
            running_total += 1
        elif x >= 6:
            running_total -= 1

    if running_total >= 2:
        return True
    if running_total <= -2:
        return False

    return None


def get_cats_of_romantic_interest(cat):
    """Returns a list of cats, those cats are love interest of the given cat"""
    cats = []
    for inter_cat in cat.all_cats.values():
        if inter_cat.dead or inter_cat.outside or inter_cat.exiled:
            continue
        if inter_cat.ID == cat.ID:
            continue

        if inter_cat.ID not in cat.relationships:
            cat.create_one_relationship(inter_cat)
            if cat.ID not in inter_cat.relationships:
                inter_cat.create_one_relationship(cat)
            continue

        # Extra check to ensure they are potential mates
        if (
                inter_cat.is_potential_mate(cat, for_love_interest=True)
                and cat.relationships[inter_cat.ID].romantic_love > 0
        ):
            cats.append(inter_cat)
    return cats


def get_amount_of_cats_with_relation_value_towards(cat, value, all_cats):
    """
    Looks how many cats have the certain value
    :param cat: cat in question
    :param value: value which has to be reached
    :param all_cats: list of cats which has to be checked
    """

    # collect all true or false if the value is reached for the cat or not
    # later count or sum can be used to get the amount of cats
    # this will be handled like this, because it is easier / shorter to check
    relation_dict = {
        "romantic_love": [],
        "platonic_like": [],
        "dislike": [],
        "admiration": [],
        "comfortable": [],
        "jealousy": [],
        "trust": [],
    }

    for inter_cat in all_cats:
        if cat.ID in inter_cat.relationships:
            relation = inter_cat.relationships[cat.ID]
        else:
            continue

        relation_dict["romantic_love"].append(relation.romantic_love >= value)
        relation_dict["platonic_like"].append(relation.platonic_like >= value)
        relation_dict["dislike"].append(relation.dislike >= value)
        relation_dict["admiration"].append(relation.admiration >= value)
        relation_dict["comfortable"].append(relation.comfortable >= value)
        relation_dict["jealousy"].append(relation.jealousy >= value)
        relation_dict["trust"].append(relation.trust >= value)

    return_dict = {
        "romantic_love": sum(relation_dict["romantic_love"]),
        "platonic_like": sum(relation_dict["platonic_like"]),
        "dislike": sum(relation_dict["dislike"]),
        "admiration": sum(relation_dict["admiration"]),
        "comfortable": sum(relation_dict["comfortable"]),
        "jealousy": sum(relation_dict["jealousy"]),
        "trust": sum(relation_dict["trust"]),
    }

    return return_dict


def filter_relationship_type(
        group: list, filter_types: List[str], event_id: str = None, patrol_leader=None
):
    """
    filters for specific types of relationships between groups of cat objects, returns bool
    :param list[Cat] group: the group of cats to be tested (make sure they're in the correct order (i.e. if testing for
    parent/child, the cat being tested as parent must be index 0)
    :param list[str] filter_types: the relationship types to check for. possible types: "siblings", "mates",
    "mates_with_pl" (PATROL ONLY), "not_mates", "parent/child", "child/parent", "mentor/app", "app/mentor",
    (following tags check if value is over given int) "romantic_int", "platonic_int", "dislike_int", "comfortable_int",
    "jealousy_int", "trust_int"
    :param str event_id: if the event has an ID, include it here
    :param Cat patrol_leader: if you are testing a patrol, ensure you include the self.patrol_leader here
    """
    if not filter_types:
        return True

    # keeping this list here just for quick reference of what tags are handled here
    possible_rel_types = [
        "siblings",
        "mates",
        "mates_with_pl",
        "not_mates",
        "parent/child",
        "child/parent",
        "mentor/app",
        "app/mentor",
    ]

    possible_value_types = [
        "romantic",
        "platonic",
        "dislike",
        "comfortable",
        "jealousy",
        "trust",
        "admiration",
    ]

    if "siblings" in filter_types:
        test_cat = group[0]
        testing_cats = [cat for cat in group if cat.ID != test_cat.ID]

        siblings = [test_cat.is_sibling(inter_cat) for inter_cat in testing_cats]
        if not all(siblings):
            return False

    if "mates" in filter_types:
        # first test if more than one cat
        if len(group) == 1:
            return False

        # then if cats don't have the needed number of mates
        if not all(len(i.mate) >= (len(group) - 1) for i in group):
            return False

        # Now the expensive test.  We have to see if everone is mates with each other
        # Hopefully the cheaper tests mean this is only needed on events with a small number of cats
        for x in combinations(group, 2):
            if x[0].ID not in x[1].mate:
                return False

    # check if all cats are mates with p_l (they do not have to be mates with each other)
    if "mates_with_pl" in filter_types:
        # First test if there is more than one cat
        if len(group) == 1:
            return False

        # Check each cat to see if it is mates with the patrol leader
        for cat in group:
            if cat.ID == patrol_leader.ID:
                continue
            if cat.ID not in patrol_leader.mate:
                return False

    # Check if all cats are not mates
    if "not_mates" in filter_types:
        # opposite of mate check
        for x in combinations(group, 2):
            if x[0].ID in x[1].mate:
                return False

    # Check if the cats are in a parent/child relationship
    if "parent/child" in filter_types:
        if patrol_leader:
            if patrol_leader in group:
                group.remove(patrol_leader)
            group.insert(0, patrol_leader)
        # It should be exactly two cats for a "parent/child" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[0].is_parent(group[1]):
            return False

    if "child/parent" in filter_types:
        if patrol_leader:
            if patrol_leader in group:
                group.remove(patrol_leader)
            group.insert(0, patrol_leader)
        # It should be exactly two cats for a "parent/child" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[1].is_parent(group[0]):
            return False

    if "mentor/app" in filter_types:
        if patrol_leader:
            if patrol_leader in group:
                group.remove(patrol_leader)
            group.insert(0, patrol_leader)
        # It should be exactly two cats for a "parent/child" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[1].ID in group[0].apprentice:
            return False

    if "app/mentor" in filter_types:
        if patrol_leader:
            if patrol_leader in group:
                group.remove(patrol_leader)
            group.insert(0, patrol_leader)
        # It should be exactly two cats for a "parent/child" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[0].ID in group[1].apprentice:
            return False

    # Filtering relationship values
    break_loop = False
    for v_type in possible_value_types:
        # first get all tags for current value types
        tags = [constraint for constraint in filter_types if v_type in constraint]

        # If there is not a tag for the current value type, check next one
        if len(tags) == 0:
            continue

            # there should be only one value constraint for each value type
        elif len(tags) > 1:
            print(
                f"ERROR: event {event_id} has multiple relationship constraints for the value {v_type}."
            )
            break_loop = True
            break

        # try to extract the value/threshold from the text
        try:
            threshold = int(tags[0].split("_")[1])
        except:
            print(
                f"ERROR: event {event_id} with the relationship constraint for the value does not {v_type} follow the formatting guidelines."
            )
            break_loop = True
            break

        if threshold > 100:
            print(
                f"ERROR: event {event_id} has a relationship constraint for the value {v_type}, which is higher than the max value of a relationship."
            )
            break_loop = True
            break

        if threshold <= 0:
            print(
                f"ERROR: event {event_id} has a relationship constraint for the value {v_type}, which is lower than the min value of a relationship or 0."
            )
            break_loop = True
            break

        # each cat has to have relationships with this relationship value above the threshold
        fulfilled = True
        for inter_cat in group:
            rel_above_threshold = []
            group_ids = [cat.ID for cat in group]
            relevant_relationships = list(
                filter(
                    lambda rel: rel.cat_to.ID in group_ids
                                and rel.cat_to.ID != inter_cat.ID,
                    list(inter_cat.relationships.values()),
                )
            )

            # get the relationships depending on the current value type + threshold
            if v_type == "romantic":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.romantic_love >= threshold
                ]
            elif v_type == "platonic":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.platonic_like >= threshold
                ]
            elif v_type == "dislike":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.dislike >= threshold
                ]
            elif v_type == "comfortable":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.comfortable >= threshold
                ]
            elif v_type == "jealousy":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.jealousy >= threshold
                ]
            elif v_type == "trust":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.trust >= threshold
                ]
            elif v_type == "admiration":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.admiration >= threshold
                ]

            # if the lengths are not equal, one cat has not the relationship value which is needed to another cat of
            # the event
            if len(rel_above_threshold) + 1 != len(group):
                fulfilled = False
                break

        if not fulfilled:
            break_loop = True
            break

    # if break is used in the loop, the condition are not fulfilled
    # and this event should not be added to the filtered list
    if break_loop:
        return False

    return True


def gather_cat_objects(
        Cat, abbr_list: List[str], event, stat_cat=None, extra_cat=None
) -> list:
    """
    gathers cat objects from list of abbreviations used within an event format block
    :param Cat Cat: Cat class
    :param list[str] abbr_list: The list of abbreviations, supports "m_c", "r_c", "p_l", "s_c", "app1" through "app6",
    "clan", "some_clan", "patrol", "multi", "n_c{index}"
    :param event: the controlling class of the event (e.g. Patrol, HandleShortEvents), default None
    :param Cat stat_cat: if passing the Patrol class, must include stat_cat separately
    :param Cat extra_cat: if not passing an event class, include the single affected cat object here. If you are not
    passing a full event class, then be aware that you can only include "m_c" as a cat abbreviation in your rel block.
    The other cat abbreviations will not work.
    :return: list of cat objects
    """
    out_set = set()

    for abbr in abbr_list:
        if abbr == "m_c":
            if extra_cat:
                out_set.add(extra_cat)
            else:
                out_set.add(event.main_cat)
        elif abbr == "r_c":
            out_set.add(event.random_cat)
        elif abbr == "p_l":
            out_set.add(event.patrol_leader)
        elif abbr == "s_c":
            out_set.add(stat_cat)
        elif abbr == "app1" and len(event.patrol_apprentices) >= 1:
            out_set.add(event.patrol_apprentices[0])
        elif abbr == "app2" and len(event.patrol_apprentices) >= 2:
            out_set.add(event.patrol_apprentices[1])
        elif abbr == "app3" and len(event.patrol_apprentices) >= 3:
            out_set.add(event.patrol_apprentices[2])
        elif abbr == "app4" and len(event.patrol_apprentices) >= 4:
            out_set.add(event.patrol_apprentices[3])
        elif abbr == "app5" and len(event.patrol_apprentices) >= 5:
            out_set.add(event.patrol_apprentices[4])
        elif abbr == "app6" and len(event.patrol_apprentices) >= 6:
            out_set.add(event.patrol_apprentices[5])
        elif abbr == "clan":
            out_set.update(
                [x for x in Cat.all_cats_list if not (x.dead or x.outside or x.exiled)]
            )
        elif abbr == "some_clan":  # 1 / 8 of clan cats are affected
            clan_cats = [
                x for x in Cat.all_cats_list if not (x.dead or x.outside or x.exiled)
            ]
            out_set.update(
                sample(clan_cats, randint(1, max(1, round(len(clan_cats) / 8))))
            )
        elif abbr == "patrol":
            out_set.update(event.patrol_cats)
        elif abbr == "multi":
            cat_num = randint(1, max(1, len(event.patrol_cats) - 1))
            out_set.update(sample(event.patrol_cats, cat_num))
        elif re.match(r"n_c:[0-9]+", abbr):
            index = re.match(r"n_c:([0-9]+)", abbr).group(1)
            index = int(index)
            if index < len(event.new_cats):
                out_set.update(event.new_cats[index])
        else:
            print(f"WARNING: Unsupported abbreviation {abbr}")

    return list(out_set)


def unpack_rel_block(
        Cat, relationship_effects: List[dict], event=None, stat_cat=None, extra_cat=None
):
    """
    Unpacks the info from the relationship effect block used in patrol and moon events, then adjusts rel values
    accordingly.

    :param Cat Cat: Cat class
    :param list[dict] relationship_effects: the relationship effect block
    :param event: the controlling class of the event (e.g. Patrol, HandleShortEvents), default None
    :param Cat stat_cat: if passing the Patrol class, must include stat_cat separately
    :param Cat extra_cat: if not passing an event class, include the single affected cat object here. If you are not passing a full event class, then be aware that you can only include "m_c" as a cat abbreviation in your rel block.  The other cat abbreviations will not work.
    """
    possible_values = (
        "romantic",
        "platonic",
        "dislike",
        "comfort",
        "jealous",
        "trust",
        "respect",
    )

    for block in relationship_effects:
        cats_from = block.get("cats_from", [])
        cats_to = block.get("cats_to", [])
        amount = block.get("amount")
        values = [x for x in block.get("values", ()) if x in possible_values]

        # Gather actual cat objects:
        cats_from_ob = gather_cat_objects(Cat, cats_from, event, stat_cat, extra_cat)
        cats_to_ob = gather_cat_objects(Cat, cats_to, event, stat_cat, extra_cat)

        # Remove any "None" that might have snuck in
        if None in cats_from_ob:
            cats_from_ob.remove(None)
        if None in cats_to_ob:
            cats_to_ob.remove(None)

        # Check to see if value block
        if not (cats_to_ob and cats_from_ob and values and isinstance(amount, int)):
            print(f"Relationship block incorrectly formatted: {block}")
            continue

        positive = False

        # grabbing values
        romantic_love = 0
        platonic_like = 0
        dislike = 0
        comfortable = 0
        jealousy = 0
        admiration = 0
        trust = 0
        if "romantic" in values:
            romantic_love = amount
            if amount > 0:
                positive = True
        if "platonic" in values:
            platonic_like = amount
            if amount > 0:
                positive = True
        if "dislike" in values:
            dislike = amount
            if amount < 0:
                positive = True
        if "comfort" in values:
            comfortable = amount
            if amount > 0:
                positive = True
        if "jealous" in values:
            jealousy = amount
            if amount < 0:
                positive = True
        if "trust" in values:
            trust = amount
            if amount > 0:
                positive = True
        if "respect" in values:
            admiration = amount
            if amount > 0:
                positive = True

        if positive:
            effect = i18n.t("relationships.positive_postscript")
        else:
            effect = i18n.t("relationships.negative_postscript")

        # Get log
        log1 = None
        log2 = None
        if block.get("log"):
            log = block.get("log")
            if isinstance(log, str):
                log1 = log
            elif isinstance(log, list):
                if len(log) >= 2:
                    log1 = log[0]
                    log2 = log[1]
                elif len(log) == 1:
                    log1 = log[0]
            else:
                print(f"something is wrong with relationship log: {log}")

        if not log1:
            if hasattr(event, "text"):
                try:
                    log1 = event.text + effect
                except AttributeError:
                    print(
                        f"WARNING: event changed relationships but did not create a relationship log"
                    )
            else:
                log1 = i18n.t("defaults.relationship_log") + effect
        if not log2:
            if hasattr(event, "text"):
                try:
                    log2 = event.text + effect
                except AttributeError:
                    print(
                        f"WARNING: event changed relationships but did not create a relationship log"
                    )
            else:
                log2 = i18n.t("defaults.relationship_log") + effect

        change_relationship_values(
            cats_to_ob,
            cats_from_ob,
            romantic_love,
            platonic_like,
            dislike,
            admiration,
            comfortable,
            jealousy,
            trust,
            log=log1,
        )

        if block.get("mutual"):
            change_relationship_values(
                cats_from_ob,
                cats_to_ob,
                romantic_love,
                platonic_like,
                dislike,
                admiration,
                comfortable,
                jealousy,
                trust,
                log=log2,
            )


def change_relationship_values(
        cats_to: list,
        cats_from: list,
        romantic_love: int = 0,
        platonic_like: int = 0,
        dislike: int = 0,
        admiration: int = 0,
        comfortable: int = 0,
        jealousy: int = 0,
        trust: int = 0,
        auto_romance: bool = False,
        log: str = None,
):
    """
    changes relationship values according to the parameters.

    :param list[Cat] cats_from: list of cat objects whose rel values will be affected
    (e.g. cat_from loses trust in cat_to)
    :param list[Cat] cats_to: list of cats objects who are the target of that rel value
    (e.g. cat_from loses trust in cat_to)
    :param int romantic_love: amount to change romantic, default 0
    :param int platonic_like: amount to change platonic, default 0
    :param int dislike: amount to change dislike, default 0
    :param int admiration: amount to change admiration (respect), default 0
    :param int comfortable: amount to change comfort, default 0
    :param int jealousy: amount to change jealousy, default 0
    :param int trust: amount to change trust, default 0
    :param bool auto_romance: if the cat_from already has romantic value with cat_to, then the platonic_like param value
    will also be applied to romantic, default False
    :param str log: the string to append to the relationship log of cats involved
    """

    # This is just for test prints - DON'T DELETE - you can use this to test if relationships are changing
    """changed = False
    if romantic_love == 0 and platonic_like == 0 and dislike == 0 and admiration == 0 and \
            comfortable == 0 and jealousy == 0 and trust == 0:
        changed = False
    else:
        changed = True"""

    # pick out the correct cats
    for single_cat_from in cats_from:
        for single_cat_to in cats_to:
            # make sure we aren't trying to change a cat's relationship with themself
            if single_cat_from == single_cat_to:
                continue

            # if the cats don't know each other, start a new relationship
            if single_cat_to.ID not in single_cat_from.relationships:
                single_cat_from.create_one_relationship(single_cat_to)

            rel = single_cat_from.relationships[single_cat_to.ID]

            # here we just double-check that the cats are allowed to be romantic with each other
            if (
                    single_cat_from.is_potential_mate(single_cat_to, for_love_interest=True)
                    or single_cat_to.ID in single_cat_from.mate
            ):
                # if cat already has romantic feelings then automatically increase romantic feelings
                # when platonic feelings would increase
                if rel.romantic_love > 0 and auto_romance:
                    romantic_love = platonic_like

                # now gain the romance
                rel.romantic_love += romantic_love

            # gain other rel values
            rel.platonic_like += platonic_like
            rel.dislike += dislike
            rel.admiration += admiration
            rel.comfortable += comfortable
            rel.jealousy += jealousy
            rel.trust += trust

            # for testing purposes - DON'T DELETE - you can use this to test if relationships are changing
            """
            print(str(single_cat_from.name) + " gained relationship with " + str(rel.cat_to.name) + ": " +
                  "Romantic: " + str(romantic_love) +
                  " /Platonic: " + str(platonic_like) +
                  " /Dislike: " + str(dislike) +
                  " /Respect: " + str(admiration) +
                  " /Comfort: " + str(comfortable) +
                  " /Jealousy: " + str(jealousy) +
                  " /Trust: " + str(trust)) if changed else print("No relationship change")"""

            if log and isinstance(log, str):
                log_text = log + i18n.t(
                    "relationships.age_postscript",
                    name=str(single_cat_to.name),
                    count=single_cat_to.moons,
                )
                if log_text not in rel.log:
                    rel.log.append(log_text)


# ---------------------------------------------------------------------------- #
#                               Text Adjust                                    #
# ---------------------------------------------------------------------------- #


def get_leader_life_notice() -> str:
    """
    Returns a string specifying how many lives the leader has left or notifying of the leader's full death
    """
    if game.clan.instructor.df:
        return i18n.t("cat.history.leader_lives_left_df", count=game.clan.leader_lives)
    return i18n.t("cat.history.leader_lives_left_sc", count=game.clan.leader_lives)


def get_other_clan_relation(relation):
    """
    converts int value into string relation and returns string: "hostile", "neutral", or "ally"
    :param relation: the other_clan.relations value
    """

    if int(relation) >= 17:
        return "ally"
    elif 7 < int(relation) < 17:
        return "neutral"
    elif int(relation) <= 7:
        return "hostile"


def pronoun_repl(m, cat_pronouns_dict, raise_exception=False):
    """Helper function for add_pronouns. If raise_exception is
    False, any error in pronoun formatting will not raise an
    exception, and will use a simple replacement "error" """

    # Add protection about the "insert" sometimes used
    if m.group(0) == "{insert}":
        return m.group(0)

    inner_details = m.group(1).split("/")
    out = None

    try:
        if inner_details[1].upper() == "PLURAL":
            inner_details.pop(1)  # remove plural tag so it can be processed as normal
            catlist = []
            for cat in inner_details[1].split("+"):
                try:
                    catlist.append(cat_pronouns_dict[cat][1])
                except KeyError:
                    print(f"Missing pronouns for {cat}")
                    continue
            d = determine_plural_pronouns(catlist)
        else:
            try:
                d = cat_pronouns_dict[inner_details[1]][1]
            except KeyError:
                if inner_details[0].upper() == "ADJ":
                    # find the default - this is a semi-expected behaviour for the adj tag as it may be called when
                    # there is no relevant cat
                    return inner_details[localization.get_default_adj()]
                else:
                    logger.warning(
                        f"Could not get pronouns for {inner_details[1]}. Using default."
                    )
                    print(
                        f"Could not get pronouns for {inner_details[1]}. Using default."
                    )
                    d = choice(localization.get_new_pronouns("default"))

        if inner_details[0].upper() == "PRONOUN":
            out = d[inner_details[2]]
        elif inner_details[0].upper() == "VERB":
            out = inner_details[d["conju"] + 1]
        elif inner_details[0].upper() == "ADJ":
            out = inner_details[(d["gender"] + 2) if "gender" in d else 2]

        if out is not None:
            if inner_details[-1] == "CAP":
                out = out.capitalize()
            return out

        if raise_exception:
            raise KeyError(
                f"Pronoun tag: {m.group(1)} is not properly"
                "indicated as a PRONOUN or VERB tag."
            )

        print("Failed to find pronoun:", m.group(1))
        return "error1"
    except (KeyError, IndexError) as e:
        if raise_exception:
            raise

        logger.exception("Failed to find pronoun: " + m.group(1))
        print("Failed to find pronoun:", m.group(1))
        return "error2"


def name_repl(m, cat_dict):
    """Name replacement"""
    return cat_dict[m.group(0)][0]


def process_text(text, cat_dict, raise_exception=False):
    """Add the correct name and pronouns into a string."""
    adjust_text = re.sub(
        r"(?<!%)\{(.*?)}", lambda x: pronoun_repl(x, cat_dict, raise_exception), text
    )

    name_patterns = [r"(?<!\{)" + re.escape(l) + r"(?!\})" for l in cat_dict]
    adjust_text = re.sub(
        "|".join(name_patterns), lambda x: name_repl(x, cat_dict), adjust_text
    )
    return adjust_text


def adjust_list_text(list_of_items: List) -> str:
    """
    returns the list in correct grammar format (i.e. item1, item2, item3 and item4)
    this works with any number of items
    :param list_of_items: the list of items you want converted
    :return: the new string
    """

    if not isinstance(list_of_items, list):
        logger.warning("non-list object was passed to adjust_list_text")
        list_of_items = list(list_of_items)

    if len(list_of_items) == 0:
        item1 = ""
        item2 = ""
    elif len(list_of_items) == 1:
        item1 = list_of_items[0]
        item2 = ""
    elif len(list_of_items) == 2:
        item1 = list_of_items[0]
        item2 = list_of_items[1]
    else:
        item1 = ", ".join(list_of_items[:-1])
        if get_lang_config().get("oxford_comma"):
            item1 += ","
        item2 = list_of_items[-1]

    return i18n.t("utility.items", count=len(list_of_items), item1=item1, item2=item2)


def adjust_prey_abbr(patrol_text):
    """
    checks for prey abbreviations and returns adjusted text
    """
    global PREY_LISTS
    if langs["prey"] != i18n.config.get("locale"):
        langs["prey"] = i18n.config.get("locale")
        PREY_LISTS = load_lang_resource("patrols/prey_text_replacements.json")

    for abbr in PREY_LISTS["abbreviations"]:
        if abbr in patrol_text:
            chosen_list = PREY_LISTS["abbreviations"].get(abbr)
            chosen_list = PREY_LISTS[chosen_list]
            prey = choice(chosen_list)
            patrol_text = patrol_text.replace(abbr, prey)

    return patrol_text


def get_special_snippet_list(
        chosen_list, amount, sense_groups=None, return_string=True
):
    """
    function to grab items from various lists in snippet_collections.json
    list options are:
    -prophecy_list - sense_groups = sight, sound, smell, emotional, touch
    -omen_list - sense_groups = sight, sound, smell, emotional, touch
    -clair_list  - sense_groups = sound, smell, emotional, touch, taste
    -dream_list (this list doesn't have sense_groups)
    -story_list (this list doesn't have sense_groups)
    :param chosen_list: pick which list you want to grab from
    :param amount: the amount of items you want the returned list to contain
    :param sense_groups: list which senses you want the snippets to correspond with:
     "touch", "sight", "emotional", "sound", "smell" are the options. Default is None, if left as this then all senses
     will be included (if the list doesn't have sense categories, then leave as None)
    :param return_string: if True then the function will format the snippet list with appropriate commas and 'ands'.
    This will work with any number of items. If set to True, then the function will return a string instead of a list.
    (i.e. ["hate", "fear", "dread"] becomes "hate, fear, and dread") - Default is True
    :return: a list of the chosen items from chosen_list or a formatted string if format is True
    """
    biome = game.clan.biome.casefold()
    global SNIPPETS
    if langs["snippet"] != i18n.config.get("locale"):
        langs["snippet"] = i18n.config.get("locale")
        SNIPPETS = load_lang_resource("snippet_collections.json")

    # these lists don't get sense specific snippets, so is handled first
    if chosen_list in ["dream_list", "story_list"]:
        if (
                chosen_list == "story_list"
        ):  # story list has some biome specific things to collect
            snippets = SNIPPETS[chosen_list]["general"]
            snippets.extend(SNIPPETS[chosen_list][biome])
        elif (
                chosen_list == "clair_list"
        ):  # the clair list also pulls from the dream list
            snippets = SNIPPETS[chosen_list]
            snippets.extend(SNIPPETS["dream_list"])
        else:  # the dream list just gets the one
            snippets = SNIPPETS[chosen_list]

    else:
        # if no sense groups were specified, use all of them
        if not sense_groups:
            if chosen_list == "clair_list":
                sense_groups = ["taste", "sound", "smell", "emotional", "touch"]
            else:
                sense_groups = ["sight", "sound", "smell", "emotional", "touch"]

        # find the correct lists and compile them
        snippets = []
        for sense in sense_groups:
            snippet_group = SNIPPETS[chosen_list][sense]
            snippets.extend(snippet_group["general"])
            snippets.extend(snippet_group[biome])

    # now choose a unique snippet from each snip list
    unique_snippets = []
    for snip_list in snippets:
        unique_snippets.append(choice(snip_list))

    # pick out our final snippets
    final_snippets = sample(unique_snippets, k=amount)

    if return_string:
        text = adjust_list_text(final_snippets)
        return text
    else:
        return final_snippets


def find_special_list_types(text):
    """
    purely to identify which senses are being called for by a snippet abbreviation
    returns adjusted text, sense list, list type, and cat_tag
    """
    senses = []
    list_text = None
    list_type = None
    words = text.split(" ")
    for bit in words:
        if "_list" in bit:
            list_text = bit
            # just getting rid of pesky punctuation
            list_text = list_text.replace(".", "")
            list_text = list_text.replace(",", "")
            break

    if not list_text:
        return text, None, None, None

    parts_of_tag = list_text.split("/")

    try:
        cat_tag = parts_of_tag[1]
    except IndexError:
        cat_tag = None

    if "omen_list" in list_text:
        list_type = "omen_list"
    elif "prophecy_list" in list_text:
        list_type = "prophecy_list"
    elif "dream_list" in list_text:
        list_type = "dream_list"
    elif "clair_list" in list_text:
        list_type = "clair_list"
    elif "story_list" in list_text:
        list_type = "story_list"
    else:
        logger.error("WARNING: no list type found for %s", list_text)
        return text, None, None, None

    if "_sight" in list_text:
        senses.append("sight")
    if "_sound" in list_text:
        senses.append("sound")
    if "_smell" in list_text:
        senses.append("smell")
    if "_emotional" in list_text:
        senses.append("emotional")
    if "_touch" in list_text:
        senses.append("touch")
    if "_taste" in list_text:
        senses.append("taste")

    text = text.replace(list_text, list_type)

    return text, senses, list_type, cat_tag


def history_text_adjust(text, other_clan_name, clan, other_cat_rc=None):
    """
    we want to handle history text on its own because it needs to preserve the pronoun tags and cat abbreviations.
    this is so that future pronoun changes or name changes will continue to be reflected in history
    """
    vowels = ["A", "E", "I", "O", "U"]

    if "o_c_n" in text:
        pos = 0
        for x in range(text.count("o_c_n")):
            if "o_c_n" in text:
                for y in vowels:
                    if str(other_clan_name).startswith(y):
                        modify = text.split()
                        if "o_c_n" in modify:
                            pos = modify.index("o_c_n")
                        if "o_c_n's" in modify:
                            pos = modify.index("o_c_n's")
                        if "o_c_n." in modify:
                            pos = modify.index("o_c_n.")
                        if modify[pos - 1] == "a":
                            modify.remove("a")
                            modify.insert(pos - 1, "an")
                        text = " ".join(modify)
                        break

        text = text.replace("o_c_n", str(other_clan_name))

    if "c_n" in text:
        text = text.replace("c_n", clan.name)
    if "r_c" in text and other_cat_rc:
        text = selective_replace(text, "r_c", str(other_cat_rc.name))
    return text


def selective_replace(text, pattern, replacement):
    i = 0
    while i < len(text):
        index = text.find(pattern, i)
        if index == -1:
            break
        start_brace = text.rfind("{", 0, index)
        end_brace = text.find("}", index)
        if start_brace != -1 and end_brace != -1 and start_brace < index < end_brace:
            i = index + len(pattern)
        else:
            text = text[:index] + replacement + text[index + len(pattern):]
            i = index + len(replacement)

    return text


def ongoing_event_text_adjust(Cat, text, clan=None, other_clan_name=None):
    """
    This function is for adjusting the text of ongoing events
    :param Cat: the cat class
    :param text: the text to be adjusted
    :param clan: the name of the clan
    :param other_clan_name: the other Clan's name if another Clan is involved
    """
    cat_dict = {}
    if "lead_name" in text:
        kitty = Cat.fetch_cat(game.clan.leader)
        cat_dict["lead_name"] = (str(kitty.name), choice(kitty.pronouns))
    if "dep_name" in text:
        kitty = Cat.fetch_cat(game.clan.deputy)
        cat_dict["dep_name"] = (str(kitty.name), choice(kitty.pronouns))
    if "med_name" in text:
        kitty = choice(get_alive_status_cats(Cat, ["medicine cat"], working=True))
        cat_dict["med_name"] = (str(kitty.name), choice(kitty.pronouns))

    if cat_dict:
        text = process_text(text, cat_dict)

    if other_clan_name:
        text = text.replace("o_c_n", other_clan_name)
    if clan:
        clan_name = str(clan.name)
    else:
        if game.clan is None:
            clan_name = game.switches["clan_list"][0]
        else:
            clan_name = str(game.clan.name)

    text = text.replace("c_n", clan_name + "Clan")

    return text


def event_text_adjust(
        Cat: Type["Cat"],
        text,
        *,
        patrol_leader=None,
        main_cat=None,
        random_cat=None,
        stat_cat=None,
        victim_cat=None,
        patrol_cats: list = None,
        patrol_apprentices: list = None,
        new_cats: list = None,
        multi_cats: list = None,
        clan=None,
        other_clan=None,
        chosen_herb: str = None,
):
    """
    handles finding abbreviations in the text and replacing them appropriately, returns the adjusted text
    :param Cat Cat: always pass the Cat class
    :param str text: the text being adjusted
    :param Cat patrol_leader: Cat object for patrol_leader (p_l), if present
    :param Cat main_cat: Cat object for main_cat (m_c), if present
    :param Cat random_cat: Cat object for random_cat (r_c), if present
    :param Cat stat_cat: Cat object for stat_cat (s_c), if present
    :param Cat victim_cat: Cat object for victim_cat (mur_c), if present
    :param list[Cat] patrol_cats: List of Cat objects for cats in patrol, if present
    :param list[Cat] patrol_apprentices: List of Cat objects for patrol_apprentices (app#), if present
    :param list[Cat] new_cats: List of Cat objects for new_cats (n_c:index), if present
    :param list[Cat] multi_cats: List of Cat objects for multi_cat (multi_cat), if present
    :param Clan clan: pass game.clan
    :param OtherClan other_clan: OtherClan object for other_clan (o_c_n), if present
    :param str chosen_herb: string of chosen_herb (chosen_herb), if present
    """
    vowels = ["A", "E", "I", "O", "U"]

    if not text:
        text = "This should not appear, report as a bug please! Tried to adjust the text, but no text was provided."
        print("WARNING: Tried to adjust text, but no text was provided.")

    # this check is really just here to catch odd bug edge-cases from old saves, specifically in death history
    # otherwise we should really *never* have lists being passed as the text
    if isinstance(text, list):
        text = text[0]

    replace_dict = {}

    # special lists - this needs to happen first for pronoun tag reasons
    text, senses, list_type, cat_tag = find_special_list_types(text)
    if list_type:
        sign_list = get_special_snippet_list(
            list_type, amount=randint(1, 3), sense_groups=senses
        )
        text = text.replace(list_type, str(sign_list))
        if cat_tag:
            text = text.replace("cat_tag", cat_tag)

    # main_cat
    if "m_c" in text:
        if main_cat:
            replace_dict["m_c"] = (str(main_cat.name), choice(main_cat.pronouns))

    # patrol_lead
    if "p_l" in text:
        if patrol_leader:
            replace_dict["p_l"] = (
                str(patrol_leader.name),
                choice(patrol_leader.pronouns),
            )

    # random_cat
    if "r_c" in text:
        if random_cat:
            replace_dict["r_c"] = (str(random_cat.name), get_pronouns(random_cat))

    # stat cat
    if "s_c" in text:
        if stat_cat:
            replace_dict["s_c"] = (str(stat_cat.name), get_pronouns(stat_cat))

    # other_cats
    if patrol_cats:
        other_cats = [
            i
            for i in patrol_cats
            if i not in [patrol_leader, random_cat, patrol_apprentices]
        ]
        other_cat_abbr = ["o_c1", "o_c2", "o_c3", "o_c4"]
        for i, abbr in enumerate(other_cat_abbr):
            if abbr not in text:
                continue
            if len(other_cats) > i:
                replace_dict[abbr] = (
                    str(other_cats[i].name),
                    choice(other_cats[i].pronouns),
                )

    # patrol_apprentices
    app_abbr = ["app1", "app2", "app3", "app4", "app5", "app6"]
    for i, abbr in enumerate(app_abbr):
        if abbr not in text:
            continue
        if len(patrol_apprentices) > i:
            replace_dict[abbr] = (
                str(patrol_apprentices[i].name),
                choice(patrol_apprentices[i].pronouns),
            )

    # new_cats (include pre version)
    if "n_c" in text:
        for i, cat_list in enumerate(new_cats):
            if len(new_cats) > 1:
                pronoun = localization.get_new_pronouns("default plural")[0]
            else:
                pronoun = choice(cat_list[0].pronouns)

            replace_dict[f"n_c:{i}"] = (str(cat_list[0].name), pronoun)
            replace_dict[f"n_c_pre:{i}"] = (str(cat_list[0].name.prefix), pronoun)

    # mur_c (murdered cat for reveals)
    if "mur_c" in text:
        replace_dict["mur_c"] = (str(victim_cat.name), get_pronouns(victim_cat))

    # lead_name
    if "lead_name" in text:
        leader = Cat.fetch_cat(game.clan.leader)
        replace_dict["lead_name"] = (str(leader.name), choice(leader.pronouns))

    # dep_name
    if "dep_name" in text:
        deputy = Cat.fetch_cat(game.clan.deputy)
        replace_dict["dep_name"] = (str(deputy.name), choice(deputy.pronouns))

    # med_name
    if "med_name" in text:
        med = choice(get_alive_status_cats(Cat, ["medicine cat"], working=True))
        replace_dict["med_name"] = (str(med.name), choice(med.pronouns))

    # assign all names and pronouns
    if replace_dict:
        text = process_text(text, replace_dict)

    # multi_cat
    if "multi_cat" in text:
        name_list = []
        for _cat in multi_cats:
            name_list.append(str(_cat.name))
        list_text = adjust_list_text(name_list)
        text = text.replace("multi_cat", list_text)

    # other_clan_name
    if "o_c_n" in text:
        other_clan_name = other_clan.name
        pos = 0
        for x in range(text.count("o_c_n")):
            if "o_c_n" in text:
                for y in vowels:
                    if str(other_clan_name).startswith(y):
                        modify = text.split()
                        if "o_c_n" in modify:
                            pos = modify.index("o_c_n")
                        if "o_c_n's" in modify:
                            pos = modify.index("o_c_n's")
                        if "o_c_n." in modify:
                            pos = modify.index("o_c_n.")
                        if modify[pos - 1] == "a":
                            modify.remove("a")
                            modify.insert(pos - 1, "an")
                        text = " ".join(modify)
                        break

        text = text.replace("o_c_n", str(other_clan_name) + "Clan")

    # clan_name
    if "c_n" in text:
        try:
            clan_name = clan.name
        except AttributeError:
            clan_name = game.switches["clan_list"][0]

        pos = 0
        for x in range(text.count("c_n")):
            if "c_n" in text:
                for y in vowels:
                    if str(clan_name).startswith(y):
                        modify = text.split()
                        if "c_n" in modify:
                            pos = modify.index("c_n")
                        if "c_n's" in modify:
                            pos = modify.index("c_n's")
                        if "c_n." in modify:
                            pos = modify.index("c_n.")
                        if modify[pos - 1] == "a":
                            modify.remove("a")
                            modify.insert(pos - 1, "an")
                        text = " ".join(modify)
                        break

        text = text.replace("c_n", str(clan_name) + "Clan")

    # prey lists
    text = adjust_prey_abbr(text)

    # acc_plural (only works for main_cat's acc)
    if "acc_plural" in text:
        text = text.replace(
            "acc_plural", i18n.t(f"cat.accessories.{main_cat.pelt.accessory[-1]}", count=2)
        )

    # acc_singular (only works for main_cat's acc)
    if "acc_singular" in text:
        text = text.replace(
            "acc_singular",
            i18n.t(f"cat.accessories.{main_cat.pelt.accessory[-1]}", count=1),
        )

    if "given_herb" in text:
        text = text.replace(
            "given_herb", i18n.t(f"conditions.herbs.{chosen_herb}", count=2)
        )

    return text


def leader_ceremony_text_adjust(
        Cat,
        text,
        leader,
        life_giver=None,
        virtue=None,
        extra_lives=None,
):
    """
    used to adjust the text for leader ceremonies
    """
    replace_dict = {
        "m_c_star": (str(leader.name.prefix + "star"), choice(leader.pronouns)),
        "m_c": (str(leader.name.prefix + leader.name.suffix), choice(leader.pronouns)),
    }

    if life_giver:
        replace_dict["r_c"] = (
            str(Cat.fetch_cat(life_giver).name),
            choice(Cat.fetch_cat(life_giver).pronouns),
        )

    text = process_text(text, replace_dict)

    if virtue:
        virtue = process_text(virtue, replace_dict)
        text = text.replace("[virtue]", virtue)

    if extra_lives:
        text = text.replace("[life_num]", str(extra_lives))

    text = text.replace("c_n", str(game.clan.name) + "Clan")

    return text


def ceremony_text_adjust(
        Cat,
        text,
        cat,
        old_name=None,
        dead_mentor=None,
        mentor=None,
        previous_alive_mentor=None,
        random_honor=None,
        living_parents=(),
        dead_parents=(),
):
    clanname = str(game.clan.name + "Clan")

    random_honor = random_honor
    random_living_parent = None
    random_dead_parent = None

    adjust_text = text

    cat_dict = {
        "m_c": (
            (str(cat.name), choice(cat.pronouns)) if cat else ("cat_placeholder", None)
        ),
        "(mentor)": (
            (str(mentor.name), choice(mentor.pronouns))
            if mentor
            else ("mentor_placeholder", None)
        ),
        "(deadmentor)": (
            (str(dead_mentor.name), get_pronouns(dead_mentor))
            if dead_mentor
            else ("dead_mentor_name", None)
        ),
        "(previous_mentor)": (
            (str(previous_alive_mentor.name), choice(previous_alive_mentor.pronouns))
            if previous_alive_mentor
            else ("previous_mentor_name", None)
        ),
        "l_n": (
            (str(game.clan.leader.name), choice(game.clan.leader.pronouns))
            if game.clan.leader
            else ("leader_name", None)
        ),
        "c_n": (clanname, None),
    }

    if old_name:
        cat_dict["(old_name)"] = (old_name, None)

    if random_honor:
        cat_dict["r_h"] = (random_honor, None)

    if "p1" in adjust_text and "p2" in adjust_text and len(living_parents) >= 2:
        cat_dict["p1"] = (
            str(living_parents[0].name),
            choice(living_parents[0].pronouns),
        )
        cat_dict["p2"] = (
            str(living_parents[1].name),
            choice(living_parents[1].pronouns),
        )
    elif living_parents:
        random_living_parent = choice(living_parents)
        cat_dict["p1"] = (
            str(random_living_parent.name),
            choice(random_living_parent.pronouns),
        )
        cat_dict["p2"] = (
            str(random_living_parent.name),
            choice(random_living_parent.pronouns),
        )

    if (
            "dead_par1" in adjust_text
            and "dead_par2" in adjust_text
            and len(dead_parents) >= 2
    ):
        cat_dict["dead_par1"] = (
            str(dead_parents[0].name),
            get_pronouns(dead_parents[0]),
        )
        cat_dict["dead_par2"] = (
            str(dead_parents[1].name),
            get_pronouns(dead_parents[1]),
        )
    elif dead_parents:
        random_dead_parent = choice(dead_parents)
        cat_dict["dead_par1"] = (
            str(random_dead_parent.name),
            get_pronouns(random_dead_parent),
        )
        cat_dict["dead_par2"] = (
            str(random_dead_parent.name),
            get_pronouns(random_dead_parent),
        )

    adjust_text = process_text(adjust_text, cat_dict)

    return adjust_text, random_living_parent, random_dead_parent


def get_pronouns(Cat: "Cat"):
    """Get a cat's pronoun even if the cat has faded to prevent crashes (use gender-neutral pronouns when the cat has faded)"""
    if Cat.pronouns == {}:
        return localization.get_new_pronouns("default")
    else:
        return choice(Cat.pronouns)


def shorten_text_to_fit(
        name, length_limit, font_size=None, font_type="resources/fonts/NotoSans-Medium.ttf"
):
    length_limit = length_limit * scripts.game_structure.screen_settings.screen_scale
    if font_size is None:
        font_size = 15
    font_size = floor(font_size * scripts.game_structure.screen_settings.screen_scale)

    if font_type == "clangen":
        font_type = "resources/fonts/clangen.ttf"
    # Create the font object
    font = pygame.font.Font(font_type, font_size)

    # Add dynamic name lengths by checking the actual width of the text
    total_width = 0
    short_name = ""
    ellipsis_width = font.size("...")[0]
    for index, character in enumerate(name):
        char_width = font.size(character)[0]

        # Check if the current character is the last one and its width is less than or equal to ellipsis_width
        if index == len(name) - 1 and char_width <= ellipsis_width:
            short_name += character
        else:
            total_width += char_width
            if total_width + ellipsis_width > length_limit:
                break
            short_name += character

    # If the name was truncated, add "..."
    if len(short_name) < len(name):
        short_name += "..."

    return short_name


# ---------------------------------------------------------------------------- #
#                                    Sprites                                   #
# ---------------------------------------------------------------------------- #


def ui_scale(rect: pygame.Rect):
    """
    Scales a pygame.Rect appropriately for the UI scaling currently in use.
    :param rect: a pygame.Rect
    :return: the same pygame.Rect, scaled for the current UI.
    """
    # offset can be negative to allow for correct anchoring
    rect[0] = floor(rect[0] * scripts.game_structure.screen_settings.screen_scale)
    rect[1] = floor(rect[1] * scripts.game_structure.screen_settings.screen_scale)
    # if the dimensions are negative, it's dynamically scaled, ignore
    rect[2] = (
        floor(rect[2] * scripts.game_structure.screen_settings.screen_scale)
        if rect[2] > 0
        else rect[2]
    )
    rect[3] = (
        floor(rect[3] * scripts.game_structure.screen_settings.screen_scale)
        if rect[3] > 0
        else rect[3]
    )

    return rect


def ui_scale_dimensions(dim: Tuple[int, int]):
    """
    Use to scale the dimensions of an item - WILL IGNORE NEGATIVE VALUES
    :param dim: The dimensions to scale
    :return: The scaled dimensions
    """
    return (
        floor(dim[0] * scripts.game_structure.screen_settings.screen_scale)
        if dim[0] > 0
        else dim[0],
        floor(dim[1] * scripts.game_structure.screen_settings.screen_scale)
        if dim[1] > 0
        else dim[1],
    )


def ui_scale_offset(coords: Tuple[int, int]):
    """
    Use to scale the offset of an item (i.e. the first 2 values of a pygame.Rect).
    Not to be confused with ui_scale_blit.
    :param coords: The coordinates to scale
    :return: The scaled coordinates
    """
    return (
        floor(coords[0] * scripts.game_structure.screen_settings.screen_scale),
        floor(coords[1] * scripts.game_structure.screen_settings.screen_scale),
    )


def ui_scale_value(val: int):
    """
    Use to scale a single value according to the UI scale. If you need this one,
    you're probably doing something unusual. Try to avoid where possible.
    :param val: The value to scale
    :return: The scaled value
    """
    return floor(val * scripts.game_structure.screen_settings.screen_scale)


def ui_scale_blit(coords: Tuple[int, int]):
    """
    Use to scale WHERE to blit an item, not the SIZE of it. (0, 0) is the top left corner of the pygame_gui managed window,
    this adds the offset from fullscreen etc. to make it blit in the right place. Not to be confused with ui_scale_offset.
    :param coords: The coordinates to blit to
    :return: The scaled, correctly offset coordinates to blit to.
    """
    return floor(
        coords[0] * scripts.game_structure.screen_settings.screen_scale
        + scripts.game_structure.screen_settings.offset[0]
    ), floor(
        coords[1] * scripts.game_structure.screen_settings.screen_scale
        + scripts.game_structure.screen_settings.offset[1]
    )


def update_sprite(cat):
    # First, check if the cat is faded.
    if cat.faded:
        # Don't update the sprite if the cat is faded.
        return

    # apply
    cat.sprite = generate_sprite(cat)
    # update class dictionary
    cat.all_cats[cat.ID] = cat


def clan_symbol_sprite(clan, return_string=False, force_light=False):
    """
    returns the clan symbol for the given clan_name, if no symbol exists then random symbol is chosen
    :param clan: the clan object
    :param return_string: default False, set True if the sprite name string is required rather than the sprite image
    :param force_light: Set true if you want this sprite to override the dark/light mode changes with the light sprite
    """
    if not clan.chosen_symbol:
        possible_sprites = []
        for sprite in sprites.clan_symbols:
            name = sprite.strip("1234567890")
            if f"symbol{clan.name.upper()}" == name:
                possible_sprites.append(sprite)
        if possible_sprites:
            clan.chosen_symbol = choice(possible_sprites)
        else:
            # give random symbol if no matching symbol exists
            print(
                f"WARNING: attempted to return symbol, but there's no clan symbol for {clan.name.upper()}. "
                f"Random chosen."
            )
            clan.chosen_symbol = choice(sprites.clan_symbols)

    if return_string:
        return clan.chosen_symbol
    else:
        return sprites.get_symbol(clan.chosen_symbol, force_light=force_light)


def generate_sprite(
    cat,
    life_state=None,
    scars_hidden=False,
    acc_hidden=False,
    wing_hidden=False,
    always_living=False,
    no_not_working=False,
) -> pygame.Surface:
    """
    Generates the sprite for a cat, with optional arguments that will override certain things.

    :param life_state: sets the age life_stage of the cat, overriding the one set by its age. Set to string.
    :param scars_hidden: If True, doesn't display the cat's scars. If False, display cat scars.
    :param acc_hidden: If True, hide the accessory. If false, show the accessory.
    :param always_living: If True, always show the cat with living lineart
    :param no_not_working: If true, never use the not_working lineart.
                    If false, use the cat.not_working() to determine the no_working art.
    """

    if life_state is not None:
        age = life_state
    else:
        age = cat.age.value

    if always_living:
        dead = False
    else:
        dead = cat.dead
        
    # setting the cat_sprite (bc this makes things much easier)
    if not no_not_working and cat.not_working() and age != 'newborn' and game.config['cat_sprites']['sick_sprites']:
        if age in ['kitten']:
            cat_sprite = str(21)
        elif age in ['adolescent']:
            cat_sprite = str(19)
        else:
            cat_sprite = str(18)
    elif cat.pelt.paralyzed and age != "newborn":
        if age in ["kitten", "adolescent"]:
            cat_sprite = str(17)
        else:
            if cat.pelt.length == "long":
                cat_sprite = str(16)
            else:
                cat_sprite = str(15)
    else:
        if age == "elder" and not game.config["fun"]["all_cats_are_newborn"]:
            age = "senior"

        if game.config["fun"]["all_cats_are_newborn"]:
            cat_sprite = str(cat.pelt.cat_sprites["newborn"])
        else:
            cat_sprite = str(cat.pelt.cat_sprites[age])

    new_sprite = pygame.Surface(
        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA
    )

    # draw base
    new_sprite.blit(sprites.sprites['base' + cat_sprite], (0, 0))

    # generating the sprite
    try:
        # copying kori's awoogen thanks kori (I would've done this route anyway)
        # base, underfur, overfur, markings fade, markings, marking inside
        # i cried typing all of this out lol help me
        color_dict = {
            "solid": {
                "WHITE": [
                    '#eef9fc',
                    '#f6fcf2',
                    '#eef9fc',
                    '#b3c0c4',
                    '#ccdadc',
                    '#D0DEE1'],
                "PALEGREY": [
                    '#c1d5d3',
                    '#D7E0D1',
                    '#C2D5D3',
                    '#788B8B',
                    '#8FA6A6',
                    '#A2B1B0'],
                "SILVER": [
                    '#B6C8CA',
                    '#d8e1d4',
                    '#c1d5d3',
                    '#6f8181',
                    '#90a7a7',
                    '#859A9D'],
                "GREY": [
                    '#92a1a1',
                    '#AFB8AE',
                    '#92A1A1',
                    '#3F514F',
                    '#677a78',
                    '#B1AEB0'],
                "DARKGREY": [
                    '#5b6c6f',
                    '#838d87',
                    '#5b6c6f',
                    '#152220',
                    '#253e3a',
                    '#39484B'],
                "GHOST": [
                    '#3a3f4b',
                    '#5c5e64',
                    '#4D5056',
                    '#66747a',
                    '#515e62',
                    '#4D4E59'],
                "BLACK": [
                    '#2f353a',
                    '#4a4d52',
                    '#2f353a',
                    '#0f121b',
                    '#151922',
                    '#202427'],
                "CREAM": [
                    '#f3d7b4',
                    '#f4e7c9',
                    '#f3d6b2',
                    '#d6a981',
                    '#efbc8e',
                    '#F5CE9A'],
                "PALEGINGER": [
                    '#E7C498',
                    '#E7C69A',
                    '#E5BD92',
                    '#C68B5B',
                    '#DA9C68',
                    '#E8B479'],
                "GOLDEN": [
                    '#EECB84',
                    '#ECD69F',
                    '#E5B374',
                    '#775441',
                    '#CB906F',
                    '#D9A859'],
                "GINGER": [
                    '#F2AE71',
                    '#F4C391',
                    '#F0AC73',
                    '#AC5A2C',
                    '#DB7338',
                    '#DB9355'],
                "DARKGINGER": [
                    '#D2713D',
                    '#E0A67A',
                    '#D1703C',
                    '#6F2E18',
                    '#A34323',
                    '#BC5D2A'],
                "SIENNA": [
                    '#AA583E',
                    '#B36F50',
                    '#A9563D',
                    '#502A2D',
                    '#87413C',
                    '#BA6D4C'],
                "LIGHTBROWN": [
                    '#DAC7A4',
                    '#E6D7B6',
                    '#CEC6B8',
                    '#6F5D46',
                    '#BCA07B',
                    '#C2AF8C'],
                "LILAC": [
                    '#B49890',
                    '#D0BBAC',
                    '#A6A4A5',
                    '#655252',
                    '#8B696B',
                    '#AD898A'],
                "BROWN": [
                    '#A4856C',
                    '#BEAA8D',
                    '#93887E',
                    '#2D221D',
                    '#674F43',
                    '#957961'],
                "GOLDEN-BROWN": [
                    '#A86D59',
                    '#D2A686',
                    '#836B5B',
                    '#432E2C',
                    '#7B5248',
                    '#A86F59'],
                "DARKBROWN": [
                    '#754E3C',
                    '#B09479',
                    '#6C625D',
                    '#130B0A',
                    '#3B2420',
                    '#5F483C'],
                "CHOCOLATE": [
                    '#704642',
                    '#855953',
                    '#484145',
                    '#1E1719',
                    '#5A3134',
                    '#705153'],
                "LAVENDER": [
                    '#C0B8C8',
                    '#F7F6FA',
                    '#B2AAB7',
                    '#92848E',
                    '#ADA1B2',
                    '#CDBFC6'],
                "ASH": [
                    '#272120',
                    '#6C5240',
                    '#090707',
                    '#030202',
                    '#231A19',
                    '#3D312E'],
                "PALECREAM": [
                    '#FFFBF0',
                    '#FFFFFF',
                    '#FFEED8',
                    '#F7D1B5',
                    '#FFF5E6',
                    '#FFFCF3'],
                "DARKLAVENDER": [
                    '#837487', #base
                    '#8B7D8E', #underfur
                    '#5B4F6C', #overfur
                    '#483E5D', #marking fade bottom
                    '#766B83', #markings
                    '#978C92'], #marking inside
                "BEIGE": [
                    '#DDD7D0', #base
                    '#F3EDE8', #underfur
                    '#D6CAC6', #overfur
                    '#A29591', #marking fade bottom
                    '#B3A59D', #markings
                    '#C3B8B1'], #marking inside
                "DUST": [
                    '#BCAF9F', #base
                    '#CDC1B7', #underfur
                    '#9C8F86', #overfur
                    '#665651', #marking fade bottom
                    '#7D6965', #markings
                    '#A1918C'], #marking inside
                "SUNSET": [
                    '#E5A774', #base
                    '#ECB779', #underfur
                    '#E99063', #overfur
                    '#B4513A', #marking fade bottom
                    '#D27958', #markings
                    '#C86763'], #marking inside
                "OLDLILAC": [
                    '#856A6E', #base
                    '#947A7E', #underfur
                    '#77565F', #overfur
                    '#624049', #marking fade bottom
                    '#7B575F', #markings
                    '#876762'], #marking inside
                "GLASS": [
                    '#dbd4d8', #base
                    '#dbd4d8', #underfur
                    '#c8c3c8', #overfur
                    '#f8f5f2', #marking fade bottom
                    '#efebe9', #markings
                    '#e7e3e6'], #marking inside
                "GHOSTBROWN": [
                    '#613227', #base
                    '#603730', #underfur
                    '#472a2a', #overfur
                    '#be907b', #marking fade bottom
                    '#885953', #markings
                    '#714640'], #marking inside
                "GHOSTRED": [
                    '#853521', #base
                    '#9f3f29', #underfur
                    '#652a1f', #overfur
                    '#e6bd9d', #marking fade bottom
                    '#ce864d', #markings
                    '#b65737'], #marking inside
                "COPPER": [
                    '#7c3711', #base
                    '#b4612f', #underfur
                    '#7c3711', #overfur
                    '#36170c', #marking fade bottom
                    '#5b240b', #markings
                    '#62270a'] #marking inside
            },
            "special": {
                "SINGLECOLOUR": {
                    "WHITE": [
                        '#EFFAFC',
                        '#F6FBF9',
                        '#EEF9FC',
                        '#A7B9BF',
                        '#C6D6DB',
                        '#D0DEE1'],
                    "PALEGREY": [
                        '#C6D7D3',
                        '#D7E0D1',
                        '#C2D5D3',
                        '#788B8B',
                        '#8FA6A6',
                        '#A2B1B0'],
                    "SILVER": [
                        '#B6C8CA',
                        '#CAD6C7',
                        '#9FB8BD',
                        '#2C383F',
                        '#4C626D',
                        '#859A9D'],
                    "GREY": [
                        '#92A1A1',
                        '#AFB8AE',
                        '#92A1A1',
                        '#3F514F',
                        '#637674',
                        '#B1AEB0'],
                    "DARKGREY": [
                        '#697879',
                        '#8F978F',
                        '#5B6C6F',
                        '#0B1110',
                        '#223734',
                        '#39484B'],
                    "GHOST": [
                        '#3C404C',
                        '#3A3F4B',
                        '#4D5056',
                        '#5D6B6F',
                        '#515E64',
                        '#4D4E59'],
                    "BLACK": [
                        '#353A42',
                        '#46494E',
                        '#31383F',
                        '#0A0D15',
                        '#141720',
                        '#202427'],
                    "CREAM": [
                        '#F4DAB5',
                        '#F4E8CB',
                        '#F3D7B4',
                        '#D4A57D',
                        '#E9B68B',
                        '#F5CE9A'],
                    "PALEGINGER": [
                        '#E7C498',
                        '#E7C69A',
                        '#E5BD92',
                        '#C68B5B',
                        '#DA9C68',
                        '#E8B479'],
                    "GOLDEN": [
                        '#EECB84',
                        '#ECD69F',
                        '#E5B374',
                        '#775441',
                        '#CB906F',
                        '#D9A859'],
                    "GINGER": [
                        '#F2AE71',
                        '#F4C391',
                        '#F0AC73',
                        '#AC5A2C',
                        '#DB7338',
                        '#DB9355'],
                    "DARKGINGER": [
                        '#D2713D',
                        '#E0A67A',
                        '#D1703C',
                        '#6F2E18',
                        '#A34323',
                        '#BC5D2A'],
                    "SIENNA": [
                        '#AA583E',
                        '#B36F50',
                        '#A9563D',
                        '#502A2D',
                        '#87413C',
                        '#BA6D4C'],
                    "LIGHTBROWN": [
                        '#DAC7A4',
                        '#E6D7B6',
                        '#CEC6B8',
                        '#6F5D46',
                        '#BCA07B',
                        '#C2AF8C'],
                    "LILAC": [
                        '#B49890',
                        '#D0BBAC',
                        '#A6A4A5',
                        '#655252',
                        '#8B696B',
                        '#AD898A'],
                    "BROWN": [
                        '#A4856C',
                        '#BEAA8D',
                        '#93887E',
                        '#2D221D',
                        '#674F43',
                        '#957961'],
                    "GOLDEN-BROWN": [
                        '#A86D59',
                        '#D2A686',
                        '#836B5B',
                        '#432E2C',
                        '#7B5248',
                        '#A86F59'],
                    "DARKBROWN": [
                        '#754E3C',
                        '#B09479',
                        '#6C625D',
                        '#130B0A',
                        '#3B2420',
                        '#5F483C'],
                    "CHOCOLATE": [
                        '#704642',
                        '#855953',
                        '#484145',
                        '#1E1719',
                        '#5A3134',
                        '#705153'],
                    "LAVENDER": [
                        '#C0B8C8',
                        '#F7F6FA',
                        '#B2AAB7',
                        '#92848E',
                        '#ADA1B2',
                        '#CDBFC6'],
                    "ASH": [
                        '#272120',
                        '#6C5240',
                        '#090707',
                        '#030202',
                        '#231A19',
                        '#3D312E'],
                    "PALECREAM": [
                        '#FFFBF0',
                        '#FFFFFF',
                        '#FFEED8',
                        '#F7D1B5',
                        '#FFF5E6',
                        '#FFFCF3'],
                    "DARKLAVENDER": [
                        '#837487', #base
                        '#8B7D8E', #underfur
                        '#5B4F6C', #overfur
                        '#483E5D', #marking fade bottom
                        '#766B83', #markings
                        '#978C92'], #marking inside
                    "BEIGE": [
                        '#DDD7D0', #base
                        '#F3EDE8', #underfur
                        '#D6CAC6', #overfur
                        '#A29591', #marking fade bottom
                        '#B3A59D', #markings
                        '#C3B8B1'], #marking inside
                    "DUST": [
                        '#BCAF9F', #base
                        '#CDC1B7', #underfur
                        '#9C8F86', #overfur
                        '#665651', #marking fade bottom
                        '#7D6965', #markings
                        '#A1918C'], #marking inside
                    "SUNSET": [
                        '#E5A774', #base
                        '#ECB779', #underfur
                        '#E99063', #overfur
                        '#B4513A', #marking fade bottom
                        '#D27958', #markings
                        '#C86763'], #marking inside
                    "OLDLILAC": [
                        '#856A6E', #base
                        '#947A7E', #underfur
                        '#77565F', #overfur
                        '#624049', #marking fade bottom
                        '#7B575F', #markings
                        '#876762'], #marking inside
                    "GLASS": [
                        '#e5e1d6', #base
                        '#efebe9', #underfur
                        '#dedacb', #overfur
                        '#efebe9', #marking fade bottom
                        '#f8f5f2', #markings
                        '#e7e3e6'], #marking inside
                    "GHOSTBROWN": [
                        '#55312b', #base
                        '#5d3229', #underfur
                        '#402629', #overfur
                        '#885953', #marking fade bottom
                        '#be907b', #markings
                        '#714640'], #marking inside
                    "GHOSTRED": [
                        '#863224', #base
                        '#9f3c25', #underfur
                        '#652a21', #overfur
                        '#ce864d', #marking fade bottom
                        '#e6bd9d', #markings
                        '#b65737'], #marking inside
                    "COPPER": [
                        '#97461c', #base
                        '#b35f2d', #underfur
                        '#7c3711', #overfur
                        '#5b240b', #marking fade bottom
                        '#36170c', #markings
                        '#62270a'] #marking inside
                },
                "SMOKE": {
                    "WHITE": [
                        '#ECF4F6',
                        '#F4FBF3',
                        '#ECF4F6',
                        '#C1CDD1',
                        '#C1CDD1',
                        '#C1CDD1'],
                    "PALEGREY": [
                        '#C4D4D1',
                        '#D9E1D1',
                        '#C4D4D1',
                        '#8FA1A1',
                        '#8FA1A1',
                        '#8FA1A1'],
                    "SILVER": [
                        '#ABC0C3',
                        '#D0D7C9',
                        '#ABC0C3',
                        '#4D5256',
                        '#4D5256',
                        '#4D5256'],
                    "GREY": [
                        '#99A5A4',
                        '#BFC4B5',
                        '#99A5A4',
                        '#5B6967',
                        '#5B6967',
                        '#5B6967'],
                    "DARKGREY": [
                        '#687577',
                        '#8F978F',
                        '#687577',
                        '#273534',
                        '#273534',
                        '#273534'],
                    "GHOST": [
                        '#3A3F4B',
                        '#464952',
                        '#3A3F4B',
                        '#6A7E85',
                        '#6A7E85',
                        '#6A7E85'],
                    "BLACK": [
                        '#2F353A',
                        '#4D5055',
                        '#2F353A',
                        '#171B24',
                        '#171B24',
                        '#171B24'],
                    "CREAM": [
                        '#F3D7B3',
                        '#F4E8CB',
                        '#F3D7B3',
                        '#DFB68E',
                        '#DFB68E',
                        '#DFB68E'],
                    "PALEGINGER": [
                        '#E3BC93',
                        '#E7CEAA',
                        '#E3BC93',
                        '#D39D6E',
                        '#D39D6E',
                        '#D39D6E'],
                    "GOLDEN": [
                        '#EDC881',
                        '#ECD49C',
                        '#E4B072',
                        '#906A4C',
                        '#906A4C',
                        '#906A4C'],
                    "GINGER": [
                        '#F2AD70',
                        '#F3CEA3',
                        '#F2AD70',
                        '#C67340',
                        '#C67340',
                        '#C67340'],
                    "DARKGINGER": [
                        '#D1703C',
                        '#E0A67C',
                        '#D1703C',
                        '#994625',
                        '#994625',
                        '#994625'],
                    "SIENNA": [
                        '#A6563E',
                        '#B26E4F',
                        '#9C503B',
                        '#643739',
                        '#643739',
                        '#643739'],
                    "LIGHTBROWN": [
                        '#d3c6ad',
                        '#eadfc0',
                        '#d3c6ad',
                        '#9f9078',
                        '#9f9078',
                        '#9f9078'],
                    "LILAC": [
                        '#b1968f',
                        '#cfbaab',
                        '#a09a9c',
                        '#785f61',
                        '#785f61',
                        '#785f61'],
                    "BROWN": [
                        '#a58f7e',
                        '#af9981',
                        '#998c7d',
                        '#4c3d35',
                        '#4c3d35',
                        '#4c3d35'],
                    "GOLDEN-BROWN": [
                        '#a26855',
                        '#c59577',
                        '#6c4f45',
                        '#483230',
                        '#483230',
                        '#483230'],
                    "DARKBROWN": [
                        '#745e55',
                        '#9a8270',
                        '#745e55',
                        '#2c201c',
                        '#2c201c',
                        '#2c201c'],
                    "CHOCOLATE": [
                        '#654241',
                        '#875b54',
                        '#4e3e42',
                        '#352426',
                        '#352426',
                        '#352426'],
                    "LAVENDER": [ # new colors
                        '#c3bbc7',
                        '#dcd7df',
                        '#aea4b2',
                        '#65617b',
                        '#65617b',
                        '#65617b'],
                    "ASH": [
                        '#32261e',
                        '#574233',
                        '#201815',
                        '#090706',
                        '#090706',
                        '#090706'],
                    "PALECREAM": [
                        '#fae7d0',
                        '#fcf6ef',
                        '#faddbb',
                        '#f3ceab',
                        '#f3ceab',
                        '#f3ceab'],
                    "DARKLAVENDER": [
                        '#897b8b', #base
                        '#aa979d', #underfur
                        '#665a72', #overfur
                        '#4d4260', #marking fade bottom
                        '#4d4260', #markings
                        '#4d4260'], #marking inside
                    "BEIGE": [
                        '#ded6d2', #base
                        '#eee7e1', #underfur
                        '#d6ceca', #overfur
                        '#a99a93', #marking fade bottom
                        '#a99a93', #markings
                        '#a99a93'], #marking inside
                    "DUST": [
                        '#b0a295', #base
                        '#cdc1b7', #underfur
                        '#9d8c7d', #overfur
                        '#4c403b', #marking fade bottom
                        '#4c403b', #markings
                        '#4c403b'], #marking inside
                    "SUNSET": [
                        '#dc9564', #base
                        '#f1c787', #underfur
                        '#d37854', #overfur
                        '#ad5a46', #marking fade bottom
                        '#ad5a46', #markings
                        '#ad5a46'], #marking inside
                    "OLDLILAC": [
                        '#8f6f75', #base
                        '#a19196', #underfur
                        '#7b5a60', #overfur
                        '#442b2f', #marking fade bottom
                        '#442b2f', #markings
                        '#442b2f'], #marking inside
                    "GLASS": [
                        '#d2ccc7', #base
                        '#d9d4cd', #underfur
                        '#d0cac5', #overfur
                        '#e8e4db', #marking fade bottom
                        '#e8e4db', #markings
                        '#e8e4db'], #marking inside
                    "GHOSTBROWN": [
                        '#57322a', #base
                        '#6e3d30', #underfur
                        '#442a2a', #overfur
                        '#b47862', #marking fade bottom
                        '#b47862', #markings
                        '#714640'], #marking inside
                    "GHOSTRED": [
                        '#8c3a22', #base
                        '#973c25', #underfur
                        '#5f2920', #overfur
                        '#d3a36e', #marking fade bottom
                        '#d3a36e', #markings
                        '#b65737'], #marking inside
                    "COPPER": [
                        '#a24c22', #base
                        '#ce894a', #underfur
                        '#71300f', #overfur
                        '#58240b', #marking fade bottom
                        '#58240b', #markings
                        '#62270a'] #marking inside
                },
                "SINGLESTRIPE": {
                    "WHITE": [
                        '#EEF9FC',
                        '#F4FBF4',
                        '#EEF9FC',
                        '#B4D1DB',
                        '#B4D1DB',
                        '#D0DEE1'],
                    "PALEGREY": [
                        '#C2D5D3',
                        '#D9E1D1',
                        '#C1D5D3',
                        '#89A9A2',
                        '#89A9A2',
                        '#A2B1B0'],
                    "SILVER": [
                        '#A6BFC1',
                        '#C5D3C6',
                        '#9FBBC0',
                        '#436A6F',
                        '#436A6F',
                        '#859A9D'],
                    "GREY": [
                        '#94A3A2',
                        '#92A1A1',
                        '#92A1A1',
                        '#324242',
                        '#324242',
                        '#B1AEB0'],
                    "DARKGREY": [
                        '#5E6D70',
                        '#828E8C',
                        '#5B6C6F',
                        '#0C1315',
                        '#0C1315',
                        '#39484B'],
                    "GHOST": [
                        '#3E424E',
                        '#5C5E63',
                        '#3A3F4B',
                        '#8B93A5',
                        '#8B93A5',
                        '#4D4E59'],
                    "BLACK": [
                        '#2F353A',
                        '#3D4247',
                        '#2F353A',
                        '#050708',
                        '#050708',
                        '#202427'],
                    "CREAM": [
                        '#F3D6B2',
                        '#F4E8CB',
                        '#F3D6B2',
                        '#E1A568',
                        '#E1A568',
                        '#F5CE9A'],
                    "PALEGINGER": [
                        '#E7C498',
                        '#E7C69A',
                        '#E5BD92',
                        '#C1763E',
                        '#C1763E',
                        '#E8B479'],
                    "GOLDEN": [
                        '#EBC27D',
                        '#ECD49B',
                        '#E6B576',
                        '#C16A27',
                        '#C16A27',
                        '#D9A859'],
                    "GINGER": [
                        '#F2A96B',
                        '#F4C594',
                        '#F0AC73',
                        '#DB6126',
                        '#DB6126',
                        '#DB9355'],
                    "DARKGINGER": [
                        '#D57D4B',
                        '#E0A67A',
                        '#D1703C',
                        '#9A230A',
                        '#9A230A',
                        '#BC5D2A'],
                    "SIENNA": [
                        '#A9563D',
                        '#B47353',
                        '#A9563D',
                        '#3F2529',
                        '#743A38',
                        '#BA6D4C'],
                    "LIGHTBROWN": [
                        '#DDCCAE',
                        '#E6D7B7',
                        '#D0C6B5',
                        '#9E8867',
                        '#9E8867',
                        '#C2AF8C'],
                    "LILAC": [
                        '#B3968F',
                        '#D0BCAD',
                        '#A6A4A5',
                        '#6E5859',
                        '#8D6B6C',
                        '#AD898A'],
                    "BROWN": [
                        '#AA9682',
                        '#BDA78E',
                        '#93887E',
                        '#4D3625',
                        '#4D3625',
                        '#957961'],
                    "GOLDEN-BROWN": [
                        '#A76B57',
                        '#D2A685',
                        '#886C5D',
                        '#473130',
                        '#795047',
                        '#A86F59'],
                    "DARKBROWN": [
                        '#7A5948',
                        '#927C6A',
                        '#6B5C54',
                        '#311910',
                        '#311910',
                        '#5F483C'],
                    "CHOCOLATE": [
                        '#6E4642',
                        '#875B54',
                        '#4A3F46',
                        '#281E1F',
                        '#513133',
                        '#705153'],
                    "LAVENDER": [
                        '#C8C2CD',
                        '#F7F6FA',
                        '#BEB5C8',
                        '#6C5A6A',
                        '#A798AE',
                        '#CDBFC6'],
                    "ASH": [
                        '#352D2C',
                        '#8E7156',
                        '#090707',
                        '#030202',
                        '#231A1A',
                        '#3D312E'],
                    "PALECREAM": [
                        '#FFFBF0',
                        '#FFFFFF',
                        '#FFEED8',
                        '#EDB690',
                        '#FFDFB9',
                        '#FFFCF3'],
                    "DARKLAVENDER": [
                        '#837487', #base
                        '#767180', #underfur
                        '#6F6576', #overfur
                        '#483E5D', #marking fade bottom
                        '#504B5E', #markings
                        '#978C92'] ,#marking inside
                    "BEIGE": [
                        '#EADFD3', #base
                        '#F3EDE8', #underfur
                        '#D6CAC6', #overfur
                        '#95887E', #marking fade bottom
                        '#9E9284', #markings
                        '#C3B8B1'], #marking inside
                    "DUST": [
                        '#BCAF9F', #base
                        '#CDC1B7', #underfur
                        '#9C8F86', #overfur
                        '#665651', #marking fade bottom
                        '#7D6965', #markings
                        '#A1918C'], #marking inside
                    "SUNSET": [
                        '#DA9E66', #base
                        '#ECB779', #underfur
                        '#DF835A', #overfur
                        '#B4513A', #marking fade bottom
                        '#C86758', #markings
                        '#C86763'], #marking inside
                    "OLDLILAC": [
                        '#856A6E', #base
                        '#947A7E', #underfur
                        '#7C606A', #overfur
                        '#593A43', #marking fade bottom
                        '#754D59', #markings
                        '#876762'], #marking inside
                    "GLASS": [
                        '#cbc5c0', #base
                        '#cbc5c0', #underfur
                        '#c1bcb7', #overfur
                        '#faf8f7', #marking fade bottom
                        '#faf8f7', #markings
                        '#faf8f7'], #marking inside
                    "GHOSTBROWN": [
                        '#552f27', #base
                        '#572f27', #underfur
                        '#422627', #overfur
                        '#a2655f', #marking fade bottom
                        '#a2655f', #markings
                        '#714640'], #marking inside
                    "GHOSTRED": [
                        '#903724', #base
                        '#9f3c25', #underfur
                        '#702c21', #overfur
                        '#d78856', #marking fade bottom
                        '#d78856', #markings
                        '#b65737'], #marking inside
                    "COPPER": [
                        '#93451b', #base
                        '#b76531', #underfur
                        '#682b0d', #overfur
                        '#3a190c', #marking fade bottom
                        '#3a190c', #markings
                        '#62270a'] #marking inside
                }
            },
            
            "bengal": {
                "WHITE": [
                    '#F5F5F5',
                    '#FFFFFF',
                    '#E7E6EB',
                    '#BEBDBE',
                    '#D4D3D3',
                    '#CDCCCE',
                    '#D7D6D6'],
                "PALEGREY": [
                    '#C4C9CE',
                    '#F8F8F5',
                    '#959AA0',
                    '#1A1A20',
                    '#403F4A',
                    '#47494F',
                    '#7D7C81'],
                "SILVER": [
                    '#C0C6CF',
                    '#F8F8F5',
                    '#7D828A',
                    '#43464D',
                    '#5F6571',
                    '#595C64',
                    '#92969C'],
                "GREY": [
                    '#8B919C',
                    '#F2F2DB',
                    '#6B7078',
                    '#43464D',
                    '#666B75',
                    '#53565E',
                    '#939594'],
                "DARKGREY": [
                    '#A0A2A9',
                    '#F8F8F5',
                    '#4F5155',
                    '#1E1E24',
                    '#403F4A',
                    '#1E1E24',
                    '#403F4A'],
                "GHOST": [
                    '#525D65',
                    '#8899A9',
                    '#2F353A',
                    '#0A0D15',
                    '#0F0F12',
                    '#171B24',
                    '#171B24'],
                "BLACK": [
                    '#7E7878',
                    '#C7C3BA',
                    '#35353A',
                    '#0E0E11',
                    '#1E1E24',
                    '#0E0E11',
                    '#1E1E24'],
                "CREAM": [
                    '#F3D6B2',
                    '#FEFDFD',
                    '#EFBC8E',
                    '#D3A17A',
                    '#EFBC8E',
                    '#DCAA82',
                    '#F0CEAF'],
                "PALEGINGER": [
                    '#C4C9CE',
                    '#EBDDD3',
                    '#E2A36F',
                    '#C5875A',
                    '#E2A36F',
                    '#CF9162',
                    '#E3B590'],
                "GOLDEN": [
                    '#EECB83',
                    '#F3ECD9',
                    '#E6B575',
                    '#6C4C3A',
                    '#CD9170',
                    '#98724F',
                    '#D2AB90'],
                "GINGER": [
                    '#F2A96B',
                    '#FFF0B6',
                    '#DB8A51',
                    '#A8582B',
                    '#EF884C',
                    '#BA6A38',
                    '#EEA76D'],
                "DARKGINGER": [
                    '#D37642',
                    '#FFEFB6',
                    '#BD5629',
                    '#6F2E17',
                    '#AC4825',
                    '#8B3C1E',
                    '#9B5837'],
                "SIENNA": [
                    '#AC5D43',
                    '#D4C498',
                    '#A9563D',
                    '#482628',
                    '#743839',
                    '#89433C',
                    '#89433C'],
                "LIGHTBROWN": [
                    '#E0CFAD',
                    '#F8F7F4',
                    '#B4A07E',
                    '#877358',
                    '#BCA07B',
                    '#978366',
                    '#BEA887'],
                "LILAC": [
                    '#B79088',
                    '#DEC3A6',
                    '#AA9F9E',
                    '#654749',
                    '#876162',
                    '#8C7475',
                    '#8C7475'],
                "BROWN": [
                    '#A5856B',
                    '#F3ECDA',
                    '#8D6A4E',
                    '#46362E',
                    '#644C41',
                    '#604839',
                    '#938173'],
                "GOLDEN-BROWN": [
                    '#A26655',
                    '#DECBA5',
                    '#896C5D',
                    '#281B17',
                    '#7F5548',
                    '#65443B',
                    '#6B473D'],
                "DARKBROWN": [
                    '#685E57',
                    '#EAE1C9',
                    '#2F2A27',
                    '#110B0A',
                    '#3B2723',
                    '#110B0A',
                    '#3B2723'],
                "CHOCOLATE": [
                    '#774D48',
                    '#C1A79D',
                    '#473F46',
                    '#241A1C',
                    '#382021',
                    '#523133',
                    '#523133'],
                "LAVENDER": [
                    '#E3DFE7',
                    '#F9FBFF',
                    '#C0B9C0',
                    '#6B5F7A',
                    '#8A829B',
                    '#9D96AB',
                    '#AE9FB2'],
                "ASH": [
                    '#392F2D',
                    '#7D5A4C',
                    '#110D0D',
                    '#030202',
                    '#231A19',
                    '#060404',
                    '#231A19'],
                "PALECREAM": [
                    '#FFFBF0',
                    '#FFFFFF',
                    '#FFF2E0',
                    '#F6D1B6',
                    '#F9DFCD',
                    '#F9DCC8',
                    '#FCEDE4'],
                "DARKLAVENDER": [
                    '#998FA4', #base
                    '#BDBBC3', #underfur
                    '#5A5167', #overfur
                    '#4B3E5A', #marking fade bottom
                    '#837487', #markings
                    '#8E8093', #marking inside
                    '#A49CA7'], #marking inside lower fade
                "BEIGE": [
                    '#F5EDDF', #base
                    '#FFF6EE', #underfur
                    '#E7D8C8', #overfur
                    '#A29591', #marking fade bottom
                    '#E0CBB8', #markings
                    '#B3A59D', #marking inside
                    '#C1AFA1'], #marking inside lower fade
                "DUST": [
                    '#BCAF9F', #base
                    '#CDC1B7', #underfur
                    '#9C8F86', #overfur
                    '#665651', #marking fade bottom
                    '#7D6965', #markings
                    '#837162', #marking inside
                    '#A18C81'], #marking inside lower fade
                "SUNSET": [
                    '#F6D899', #base
                    '#FFFADB', #underfur
                    '#FBC878', #overfur
                    '#E87154', #marking fade bottom
                    '#FFB379', #markings
                    '#F29E46', #marking inside
                    '#F7B14C'], #marking inside lower fade
                "OLDLILAC": [
                    '#856A6E', #base
                    '#BDA5A1', #underfur
                    '#754D59', #overfur
                    '#401F27', #marking fade bottom
                    '#754D59', #markings
                    '#572E39', #marking inside
                    '#8A5E67'], #marking inside lower fade
                "GLASS": [
                    '#d1d1d7', #base
                    '#e9e7e9', #underfur
                    '#bcbbc6', #overfur
                    '#f4f3f3', #marking fade bottom
                    '#f3f2f1', #markings
                    '#eeedee', #marking inside
                    '#f4f3f3'], #marking inside lower fade
                "GHOSTBROWN": [
                    '#4a2a24', #base
                    '#583027', #underfur
                    '#321711', #overfur
                    '#b47b6d', #marking fade bottom
                    '#b47b6d', #markings
                    '#965c4f', #marking inside
                    '#965c4f'], #marking inside lower fade
                "GHOSTRED": [
                    '#823b21', #base
                    '#b96a40', #underfur
                    '#442011', #overfur
                    '#d6ac7a', #marking fade bottom
                    '#ca9053', #markings
                    '#cd9961', #marking inside
                    '#cd9961'], #marking inside lower fade
                "COPPER": [
                    '#b4612f', #base
                    '#f0aa58', #underfur
                    '#6c2c0c', #overfur
                    '#4b200b', #marking fade bottom
                    '#481f0b', #markings
                    '#481f0b', #marking inside
                    '#5c240a'] #marking inside lower fade
            },
            "special_overfur": {
                "DUOTONE": {
                    "WHITE": [
                    '#eef9fc', #base
                    '#f0efec', #underfur
                    '#eef9fc', #overfur
                    '#fffae2', #marking fade bottom
                    '#c5d2d6', #markings
                    '#94a5bd'], #marking fade top
                "PALEGREY": [
                    '#c1d5d3', #base
                    '#dae2d4', #underfur
                    '#90a7a7', #overfur
                    '#a5b2af', #marking fade bottom
                    '#90a7a7', #markings
                    '#676975'], #marking fade top
                "SILVER": [
                    '#d7e1e6', #base
                    '#c8d3c9', #underfur
                    '#7f9397', #overfur
                    '#a89e9a', #marking fade bottom
                    '#89a9a8', #markings
                    '#424f63'], #marking fade top
                "GREY": [
                    '#92a1a1', #base
                    '#e6e5da', #underfur
                    '#566a6f', #overfur
                    '#fff9ef', #marking fade bottom
                    '#92a1a1', #markings
                    '#262f35'], #marking fade top
                "DARKGREY": [
                    '#495659', #base
                    '#8c96a6', #underfur
                    '#494c5c', #overfur
                    '#a5b2c6', #marking fade bottom
                    '#494c5c', #markings
                    '#110e1c'], #marking fade top
                "GHOST": [
                    '#3a3f4b', #base
                    '#5e5e76', #underfur
                    '#392835', #overfur
                    '#3a3f4b', #marking fade bottom
                    '#312d46', #markings
                    '#68767c'], #marking fade top
                "BLACK": [
                    '#2f353a', #base
                    '#4a4d52', #underfur
                    '#150c32', #overfur
                    '#141821', #marking fade bottom
                    '#100f21', #markings
                    '#221c2e'], #marking fade top
                "CREAM": [
                    '#f6e4c4', #base
                    '#fffaef', #underfur
                    '#f6dfc0', #overfur
                    '#ffffff', #marking fade bottom
                    '#f1c69e', #markings
                    '#d68278'], #marking fade top
                "PALEGINGER": [
                    '#e5bd92', #base
                    '#ebdcbb', #underfur
                    '#d49564', #overfur
                    '#ede6c8', #marking fade bottom
                    '#d69a68', #markings
                    '#903348'], #marking fade top
                "GOLDEN": [
                    '#e6b475', #base
                    '#edd69e', #underfur
                    '#c2896a', #overfur
                    '#a3613d', #marking fade bottom
                    '#93481f', #markings
                    '#3f212c'], #marking fade top
                "GINGER": [
                    '#f4bd87', #base
                    '#f7deb4', #underfur
                    '#a76b56', #overfur
                    '#ffe3b1', #marking fade bottom
                    '#e09b74', #markings
                    '#702e2b'], #marking fade top
                "DARKGINGER": [
                    '#d98e62', #base
                    '#f0c695', #underfur
                    '#8c3a1e', #overfur
                    '#d46538', #marking fade bottom
                    '#8c3a1e', #markings
                    '#7c0831'], #marking fade top
                "SIENNA": [
                    '#a9563d', #base
                    '#e1cbaf', #underfur
                    '#693637', #overfur
                    '#b57056', #marking fade bottom
                    '#b57056', #markings
                    '#320d12'], #marking fade top
                "LIGHTBROWN": [
                    '#ddcdb0', #base
                    '#eae0c0', #underfur
                    '#d1cabc', #overfur
                    '#d6d1cd', #marking fade bottom
                    '#b08c81', #markings
                    '#594945'], #marking fade top
                "LILAC": [
                    '#c69f96', #base
                    '#e3d5ce', #underfur
                    '#a8a1a1', #overfur
                    '#ac9d9b', #marking fade bottom
                    '#a07175', #markings
                    '#908487'], #marking fade top
                "BROWN": [
                    '#846a59', #base
                    '#c1aa94', #underfur
                    '#776558', #overfur
                    '#99756c', #marking fade bottom
                    '#4c2929', #markings
                    '#2f1b18'], #marking fade top
                "GOLDEN-BROWN": [
                    '#a56b58', #base
                    '#d2b58a', #underfur
                    '#c19477', #overfur
                    '#724c44', #marking fade bottom
                    '#724c44', #markings
                    '#593c38'], #marking fade top
                "DARKBROWN": [
                    '#685b54', #base
                    '#856a58', #underfur
                    '#856a58', #overfur
                    '#34201c', #marking fade bottom
                    '#52342f', #markings
                    '#150a14'], #marking fade top
                "CHOCOLATE": [
                    '#744945', #base
                    '#936259', #underfur
                    '#5b4244', #overfur
                    '#dda48e', #marking fade bottom
                    '#5b3133', #markings
                    '#1b1719'], #marking fade top
                "LAVENDER": [
                    '#c1b9c9', #base
                    '#f3f1f6', #underfur
                    '#92848e', #overfur
                    '#a69cb3', #marking fade bottom
                    '#352820', #markings
                    '#6a6c83'], #marking fade top
                "ASH": [
                    '#795942', #base
                    '#0f0b09', #underfur
                    '#0a0808', #overfur
                    '#684f3e', #marking fade bottom
                    '#352820', #markings
                    '#0a0808'], #marking fade top
                "PALECREAM": [
                    '#fffcf1', #base
                    '#fffcf1', #underfur
                    '#fffcf1', #overfur
                    '#e3eaed', #marking fade bottom
                    '#f8d2b6', #markings
                    '#ca908e'], #marking fade top
                "DARKLAVENDER": [
                    '#87798b', #base
                    '#aaa1b9', #underfur
                    '#713576', #overfur
                    '#725a73', #marking fade bottom
                    '#483e5d', #markings
                    '#574069'], #marking fade top
                "BEIGE": [
                    '#ded8d1', #base
                    '#ffffff', #underfur
                    '#b0a395', #overfur
                    '#d6b895', #marking fade bottom
                    '#bdb4a9', #markings
                    '#80776d'], #marking fade top
                "DUST": [
                    '#bfb2a3', #base
                    '#f0e4e3', #underfur
                    '#a68c8f', #overfur
                    '#ad8d83', #marking fade bottom
                    '#837075', #markings
                    '#463a36'], #marking fade top
                "SUNSET": [
                    '#edb96f', #base
                    '#ffe2a5', #underfur
                    '#dd9075', #overfur
                    '#cd5d36', #marking fade bottom
                    '#d77c55', #markings
                    '#b9372f'], #marking fade top
                "OLDLILAC": [
                    '#8b7074', #base
                    '#93797d', #underfur
                    '#93797d', #overfur
                    '#7c4e55', #marking fade bottom
                    '#764653', #markings
                    '#59263b'], #marking fade top
                "GLASS": [
                    '#dbd4d8', #base
                    '#e6e5dd', #underfur
                    '#ffffff', #overfur
                    '#bfc0cd', #marking fade bottom
                    '#8585a0', #markings
                    '#ffffff'], #marking fade top
                "GHOSTBROWN": [
                    '#613227', #base
                    '#3c100c', #underfur
                    '#472a2a', #overfur
                    '#8a5b55', #marking fade bottom
                    '#8d4e41', #markings
                    '#c2927a'], #marking fade top
                "GHOSTRED": [
                    '#672a1f', #base
                    '#bd6939', #underfur
                    '#b26c28', #overfur
                    '#ffdb9b', #marking fade bottom
                    '#db9f62', #markings
                    '#e9c19a'], #marking fade top
                "COPPER": [
                    '#7c3711', #base
                    '#caa172', #underfur
                    '#7c3711', #overfur
                    '#a35121', #marking fade bottom
                    '#603924', #markings
                    '#1f1d1d'] #marking fade top
                }
                
            }
        }
        # to handle the ones with more special coloration - special are for overridden colors for that specific marking and then bengal is just... sharing bengal lol
        # why am I explaining... who knows
        color_type_dict = {
            "special": ["SINGLESTRIPE", "SINGLECOLOUR", "TWOCOLOUR", "SMOKE"],
            "bengal": ["BENGAL", "MARBLED", "BRAIDED"],
            "special_overfur": ["DUOTONE"]
        }

        # base, shadow, pupil
        eye_color_dict = {
            "YELLOW": ['#FFFC8B','#FFD968','#A7861E'],
            "AMBER": ['#F2E085','#DD7631','#DD7631'],
            "HAZEL": ['#FFC68D','#B7C969','#6E7B3A'],
            "PALEGREEN": ['#F3FFAB','#A1DA7C','#A1DA7C'],
            "GREEN": ['#90FE7F','#6AC081','#418573'],
            "BLUE": ['#C3FEFE','#86D6F7','#5074C5'],
            "DARKBLUE": ['#82ABF7','#505FBF','#492495'],
            "PURPLE": ['#F2D7FB','#BC87E1','#6C328F'], # nah thats purple now
            "CYAN": ['#E1FFFF','#8AFEE8','#4699AA'],
            "EMERALD": ['#45C06F','#287770','#134344'],
            "HEATHERBLUE": ['#94B6EF','#B581DD','#B581DD'],
            "SUNLITICE": ['#BAFFFF','#FAEE89','#7A6136'],
            "COPPER": ['#EE9357','#BF6C34','#833F24'],
            "SAGE": ['#A7BE6D','#849653','#454E2B'],
            "COBALT": ['#A0C7F3','#5F6FDB','#2730A2'],
            "SEABLUE": ['#3CECFF','#1B9D9B','#15574A'],
            "DARKMAGENTA": ['#FF6E8A','#A4398D','#462E6A'],
            "IRIDESCENT": ['#E2F9A2','#7EBAE4','#8F55A8'],
            "PINKYELLOW": ['#FFF19F','#FAAED3','#A86083'],
            "GOLD": ['#FFEF84','#EDB459','#CD8342'],
            "GREENYELLOW": ['#FFFFCE','#93DDCB','#48907D'],
            "MIRE": ['#9DE6AC','#80709D','#6E3D69'],
            "DAWN": ['#FFA05F','#694688','#691411'],
            "GARNET": ['#C0006D','#830068','#460054'],
            "PEACH": ['#FFD3A9','#F89373','#BB1A0E'],
            "RED": ['#DF002F','#740C1F','#24014E'],
            "TOXIC": ['#D3E658','#68B033','#752EAD'], 
            "HOLLY": ['#A3D51E','#1FA412','#C11B01'], # hollyleaf
            "ICY": ['#77F1F2','#14B7C8','#CF0A49'], # ashfur 
            "HAZELBLUE": ['#B0EAFF','#D8A576','#825D3A'],
            "SUNSET": ['#F8C74C','#FE874F','#BD29A7'],
            "LILY": ['#FFC3F2','#94E394','#215A2C'],
            "OPAL": ['#F7D6E7','#2BA4FD','#8045B6'],
            "ROSE": ['#B7ECC9','#C87F9E','#854760'],
            "DUSK": ['#FFCBCE','#7CCDDE','#387683'],
            "STARLIGHT": ['#FFEEB1','#6D68EC','#3F3B98'],
        }

        # waeh
        skin_dict = {
            "BLACK": "#5E504B",
            "RED": "#BE4E32",
            "PINK": "#FABFB7",
            "DARKBROWN": "#5A4235",
            "BROWN": "#816559",
            "LIGHTBROWN": "#977A67",
            "DARK": "#24211E",
            "DARKGREY": "#4F4A48",
            "GREY": "#736B64",
            "DARKSALMON": "#A55C43",
            "SALMON": "#D29777",
            "PEACH": "#F9C0A2",
            "DARKMARBLED": "#2A1F1D",
            "MARBLED": "#CC9587",
            "LIGHTMARBLED": "#433130",
            "DARKBLUE": "#3B474C",
            "BLUE": "#4E5B61",
            "LIGHTBLUE": "#5B666B",
        }

        accessory_layers = {
            "middle": 
            ["MAPLE LEAF", "HOLLY", "BLUE BERRIES", "FORGET ME NOTS", "RYE STALK", "CATTAIL", "POPPY", "ORANGE POPPY", "CYAN POPPY", "WHITE POPPY", "PINK POPPY", "BLUEBELLS", "LILY OF THE VALLEY", "SNAPDRAGON", "HERBS", "PETALS", "NETTLE", "HEATHER", "GORSE", "JUNIPER", "RASPBERRY", "LAVENDER", "OAK LEAVES", "CATMINT", "MAPLE SEED", "LAUREL", "BULB WHITE", "BULB YELLOW", "BULB ORANGE", "BULB PINK", "BULB BLUE", "CLOVER", "DAISY", "DRY HERBS", "DRY CATMINT", "DRY NETTLES", "DRY LAURELS", "RED FEATHERS", "BLUE FEATHERS", "JAY FEATHERS", "GULL FEATHERS", "SPARROW FEATHERS", "MOTH WINGS", "ROSY MOTH WINGS", "MORPHO BUTTERFLY", "MONARCH BUTTERFLY", "CICADA WINGS", "BLACK CICADA", "CRIMSONBELL", "BLUEBELL", "YELLOWBELL", "CYANBELL", "REDBELL", "LIMEBELL", "GREENBELL", "RAINBOWBELL", "BLACKBELL", "SPIKESBELL", "WHITEBELL", "PINKBELL", "PURPLEBELL", "MULTIBELL", "INDIGOBELL", "CRIMSONBOW", "BLUEBOW", "YELLOWBOW", "CYANBOW", "REDBOW", "LIMEBOW", "GREENBOW", "RAINBOWBOW", "BLACKBOW", "SPIKESBOW", "WHITEBOW", "PINKBOW", "PURPLEBOW", "MULTIBOW", "INDIGOBOW", "CRIMSONNYLON", "BLUENYLON", "YELLOWNYLON", "CYANNYLON", "REDNYLON", "LIMENYLON", "GREENNYLON", "RAINBOWNYLON", "BLACKNYLON", "SPIKESNYLON", "WHITENYLON", "PINKNYLON", "PURPLENYLON", "MULTINYLON", "INDIGONYLON"],
            "top": 
            []
        }

        wing_scars = []

        # Get colors - makes things easier for later lol

        marking_fade_over = None
        tortie_marking_fade_over = None

        birdwing_markings = cat.pelt.wing_marks

        eye_base_color = eye_color_dict[cat.pelt.eye_colour][0]
        eye_shade_color = eye_color_dict[cat.pelt.eye_colour][1]
        eye_pupil_color = eye_color_dict[cat.pelt.eye_colour][2]
            
        if cat.pelt.eye_colour2 != None:
            eye2_base_color = eye_color_dict[cat.pelt.eye_colour2][0]
            eye2_shade_color = eye_color_dict[cat.pelt.eye_colour2][1]
            eye2_pupil_color = eye_color_dict[cat.pelt.eye_colour2][2]

        if cat.pelt.name not in ['Tortie', 'Calico']:
            # Get dict
            if cat.pelt.name.upper() in color_type_dict['special']:
                color_type = "special"
            elif cat.pelt.name.upper() in color_type_dict['bengal']:
                color_type = "bengal"
            elif cat.pelt.name.upper() in color_type_dict['special_overfur']:
                color_type = "special_overfur"
            else:
                color_type = 0

            if cat.pelt.name.upper() in ['SINGLECOLOUR', 'TWOCOLOUR', 'SINGLE']:
                # because they are essentially the same thing
                cat_marking = "SINGLECOLOUR"
            else:
                cat_marking = cat.pelt.name.upper()

            if color_type == "special":

                base_pelt = color_dict['special'][f'{cat_marking}'][f'{cat.pelt.colour}'][0]
                base_underfur_pelt = color_dict['special'][f'{cat_marking}'][f'{cat.pelt.colour}'][1]
                base_overfur_pelt = color_dict['special'][f'{cat_marking}'][f'{cat.pelt.colour}'][2]
                marking_base = color_dict['special'][f'{cat_marking}'][f'{cat.pelt.colour}'][3]
                marking_fade = color_dict['special'][f'{cat_marking}'][f'{cat.pelt.colour}'][4]
                marking_inside = color_dict['special'][f'{cat_marking}'][f'{cat.pelt.colour}'][5]
            elif color_type == 0:
                base_pelt = color_dict['solid'][f'{cat.pelt.colour}'][0]
                base_underfur_pelt = color_dict['solid'][f'{cat.pelt.colour}'][1]
                base_overfur_pelt = color_dict['solid'][f'{cat.pelt.colour}'][2]
                marking_base = color_dict['solid'][f'{cat.pelt.colour}'][3]
                marking_fade = color_dict['solid'][f'{cat.pelt.colour}'][4]
                marking_inside = color_dict['solid'][f'{cat.pelt.colour}'][5]
            elif color_type == "special_overfur":
                base_pelt = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.colour}'][0]
                base_underfur_pelt = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.colour}'][1]
                base_overfur_pelt = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.colour}'][2]
                marking_fade = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.colour}'][3]
                marking_base = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.colour}'][4]
                marking_fade_over = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.colour}'][5]
            else:
                base_pelt = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][0]
                base_underfur_pelt = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][1]
                base_overfur_pelt = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][2]
                marking_base = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][3]
                marking_fade = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][4]
                marking_inside = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][5]
                marking_inside_fade = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][6]
        else:
            # Get dict
            if cat.pelt.tortiebase.upper() in color_type_dict['special']:
                color_type = "special"
            elif cat.pelt.tortiebase.upper() in color_type_dict['bengal']:
                color_type = "bengal"
            elif cat.pelt.tortiebase.upper() in color_type_dict['special_overfur']:
                color_type = "special_overfur"
            else:
                color_type = 0

            # Get dict of tortie
            if cat.pelt.tortiepattern.upper() in color_type_dict['special']:
                tortie_color_type = "special"
            elif cat.pelt.tortiepattern.upper() in color_type_dict['bengal']:
                tortie_color_type = "bengal"
            elif cat.pelt.tortiepattern.upper() in color_type_dict['special_overfur']:
                tortie_color_type = "special_overfur"
            else:
                tortie_color_type = 0
            
            if cat.pelt.tortiebase.upper() in ['SINGLECOLOUR', 'TWOCOLOUR', 'SINGLE']:
                # because they are essentially the same thing
                cat_marking = "SINGLECOLOUR"
            else:
                cat_marking = cat.pelt.tortiebase.upper()
            
            if cat.pelt.tortiepattern.upper() in ['SINGLECOLOUR', 'TWOCOLOUR', 'SINGLE']:
                # because they are essentially the same thing
                tortie_pattern = "SINGLECOLOUR"
            else:
                tortie_pattern = cat.pelt.tortiepattern.upper()

            if color_type == "special":

                base_pelt = color_dict['special'][f'{cat_marking}'][f'{cat.pelt.colour}'][0]
                base_underfur_pelt = color_dict['special'][f'{cat_marking}'][f'{cat.pelt.colour}'][1]
                base_overfur_pelt = color_dict['special'][f'{cat_marking}'][f'{cat.pelt.colour}'][2]
                marking_base = color_dict['special'][f'{cat_marking}'][f'{cat.pelt.colour}'][3]
                marking_fade = color_dict['special'][f'{cat_marking}'][f'{cat.pelt.colour}'][4]
                marking_inside = color_dict['special'][f'{cat_marking}'][f'{cat.pelt.colour}'][5]
            elif color_type == 0:
                base_pelt = color_dict['solid'][f'{cat.pelt.colour}'][0]
                base_underfur_pelt = color_dict['solid'][f'{cat.pelt.colour}'][1]
                base_overfur_pelt = color_dict['solid'][f'{cat.pelt.colour}'][2]
                marking_base = color_dict['solid'][f'{cat.pelt.colour}'][3]
                marking_fade = color_dict['solid'][f'{cat.pelt.colour}'][4]
                marking_inside = color_dict['solid'][f'{cat.pelt.colour}'][5]
            elif color_type == "special_overfur":
                base_pelt = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.colour}'][0]
                base_underfur_pelt = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.colour}'][1]
                base_overfur_pelt = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.colour}'][2]
                marking_fade = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.colour}'][3]
                marking_base = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.colour}'][4]
                marking_fade_over = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.colour}'][5]
            else:
                base_pelt = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][0]
                base_underfur_pelt = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][1]
                base_overfur_pelt = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][2]
                marking_base = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][3]
                marking_fade = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][4]
                marking_inside = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][5]
                marking_inside_fade = color_dict[f'{color_type}'][f'{cat.pelt.colour}'][6]

            if tortie_color_type == "special":
                tortie_base_pelt = color_dict['special'][f'{tortie_pattern}'][f'{cat.pelt.tortiecolour}'][0]
                tortie_base_underfur_pelt = color_dict['special'][f'{tortie_pattern}'][f'{cat.pelt.tortiecolour}'][1]
                tortie_base_overfur_pelt = color_dict['special'][f'{tortie_pattern}'][f'{cat.pelt.tortiecolour}'][2]
                tortie_marking_base = color_dict['special'][f'{tortie_pattern}'][f'{cat.pelt.tortiecolour}'][3]
                tortie_marking_fade = color_dict['special'][f'{tortie_pattern}'][f'{cat.pelt.tortiecolour}'][4]
                tortie_marking_inside = color_dict['special'][f'{tortie_pattern}'][f'{cat.pelt.tortiecolour}'][5]
            elif tortie_color_type == 0:
                tortie_base_pelt = color_dict['solid'][f'{cat.pelt.tortiecolour}'][0]
                tortie_base_underfur_pelt = color_dict['solid'][f'{cat.pelt.tortiecolour}'][1]
                tortie_base_overfur_pelt = color_dict['solid'][f'{cat.pelt.tortiecolour}'][2]
                tortie_marking_base = color_dict['solid'][f'{cat.pelt.tortiecolour}'][3]
                tortie_marking_fade = color_dict['solid'][f'{cat.pelt.tortiecolour}'][4]
                tortie_marking_inside = color_dict['solid'][f'{cat.pelt.tortiecolour}'][5]
            elif tortie_color_type == "special_overfur":
                tortie_base_pelt = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.tortiecolour}'][0]
                tortie_base_underfur_pelt = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.tortiecolour}'][1]
                tortie_base_overfur_pelt = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.tortiecolour}'][2]
                tortie_marking_fade = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.tortiecolour}'][3]
                tortie_marking_base = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.tortiecolour}'][4]
                tortie_marking_fade_over = color_dict['special_overfur'][f'{cat_marking}'][f'{cat.pelt.tortiecolour}'][5]
            else:
                tortie_base_pelt = color_dict[f'{tortie_color_type}'][f'{cat.pelt.tortiecolour}'][0]
                tortie_base_underfur_pelt = color_dict[f'{tortie_color_type}'][f'{cat.pelt.tortiecolour}'][1]
                tortie_base_overfur_pelt = color_dict[f'{tortie_color_type}'][f'{cat.pelt.tortiecolour}'][2]
                tortie_marking_base = color_dict[f'{tortie_color_type}'][f'{cat.pelt.tortiecolour}'][3]
                tortie_marking_fade = color_dict[f'{tortie_color_type}'][f'{cat.pelt.tortiecolour}'][4]
                tortie_marking_inside = color_dict[f'{tortie_color_type}'][f'{cat.pelt.tortiecolour}'][5]
                tortie_marking_inside_fade = color_dict[f'{tortie_color_type}'][f'{cat.pelt.tortiecolour}'][6]
        

        # draw pelt
        base_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
        base_tint.fill(base_pelt)
        new_sprite.blit(base_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        
        # draw overlays
        underfur_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
        underfur_tint.fill(base_underfur_pelt)

        overfur_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
        overfur_tint.fill(base_overfur_pelt)
        
        markings_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
        markings_tint.fill(marking_base)

        mark_fade_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
        mark_fade_tint.fill(marking_fade)

        if marking_fade_over:
            mark_fade_over_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
            mark_fade_over_tint.fill(marking_fade_over)

        if cat_marking in ['BENGAL', 'MARBLED', 'BRAIDED']:
            underfur = sprites.sprites['underfur' + 'BENGAL' + cat_sprite].copy()
            underfur.blit(underfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        elif cat_marking in ['SINGLESTRIPE', 'DUOTONE']:
            underfur = sprites.sprites['underfur' + 'SOLID' + cat_sprite].copy()
            underfur.blit(underfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        elif cat_marking in ['SINGLECOLOUR']:
            underfur = sprites.sprites['underfur' + 'BASIC' + cat_sprite].copy()
            underfur.blit(underfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        elif cat_marking in ['SMOKE']:
            underfur = sprites.sprites['underfur' + 'SMOKE' + cat_sprite].copy()
            underfur.blit(underfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        else:
            underfur = sprites.sprites['underfur' + 'TABBY' + cat_sprite].copy()
            underfur.blit(underfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)


        new_sprite.blit(underfur, (0, 0))
            

        if cat_marking in ['BENGAL', 'MARBLED', 'BRAIDED']:
            overfur = sprites.sprites['overfur' + 'BENGAL' + cat_sprite].copy()
            overfur.blit(overfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        elif cat_marking in ['SINGLESTRIPE', 'DUOTONE']:
            overfur = sprites.sprites['overfur' + 'SOLID' + cat_sprite].copy()
            overfur.blit(overfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        elif cat_marking in ['SINGLECOLOUR', 'SMOKE']:
            overfur = sprites.sprites['overfur' + 'BASIC' + cat_sprite].copy()
            overfur.blit(overfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        else:
            overfur = sprites.sprites['overfur' + 'TABBY' + cat_sprite].copy()
            overfur.blit(overfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        new_sprite.blit(overfur, (0, 0))

        # draw markings

        if cat_marking not in ['SINGLECOLOUR', 'TWOCOLOUR', 'SINGLE']:
            markings = sprites.sprites['markings' + cat_marking + cat_sprite].copy().convert_alpha()
            markings.blit(markings_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

            # uh...
            if cat_marking in ['BENGAL', 'MARBLED', 'BRAIDED']:
                mark_fade = sprites.sprites['underfur' + 'BENGAL' + cat_sprite].copy()
                mark_fade.blit(mark_fade_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            
            elif cat_marking in ['DUOTONE']:
                mark_fade = sprites.sprites['overfur' + 'SOLID' + cat_sprite].copy()
                mark_fade.blit(mark_fade_over_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

            elif cat_marking in ['SINGLESTRIPE']:
                mark_fade = sprites.sprites['overfur' + 'SOLID' + cat_sprite].copy()
                mark_fade.blit(mark_fade_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
                
            else:
                mark_fade = sprites.sprites['underfur' + 'BASIC' + cat_sprite].copy()
                mark_fade.blit(mark_fade_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

            markings.blit(mark_fade, (0, 0))

            if cat_marking in ['DUOTONE']:
                
                mark_fade_under = sprites.sprites['underfur' + 'SOLID' + cat_sprite].copy()
                mark_fade_under.blit(mark_fade_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                markings.blit(mark_fade_under, (0,0))

            markings.blit(sprites.sprites['markings' + cat_marking + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            if cat_marking in ['SOKOKE', 'MARBLED', 'BENGAL', 'ROSETTE', 'MASKED', 'BRAIDED']:
                markings_inside_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                markings_inside_tint.fill(marking_inside)

                markings_inside = sprites.sprites['markinside' + cat_marking + cat_sprite].copy().convert_alpha()
                markings_inside.blit(markings_inside_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                # i am thirsty i should get water
                if cat_marking in ['BENGAL', 'MARBLED', 'BRAIDED']:
                    markings_inside_fade = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                    markings_inside_fade.fill(marking_inside_fade)

                    mark_inside_fade = sprites.sprites['underfur' + 'BENGAL' + cat_sprite].copy()
                    mark_inside_fade.blit(markings_inside_fade, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                    mark_inside_fade.blit(sprites.sprites['underfur' + 'BENGAL' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                    markings_inside.blit(mark_inside_fade, (0, 0))

                    mark_inside_fade.blit(sprites.sprites['markinside' + cat_marking + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                    markings_inside.blit(mark_inside_fade, (0, 0))
                
                markings_inside.blit(sprites.sprites['markinside' + cat_marking + cat_sprite], (0,0), special_flags=pygame.BLEND_RGBA_MULT)
                markings.blit(markings_inside, (0, 0))
        
            # appear.
            new_sprite.blit(markings, (0, 0))

        # draw tortie
        if cat.pelt.name in ['Tortie', 'Calico']:
            patches = sprites.sprites["tortiemask" + cat.pelt.pattern + cat_sprite].copy()

            tortie_base_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
            tortie_base_tint.fill(tortie_base_pelt)

            # draw base
            patches.blit(tortie_base_tint, (0,0), special_flags=pygame.BLEND_RGB_MULT)
            
            # draw overlays aa
            tortie_underfur_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
            tortie_underfur_tint.fill(tortie_base_underfur_pelt)

            tortie_overfur_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
            tortie_overfur_tint.fill(tortie_base_overfur_pelt)

            if tortie_pattern in ['BENGAL', 'MARBLED', 'BRAIDED']:
                tortie_underfur = sprites.sprites['underfur' + 'BENGAL' + cat_sprite].copy()
                tortie_underfur.blit(tortie_underfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                tortie_underfur.blit(sprites.sprites['underfur' + 'BENGAL' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            elif tortie_pattern in ['SINGLESTRIPE', 'DUOTONE']:
                tortie_underfur = sprites.sprites['underfur' + 'SOLID' + cat_sprite].copy()
                tortie_underfur.blit(tortie_underfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                tortie_underfur.blit(sprites.sprites['underfur' + 'SOLID' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            elif tortie_pattern in ['SINGLECOLOUR']:
                tortie_underfur = sprites.sprites['underfur' + 'BASIC' + cat_sprite].copy()
                tortie_underfur.blit(tortie_underfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                tortie_underfur.blit(sprites.sprites['underfur' + 'BASIC' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            elif tortie_pattern in ['SMOKE']:
                tortie_underfur = sprites.sprites['underfur' + 'SMOKE' + cat_sprite].copy()
                tortie_underfur.blit(tortie_underfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                tortie_underfur.blit(sprites.sprites['underfur' + 'SMOKE' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            else:
                tortie_underfur = sprites.sprites['underfur' + 'TABBY' + cat_sprite].copy()
                tortie_underfur.blit(tortie_underfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                tortie_underfur.blit(sprites.sprites['underfur' + 'TABBY' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            patches.blit(tortie_underfur, (0, 0))
                

            if tortie_pattern in ['BENGAL', 'MARBLED', 'BRAIDED']:
                tortie_overfur = sprites.sprites['overfur' + 'BENGAL' + cat_sprite].copy()
                tortie_overfur.blit(tortie_overfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                tortie_overfur.blit(sprites.sprites['overfur' + 'BENGAL' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            elif tortie_pattern in ['SINGLESTRIPE', 'DUOTONE']:
                tortie_overfur = sprites.sprites['overfur' + 'SOLID' + cat_sprite].copy()
                tortie_overfur.blit(tortie_overfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                tortie_overfur.blit(sprites.sprites['overfur' + 'SOLID' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            elif tortie_pattern in ['SINGLECOLOUR']:
                tortie_overfur = sprites.sprites['overfur' + 'BASIC' + cat_sprite].copy()
                tortie_overfur.blit(tortie_overfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                tortie_overfur.blit(sprites.sprites['overfur' + 'BASIC' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            else:
                tortie_overfur = sprites.sprites['overfur' + 'TABBY' + cat_sprite].copy()
                tortie_overfur.blit(tortie_overfur_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                tortie_overfur.blit(sprites.sprites['overfur' + 'TABBY' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            patches.blit(tortie_overfur, (0, 0))

            # draw markings

            if tortie_pattern not in ['SINGLECOLOUR', 'TWOCOLOUR', 'SINGLE']:
                tortie_markings_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tortie_markings_tint.fill(tortie_marking_base)

                tortie_mark_fade_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tortie_mark_fade_tint.fill(tortie_marking_fade)

                if tortie_marking_fade_over:
                    tortie_mark_fade_over_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                    tortie_mark_fade_over_tint.fill(tortie_marking_fade_over)

                tortie_markings = sprites.sprites['markings' + cat.pelt.tortiepattern.upper() + cat_sprite].copy().convert_alpha()
                tortie_markings.blit(tortie_markings_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                # uh...
                if cat.pelt.tortiepattern.upper() in ['BENGAL', 'MARBLED', 'BRAIDED']:
                    tortie_mark_fade = sprites.sprites['underfur' + 'BENGAL' + cat_sprite].copy()
                    tortie_mark_fade.blit(tortie_mark_fade_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                    tortie_mark_fade.blit(sprites.sprites['underfur' + 'BENGAL' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                elif cat.pelt.tortiepattern.upper() in ['DUOTONE']:
                    tortie_mark_fade = sprites.sprites['overfur' + 'SOLID' + cat_sprite].copy()
                    tortie_mark_fade.blit(mark_fade_over_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                    tortie_mark_fade.blit(sprites.sprites['overfur' + 'SOLID' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                elif cat.pelt.tortiepattern.upper() in ['SINGLESTRIPE']:
                    tortie_mark_fade = sprites.sprites['overfur' + 'SOLID' + cat_sprite].copy()
                    tortie_mark_fade.blit(tortie_mark_fade_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                    tortie_mark_fade.blit(sprites.sprites['overfur' + 'SOLID' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    
                else:
                    tortie_mark_fade = sprites.sprites['underfur' + 'BASIC' + cat_sprite].copy()
                    tortie_mark_fade.blit(tortie_mark_fade_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                    tortie_mark_fade.blit(sprites.sprites['underfur' + 'BASIC' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                tortie_markings.blit(tortie_mark_fade, (0, 0))

                if cat.pelt.tortiepattern.upper() in ['DUOTONE']:
                
                    tortie_mark_fade_under = sprites.sprites['underfur' + 'SOLID' + cat_sprite].copy()
                    tortie_mark_fade_under.blit(mark_fade_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                    tortie_markings.blit(mark_fade_under, (0,0))

                tortie_markings.blit(sprites.sprites['markings' + cat.pelt.tortiepattern.upper() + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                if cat.pelt.tortiepattern.upper() in ['SOKOKE', 'MARBLED', 'BENGAL', 'ROSETTE', 'MASKED', 'BRAIDED']:
                    tortie_markings_inside_tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                    tortie_markings_inside_tint.fill(tortie_marking_inside)

                    tortie_markings_inside = sprites.sprites['markinside' + cat.pelt.tortiepattern.upper() + cat_sprite].copy().convert_alpha()
                    tortie_markings_inside.blit(tortie_markings_inside_tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                    # my eyes are dry - inside markings
                    if cat.pelt.tortiepattern.upper() in ['BENGAL', 'MARBLED', 'BRAIDED']:
                        tortie_markings_inside_fade = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                        tortie_markings_inside_fade.fill(tortie_marking_inside_fade)
                        

                        tortie_mark_inside_fade = sprites.sprites['underfur' + 'BENGAL' + cat_sprite].copy()
                        tortie_mark_inside_fade.blit(tortie_markings_inside_fade, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

                        tortie_mark_inside_fade.blit(sprites.sprites['underfur' + 'BENGAL' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                        tortie_markings_inside.blit(tortie_mark_inside_fade, (0, 0))

                        tortie_mark_inside_fade.blit(sprites.sprites['markinside' + cat_marking + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                        tortie_markings_inside.blit(tortie_mark_inside_fade, (0, 0))
                        
                    tortie_markings_inside.blit(sprites.sprites['markinside' + cat.pelt.tortiepattern.upper() + cat_sprite], (0,0), special_flags=pygame.BLEND_RGBA_MULT)
                    tortie_markings.blit(tortie_markings_inside, (0, 0))
        
                # appear.
                patches.blit(tortie_markings, (0, 0))

            # *microwave.sfx*
            patches.blit(sprites.sprites["tortiemask" + cat.pelt.pattern + cat_sprite], (0,0), special_flags=pygame.BLEND_RGBA_MULT)

            new_sprite.blit(patches, (0, 0))

        # TINTS
        if (
                cat.pelt.tint != "none"
                and cat.pelt.tint in sprites.cat_tints["tint_colours"]
        ):
            # Multiply with alpha does not work as you would expect - it just lowers the alpha of the
            # entire surface. To get around this, we first blit the tint onto a white background to dull it,
            # then blit the surface onto the sprite with pygame.BLEND_RGB_MULT
            tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
            tint.fill(tuple(sprites.cat_tints["tint_colours"][cat.pelt.tint]))
            new_sprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        if (
                cat.pelt.tint != "none"
                and cat.pelt.tint in sprites.cat_tints["dilute_tint_colours"]
        ):
            tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
            tint.fill(tuple(sprites.cat_tints["dilute_tint_colours"][cat.pelt.tint]))
            new_sprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # draw white patches
        if cat.pelt.white_patches is not None:
            white_patches = sprites.sprites[
                "white" + cat.pelt.white_patches + cat_sprite
                ].copy()

            # Apply tint to white patches.
            if (
                    cat.pelt.white_patches_tint != "none"
                    and cat.pelt.white_patches_tint
                    in sprites.white_patches_tints["tint_colours"]
            ):
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(
                    tuple(
                        sprites.white_patches_tints["tint_colours"][
                            cat.pelt.white_patches_tint
                        ]
                    )
                )
                white_patches.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

            new_sprite.blit(white_patches, (0, 0))

        # draw vit & points

        if cat.pelt.points:
            points = sprites.sprites["white" + cat.pelt.points + cat_sprite].copy()
            if (
                    cat.pelt.white_patches_tint != "none"
                    and cat.pelt.white_patches_tint
                    in sprites.white_patches_tints["tint_colours"]
            ):
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(
                    tuple(
                        sprites.white_patches_tints["tint_colours"][
                            cat.pelt.white_patches_tint
                        ]
                    )
                )
                points.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            new_sprite.blit(points, (0, 0))

        if cat.pelt.vitiligo:
            new_sprite.blit(
                sprites.sprites["white" + cat.pelt.vitiligo + cat_sprite], (0, 0)
            )

        # draw eyes & scars1
        """eyes = sprites.sprites["eyes" + cat.pelt.eye_colour + cat_sprite].copy()
        if cat.pelt.eye_colour2 != None:
            eyes.blit(
                sprites.sprites["eyes2" + cat.pelt.eye_colour2 + cat_sprite], (0, 0)
            )
        new_sprite.blit(eyes, (0, 0))"""

        # prepare tints
        eye_base = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
        eye_base.fill(eye_base_color)

        eye_s = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
        eye_s.fill(eye_shade_color)

        eye_p = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
        eye_p.fill(eye_pupil_color)

        # base
        eyes = sprites.sprites['eyes' + 'base' + cat_sprite].copy()
        eyes.blit(eye_base, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        eyes.blit(sprites.sprites['eyes' + 'base' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # draw eye shade
        eye_shade = sprites.sprites['eyes' + 'shade' + cat_sprite].copy()
        eye_shade.blit(eye_s, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        eye_shade.blit(sprites.sprites['eyes' + 'shade' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # draw pupil
        eye_pupil = sprites.sprites['eyes' + 'pupil' + cat_sprite].copy()
        eye_pupil.blit(eye_p, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        eye_pupil.blit(sprites.sprites['eyes' + 'pupil' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # combine
        eyes.blit(eye_shade, (0, 0))
        eyes.blit(eye_pupil, (0, 0))

        new_sprite.blit(eyes, (0, 0))

        if cat.pelt.eye_colour2 != None:
            # prepare tints
            eye2_base = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
            eye2_base.fill(eye2_base_color)

            eye2_s = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
            eye2_s.fill(eye2_shade_color)

            eye2_p = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
            eye2_p.fill(eye2_pupil_color)

            # base
            eyes2 = sprites.sprites['eyes2' + 'base' + cat_sprite].copy()
            eyes2.blit(eye2_base, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

            eyes2.blit(sprites.sprites['eyes2' + 'base' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # draw eye2 shade
            eye2_shade = sprites.sprites['eyes2' + 'shade' + cat_sprite].copy()
            eye2_shade.blit(eye2_s, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            eye2_shade.blit(sprites.sprites['eyes2' + 'shade' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # draw pupil
            eye2_pupil = sprites.sprites['eyes2' + 'pupil' + cat_sprite].copy()
            eye2_pupil.blit(eye2_p, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            eye2_pupil.blit(sprites.sprites['eyes2' + 'pupil' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # combine
            eyes2.blit(eye2_shade, (0, 0))
            eyes2.blit(eye2_pupil, (0, 0))

            new_sprite.blit(eyes2, (0, 0))

        if not scars_hidden:
            for scar in cat.pelt.scars:
                if scar in cat.pelt.scars1:
                    new_sprite.blit(
                        sprites.sprites["scars" + scar + cat_sprite], (0, 0)
                    )
                if scar in cat.pelt.scars3:
                    new_sprite.blit(
                        sprites.sprites["scars" + scar + cat_sprite], (0, 0)
                    )

        # draw line art
        if game.settings["shaders"] and not dead:
            new_sprite.blit(
                sprites.sprites["shaders" + cat_sprite],
                (0, 0),
                special_flags=pygame.BLEND_RGB_MULT,
            )
            new_sprite.blit(sprites.sprites["lighting" + cat_sprite], (0, 0),
                special_flags=pygame.BLEND_RGB_ADD)

        if not dead:
            new_sprite.blit(sprites.sprites["lines" + cat_sprite], (0, 0))
        elif cat.df:
            new_sprite.blit(sprites.sprites["lineartdf" + cat_sprite], (0, 0))
        elif dead:
            new_sprite.blit(sprites.sprites["lineartdead" + cat_sprite], (0, 0))
        # draw skin and scars2
        blendmode = pygame.BLEND_RGBA_MIN
        new_sprite.blit(sprites.sprites["skin" + cat.pelt.skin + cat_sprite], (0, 0))

        if not scars_hidden:
            for scar in cat.pelt.scars:
                if scar in cat.pelt.scars2:
                    new_sprite.blit(
                        sprites.sprites["scars" + scar + cat_sprite],
                        (0, 0),
                        special_flags=blendmode,
                    )

        # draw accessories top
        if not acc_hidden and cat.pelt.accessory:
            cat_accessories = cat.pelt.accessory
            
            categories = ["collars", "tail_accessories", "body_accessories", "head_accessories"]
            for category in categories:
                for accessory in cat_accessories:
                    if accessory in getattr(Pelt, category) and accessory in accessory_layers["top"]:
                        if accessory in cat.pelt.plant_accessories:
                            new_sprite.blit(
                                sprites.sprites["acc_herbs" + accessory + cat_sprite],
                                (0, 0),
                            )
                        elif accessory in cat.pelt.wild_accessories:
                            new_sprite.blit(
                                sprites.sprites["acc_wild" + accessory + cat_sprite],
                                (0, 0),
                            )
                        elif accessory in cat.pelt.collars:
                            new_sprite.blit(
                                sprites.sprites["collars" + accessory + cat_sprite], (0, 0)
                            )

        # Apply fading fog
        if (
                cat.pelt.opacity <= 97
                and not cat.prevent_fading
                and game.clan.clan_settings["fading"]
                and dead
        ):
            stage = "0"
            if 80 >= cat.pelt.opacity > 45:
                # Stage 1
                stage = "1"
            elif cat.pelt.opacity <= 45:
                # Stage 2
                stage = "2"

            new_sprite.blit(
                sprites.sprites["fademask" + stage + cat_sprite],
                (0, 0),
                special_flags=pygame.BLEND_RGBA_MULT,
            )

            if cat.df:
                temp = sprites.sprites["fadedf" + stage + cat_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp
            else:
                temp = sprites.sprites["fadestarclan" + stage + cat_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp

        # reverse, if assigned so
        if cat.pelt.reverse:
            new_sprite = pygame.transform.flip(new_sprite, True, False)

    except (TypeError, KeyError):
        logger.exception("Failed to load sprite")

        # Placeholder image
        new_sprite = image_cache.load_image(
            f"sprites/error_placeholder.png"
        ).convert_alpha()

    return new_sprite


def apply_opacity(surface, opacity):
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            pixel = list(surface.get_at((x, y)))
            pixel[3] = int(pixel[3] * opacity / 100)
            surface.set_at((x, y), tuple(pixel))
    return surface


# ---------------------------------------------------------------------------- #
#                                     OTHER                                    #
# ---------------------------------------------------------------------------- #


def chunks(L, n):
    return [L[x: x + n] for x in range(0, len(L), n)]


def clamp(value: float, minimum_value: float, maximum_value: float) -> float:
    """
    Takes a value and returns it constrained to a certain range
    :param value: The input value
    :param minimum_value: Lower bound
    :param maximum_value: Upper bound
    :return: Clamped float.
    """
    if value < minimum_value:
        return minimum_value
    elif value > maximum_value:
        return maximum_value
    return value


def is_iterable(y):
    try:
        0 in y
    except TypeError:
        return False


def get_text_box_theme(theme_name=None):
    """Updates the name of the theme based on dark or light mode"""
    if game.settings["dark mode"]:
        return ObjectID("#dark", theme_name)
    else:
        return theme_name


def quit(savesettings=False, clearevents=False):
    """
    Quits the game, avoids a bunch of repeated lines
    """
    if savesettings:
        game.save_settings(None)
    if clearevents:
        game.cur_events_list.clear()
    game.rpc.close_rpc.set()
    game.rpc.update_rpc.set()
    pygame.display.quit()
    pygame.quit()
    if game.rpc.is_alive():
        game.rpc.join(1)
    sys_exit()


resource_directory = "resources/dicts/conditions/"
with open(os.path.normpath(f"{resource_directory}illnesses.json"), "r", encoding="utf-8") as read_file:
    ILLNESSES = ujson.loads(read_file.read())

with open(os.path.normpath(f"{resource_directory}injuries.json"), "r", encoding="utf-8") as read_file:
    INJURIES = ujson.loads(read_file.read())

with open(
        os.path.normpath(f"{resource_directory}permanent_conditions.json"), "r", encoding="utf-8"
) as read_file:
    PERMANENT = ujson.loads(read_file.read())

langs = {"snippet": None, "prey": None}

SNIPPETS = None
PREY_LISTS = None

with open(
        os.path.normpath("resources/dicts/backstories.json"), "r", encoding="utf-8"
) as read_file:
    BACKSTORIES = ujson.loads(read_file.read())
