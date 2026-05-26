""" Niestety nie zdążyłem dodać komentarzy i kilku innych rzeczy, ale program powinien działać bezproblemowo. Miłego korzystania"""

from __future__ import annotations
import random
import msvcrt as mc
import shutil
import sys
import os
from math import prod
import turtle
import textury as txt
from copy import deepcopy
from dataclasses import dataclass, field

"""

▖ ▗ ▘ ▝
▙ ▛ ▜ ▟
▌ ▐
▀ ▄
█ 

"""



ustawienia = None
stan_gry =   None
swiat =      None
gracz =      None




#===================================================================================   Klasy   ===========================================================================================




class Color:
    RESET = "\033[0m"

    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    BRIGHT_BLACK   = "\033[90m"
    BRIGHT_RED     = "\033[91m"
    BRIGHT_GREEN   = "\033[92m"
    BRIGHT_YELLOW  = "\033[93m"
    BRIGHT_BLUE    = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN    = "\033[96m"
    BRIGHT_WHITE   = "\033[97m"

    BOLD = "\033[1m"

@dataclass
class Settings:
    world_size: tuple
    difficulty: int
    seed: int

@dataclass
class GameState:
    first_chunk_tile: tuple = (5, 5)
    deaths:          int = 0
    kills:           int = 0
    path:            list = field(default_factory=list)
    game_status:     str = "active"
    


#=== funkcja generatora ===
def rng(x, y, tag):
    li = ustawienia.seed*733 + x*5651 + y*509 + tag*14771
    return random.Random(li)



class World:
    def __init__(self):
        self.enemies = []
        self.objects = [] #([(Item, ilość)], x, y)
        self.current_chunk = tuple(i // 10 for i in gracz.position)

    def get_biom(self, x, y):
        los = rng(x // 20, y // 20, 1)
        return los.choice(["łąka", "pustynia", "bagno", "tundra"])
    
    def load_chunk(self, pos):
        chunk_coords = ((pos[0]//10)*10, (pos[1]//10)*10)
        chunk = [[] for i in range(10)]
        for i in range(chunk_coords[0], chunk_coords[0]+10):
            for j in range(chunk_coords[1], chunk_coords[1]+10):
                biom = self.get_biom(i, j)
                enemy = next((e for e in self.enemies if e.position == (i, j)), None)
                drop = next((d for d in self.objects if (d[1], d[2]) == (i, j)), None)
                chunk[i-chunk_coords[0]].append((biom, enemy, drop))
        return chunk
    
    def enemy_dies(self, enemy):
        drop = []
        for i in ["right_hand", "left_hand", "helmet", "chestplate", "leggings", "boots"]:
            item = getattr(enemy, i)
            if item and random.random() < 0.1:
                drop.append(item)
        tile = next((i for i in self.objects if (i[1], i[2]) == enemy.position), None)
        if tile:
            item_list = tile[0]
            for i in drop:
                for nr, (item, amount) in enumerate(item_list):
                    if item == i:
                        item_list[nr] = (item, amount + 1)
                        break
                else:
                    item_list.append((item, 1))
        elif drop:
            self.objects.append(([(i, 1) for i in drop], enemy.position[0], enemy.position[1])) 
        gracz.gold += enemy.gold_drop
        self.enemies.remove(enemy)

    def get_enemies_in_chunk(self, chunk_x, chunk_y):
        x = chunk_x * 10
        y = chunk_y * 10
        return [
            e for e in self.enemies
            if x <= e.position[0] < x + 10 and
            y <= e.position[1] < y + 10
        ]
        
                







@dataclass
class Item:
    name: str
    item_slot: str
    price: int
    atk_damage:      int = 1
    atk_range:       str = "short"
    defense:         int = 0
    deflect_chance:  int = 0
    stack_size:      int = 1

@dataclass
class Player:
    name: str
    player_type: str
    position: tuple
    direction:       int = 0
    lives:           int = 3
    hp:              float = 100.0
    max_hp:          float = 100.0
    gold:            int = 0
    dmg_mulitiplier: dict = field(default_factory=dict)
    defense:         int = 0
    eq:              list = field(default_factory=lambda: [None for i in range(20)])
    right_hand:      Item | None = None
    left_hand:       Item | None = None
    helmet:          Item | None = None
    chestplate:      Item | None = None
    leggings:        Item | None = None
    boots:           Item | None = None

    def add_to_eq(self, item, amount):
        if item.stack_size > 1:
            while amount > 0:
                slot = next((nr for nr, slot_item in enumerate(self.eq) if slot_item!=None and slot_item[0] == item and slot_item[1] != slot_item[0].stack_size), None)
                if slot == None:
                    if None not in self.eq:
                        return "full eq"
                    empty = self.eq.index(None)
                    x = min(item.stack_size, amount)
                    self.eq[empty] = [item, x]
                    amount -= x
                else:
                    x = min(item.stack_size - self.eq[slot][1], amount)
                    self.eq[slot][1] += x
                    amount -=x
        else:
            for i in range(amount):
                if None in self.eq:
                    self.eq[self.eq.index(None)] = [item, 1]
                else:
                    return "full eq"
    
    def take_dmg(self, dmg):
        self.hp -= dmg * (1 - 0.01*self.defense)


@dataclass
class Enemy:
    enemy_type: str
    position: tuple
    hp: float
    max_hp: float
    gold_drop: int
    dmg_multiplier: float = 1.0
    defense:         int = 0
    right_hand:      Item | None = None
    left_hand:       Item | None = None
    helmet:          Item | None = None
    chestplate:      Item | None = None
    leggings:        Item | None = None
    boots:           Item | None = None

    def take_dmg(self, dmg):
        self.hp -= dmg * (1 - 0.01*self.defense)
        
    def is_dead(self):
        return self.hp <=0




#=================================================================================== lista itemów ===================================================================================
ITEMY = {
    "common_sword":         Item("zwykły miecz", "right_hand", 3, atk_damage=2),
    "uncommon_sword":       Item("niezwykły miecz", "right_hand", 10, atk_damage=4),
    "rare_sword":           Item("rzadki miecz", "right_hand", 30, atk_damage=7),
    "epic_sword":           Item("epicki miecz", "right_hand", 90, atk_damage=11),
    "mithic_sword":         Item("mityczny miecz", "right_hand", 230, atk_damage=17),
    "legendary_sword":      Item("legendarny miecz", "right_hand", 700, atk_damage=25),
    "elite_sword":          Item("elitarny miecz", "right_hand", 2200, atk_damage=45), 
  
    "common_dagger":        Item("zwykły sztylet", "right_hand", 3, atk_damage=2),
    "uncommon_dagger":      Item("niezwykły sztylet", "right_hand", 8, atk_damage=4),
    "rare_dagger":          Item("rzadki sztylet", "right_hand", 25, atk_damage=6),
    "epic_dagger":          Item("epicki sztylet", "right_hand", 80, atk_damage=10),
    "mithic_dagger":        Item("mityczny sztylet", "right_hand", 200, atk_damage=15),
    "legendary_dagger":     Item("legendarny sztylet", "right_hand", 630, atk_damage=22),
    "elite_dagger":         Item("elitarny sztylet", "right_hand", 2000, atk_damage=40),
       
    "common_shield":        Item("zwykła tarcza", "left_hand", 7, deflect_chance=3),
    "uncommon_shield":      Item("niezwykła tarcza", "left_hand", 8, deflect_chance=6),
    "rare_shield":          Item("rzadka tarcza", "left_hand", 50, deflect_chance=10),
    "epic_shield":          Item("epicka tarcza", "left_hand", 120, deflect_chance=20),
    "mithic_shield":        Item("mityczna tarcza", "left_hand", 300, deflect_chance=30),
    "legendary_shield":     Item("legendarna tarcza", "left_hand", 1000, deflect_chance=45),
    "elite_shield":         Item("elitarna tarcza", "left_hand", 3000, deflect_chance=75),
    "totem_of_undying":     Item("totem nieśmiertelności", "left_hand", 200),
       
    "common_helmet":        Item("zwykły hełm", "helmet", 2, defense=1),
    "uncommon_helmet":      Item("niezwykły hełm", "helmet", 8, defense=2),
    "rare_helmet":          Item("rzadki hełm", "helmet", 25, defense=3),
    "epic_helmet":          Item("epicki hełm", "helmet", 70, defense=5),
    "mithic_helmet":        Item("mityczny hełm", "helmet", 200, defense=9),
    "legendary_helmet":     Item("legendarny hełm", "helmet", 600, defense=14),
    "elite_helmet":         Item("elitarny hełm", "helmet", 1900, defense=20),
   
    "common_chestplate":    Item("zwykły napierśnik", "chestplate", 3, defense=2),
    "uncommon_chestplate":  Item("niezwykły napierśnik", "chestplate", 12, defense=3),
    "rare_chestplate":      Item("rzadki napierśnik", "chestplate", 35, defense=4),
    "epic_chestplate":      Item("epicki napierśnik", "chestplate", 100, defense=6),
    "mithic_chestplate":    Item("mityczny napierśnik", "chestplate", 250, defense=11),
    "legendary_chestplate": Item("legendarny napierśnik", "chestplate", 650, defense=17),
    "elite_chestplate":     Item("elitarny napierśnik", "chestplate", 2200, defense=25),

    "common_leggings":      Item("zwykłe nogawice", "leggings", 3, defense=2),
    "uncommon_leggings":    Item("niezwykłe nogawice", "leggings", 12, defense=3),
    "rare_leggings":        Item("rzadkie nogawice", "leggings", 35, defense=4),
    "epic_leggings":        Item("epickie nogawice", "leggings", 100, defense=6),
    "mithic_leggings":      Item("mityczne nogawice", "leggings", 250, defense=11),
    "legendary_leggings":   Item("legendarne nogawice", "leggings", 650, defense=17),
    "elite_leggings":       Item("elitarne nogawice", "leggings", 2200, defense=25),

    "common_boots":         Item("zwykłe buty", "boots", 2, defense=1),
    "uncommon_boots":       Item("niezwykłe buty", "boots", 8, defense=2),
    "rare_boots":           Item("rzadkie buty", "boots", 25, defense=3),
    "epic_boots":           Item("epickie buty", "boots", 70, defense=5),
    "mithic_boots":         Item("mityczne buty", "boots", 200, defense=9),
    "legendary_boots":      Item("legendarne buty", "boots", 600, defense=14),
    "elite_boots":          Item("elitarne buty", "boots", 1900, defense=20),

    "healing_potion":       Item("mikstura leczenia", "eq", 75),
    "dandelion":            Item("mniszek lekarski", "eq", 10, stack_size=16),
    "strength_potion":      Item("mikstura siły", "eq", 200),
    "cactus":               Item("kaktus", "eq", 7, stack_size=16),
    "resistance_potion":    Item("mikstura odporności", "eq", 200),
    "lily":                 Item("lilia", "eq", 7, stack_size=16),
}




#===================================================================================   Funkcje   =========================================================================================






def wpisywanie(wejscie, wys, sze, inst=str):
    oryginal = wejscie
    sys.stdout.write(f"\033[{wys}A")
    sys.stdout.write(f"\033[{sze+len(wejscie)}G")
    while True:
        key = mc.getwch()
        
        if key == "\r":
            sys.stdout.write("\b \b\n")
            sys.stdout.flush()
            return inst(wejscie)
        if key == "\x1b":
            return oryginal
        if key.lower() == "\x08" and len(wejscie) > 0:
            sys.stdout.write(Color.BRIGHT_YELLOW+"\b   \b\b>\b\b"+Color.RESET)
            wejscie = wejscie[:-1]
        elif isinstance(key, inst) and len(wejscie) < 20:
            sys.stdout.write(Color.BRIGHT_YELLOW+f"{key} >\b\b"+Color.RESET)  
            wejscie = wejscie+key
        sys.stdout.flush()
        

"""
biom = self.get_biom(i, j)
enemy = next((e for e in self.enemies if e.position == (i, j)), None)
drop = next((d for d in self.objects if (d[1], d[2]) == (i, j)), None)
chunk[i-chunk_coords[0]].append((biom, enemy, drop))
"""

def rysuj_mape(chunk, komunikat=""):
    sys.stdout.write("\033[3J\033[2J\033[H"*2 + "\n") # *2 bo nie czyściło wszystkiego
    sys.stdout.write((komunikat.center(90) if komunikat else "")+"\n")
    sys.stdout.write(f"życia: {Color.RED+"❤︎"*gracz.lives+Color.RESET}   |   hp: {round(gracz.hp, 2)}/{gracz.max_hp}   |   złoto: {gracz.gold}   |   biom: {swiat.get_biom(gracz.position[0], gracz.position[1])}   |   seed: {ustawienia.seed}\n")
    sys.stdout.write("╭"+"────────┬"*9+"────────╮\n")
    chunk_x = (gracz.position[0] // 10) * 10
    chunk_y = (gracz.position[1] // 10) * 10
    for nry in range(10):
        for j in range(4):
            for nrx in range(10):
                k = chunk[nrx][nry]
                match k[0]:
                    case "łąka":
                        wypelniacz = "·"
                        biome_color = Color.BRIGHT_GREEN
                    case "pustynia":
                        wypelniacz = "·"
                        biome_color = Color.YELLOW
                    case "bagno":
                        wypelniacz = "~"
                        biome_color = Color.GREEN
                    case "tundra":
                        wypelniacz = "*"
                        biome_color = Color.BRIGHT_WHITE

                if k[2]:        
                    # biom, enemy, ([(Item, ilość)], x, y)
                    if len(k[2][0]) == 1 and k[2][0][0][0] == ITEMY["dandelion"]:
                        tile_txt=txt.pola["mniszek"]
                        detail_color=Color.WHITE
                    elif len(k[2][0]) == 1 and k[2][0][0][0] == ITEMY["cactus"]:
                        tile_txt=txt.pola["kaktus"]
                        detail_color=Color.GREEN
                    elif len(k[2][0]) == 1 and k[2][0][0][0] == ITEMY["lily"]:
                        tile_txt=txt.pola["lilia"]
                        detail_color=Color.BRIGHT_WHITE
                    else:
                        tile_txt=txt.pola["drop"]
                        detail_color=Color.BRIGHT_YELLOW
                else:
                    tile_txt=["        " for z in range(4)]
                    detail_color=Color.WHITE
                
                if (nrx, nry) == tuple(z%10 for z in gracz.position):
                    tekst = txt.gracz[j].replace(" ", biome_color+wypelniacz+Color.RESET)

                elif k[1]:
                    match k[1].enemy_type:
                        case "rycerz":
                            enemy_color = Color.BRIGHT_BLACK
                        case "mumia":
                            enemy_color = Color.YELLOW
                        case "topielec":
                            enemy_color = Color.CYAN
                        case "mrożon":
                            enemy_color = Color.BRIGHT_BLUE

                    if k[2]:
                        tekst = "".join(enemy_color+a+Color.RESET if a != " " else detail_color+b+Color.RESET for a, b in zip(txt.przeciwnik[j], tile_txt[j])).replace(" ", biome_color+wypelniacz+Color.RESET)
                    else:
                        tekst = "".join(enemy_color+z+Color.RESET if z != " " else biome_color+wypelniacz+Color.RESET for z in txt.przeciwnik[j])

                else:
                    tekst = "".join(detail_color+z+Color.RESET if z != " " else biome_color+wypelniacz+Color.RESET for z in tile_txt[j])
                
                if chunk_x + nrx == ustawienia.world_size[0]-5 and chunk_y + nry == 5:
                    tekst = Color.MAGENTA+"████████"+Color.RESET
                
                sys.stdout.write("│"+tekst)
            sys.stdout.write("│\n")
        if nry != 9:
            sys.stdout.write("├"+"────────┼"*9+"────────┤\n")
        else:
            sys.stdout.write("╰"+"────────┴"*9+"────────╯\n")

RZADKOSCI = ["common", "uncommon", "rare", "epic", "mithic", "legendary", "elite"]

def pytanie(tekst):
    sys.stdout.write("\033[3J\033[2J\033[H" * 2)
    sys.stdout.write(tekst + "  (t/n)\n")
    sys.stdout.flush()
    while True:
        key = mc.getwch().lower()
        if key == "t":
            return True
        if key == "n" or key == "\x1b":
            return False

def pobierz_wybrany_przedmiot(wiersz, kolumna):
    if wiersz == 0:
        sloty = ["left_hand", "right_hand", "helmet", "chestplate", "leggings", "boots"]
        if 0 <= kolumna < len(sloty):
            nazwa = sloty[kolumna]
            return ("gear", nazwa, getattr(gracz, nazwa))
        return (None, None, None)

    nr_slotu = (wiersz - 1) * 10 + kolumna
    if 0 <= nr_slotu < len(gracz.eq) and gracz.eq[nr_slotu] is not None:
        return ("eq", nr_slotu, gracz.eq[nr_slotu][0])
    return (None, None, None)

def usun_jeden_wybrany(wiersz, kolumna):
    typ, gdzie, rzecz = pobierz_wybrany_przedmiot(wiersz, kolumna)

    if typ == "gear":
        setattr(gracz, gdzie, None)
        return

    if typ == "eq":
        if gracz.eq[gdzie][1] > 1:
            gracz.eq[gdzie][1] -= 1
        else:
            gracz.eq[gdzie] = None
    
def ekwipunek():
    wiersz = 0
    kolumna = 0

    BG = "\033[103m"
    RESET = Color.RESET

    def pole(tekst, aktywna):
        tekst = f"{tekst[:8]:^8}"
        if aktywna:
            return BG + tekst + RESET
        return tekst

    while True:
        sys.stdout.write("\033[3J\033[2J\033[H" * 2 + "\n\n\n")

        # ===== górny pasek =====
        sys.stdout.write("╭  lewa  |  prawa |  hełm  |napierś.|nogawice|  buty  ╮\n")
        sys.stdout.write("|        " * 6 + "|\n")

        sloty = [
            gracz.left_hand,
            gracz.right_hand,
            gracz.helmet,
            gracz.chestplate,
            gracz.leggings,
            gracz.boots
        ]

        t1 = []
        t2 = []
        t3 = []

        for idx, slot in enumerate(sloty):
            tekst = slot.name if slot else ""
            s1, s2, s3 = (tekst.split(maxsplit=2) + ["", "", ""])[:3]

            if len(s2) > 8:
                s2 = s2[:7] + "."

            aktywna = (wiersz == 0 and kolumna == idx)

            t1.append(pole(s1, aktywna))
            t2.append(pole(s2, aktywna))
            t3.append(pole(s3, aktywna))

        sys.stdout.write("|" + "|".join(t for t in t1) + "|\n")
        sys.stdout.write("|" + "|".join(t for t in t2) + "|\n")
        sys.stdout.write("|" + "|".join(t for t in t3) + "|\n")
        sys.stdout.write("╰" + "────────┴" * 5 + "────────╯\n\n")

        sys.stdout.write("ekwipunek\n")

        # ===== eq =====
        sys.stdout.write("╭" + "────────┬" * 9 + "────────╮\n")

        for r in range(2):
            t1 = []
            t2 = []
            t3 = []
            ile = []

            for c in range(10):
                slot = gracz.eq[r * 10 + c]

                tekst = slot[0].name if slot and slot[0] else ""
                s1, s2, s3 = (tekst.split(maxsplit=2) + ["", "", ""])[:3]

                if len(s2) > 8:
                    s3 = s2[7:] + " " + s3
                    s2 = s2[:7] + "-"

                aktywna = (wiersz == r + 1 and kolumna == c)

                t1.append(pole(s1, aktywna))
                t2.append(pole(s2, aktywna))
                t3.append(pole(s3, aktywna))
                ile.append(pole(str(slot[1]) if slot and slot[1] else "", aktywna))

            sys.stdout.write("|" + "|".join(t for t in t1) + "|\n")
            sys.stdout.write("|" + "|".join(t for t in t2) + "|\n")
            sys.stdout.write("|" + "|".join(t for t in t3) + "|\n")
            sys.stdout.write("|" + "|".join(t for t in ile) + "|\n")

            if r != 1:
                sys.stdout.write("├" + "────────┼" * 9 + "────────┤\n")
            else:
                sys.stdout.write("╰" + "────────┴" * 9 + "────────╯\n")
        sys.stdout.write("u - ulepszanie  o - sprzedaj  x - wyrzuć  p - przetwórz  c - użyj\n")
        sys.stdout.flush()

        key = mc.getwch().lower()

        if key == "w":
            wiersz -= 1
        elif key == "s":
            wiersz += 1
        elif key == "a":
            kolumna -= 1
        elif key == "d":
            kolumna += 1
        elif key == "u":
            typ, gdzie, przedmiot = pobierz_wybrany_przedmiot(wiersz, kolumna)

            if przedmiot:
                klucz = None
                for k, v in ITEMY.items():
                    if v == przedmiot:
                        klucz = k
                        break

                if not klucz:
                    continue

                czesci = klucz.split("_", 1)
                if len(czesci) != 2:
                    continue

                rzadkosc, nazwa = czesci
                if rzadkosc not in RZADKOSCI:
                    continue

                nr = RZADKOSCI.index(rzadkosc)
                if nr >= len(RZADKOSCI) - 1:
                    print("przedmiot ma już maksymalną rzadkość")
                    mc.getwch()
                    continue

                nowy_klucz = RZADKOSCI[nr + 1] + "_" + nazwa
                if nowy_klucz not in ITEMY:
                    print("nie ma wyższej wersji tego przedmiotu")
                    mc.getwch()
                    continue

                koszt = max(1, przedmiot.price * 2)

                if pytanie(f"Ulepszyć {przedmiot.name} za {koszt} gold?"):
                    if gracz.gold < koszt:
                        print("za mało złota")
                        mc.getwch()
                    else:
                        gracz.gold -= koszt
                        nowy = deepcopy(ITEMY[nowy_klucz])

                        if typ == "gear":
                            setattr(gracz, gdzie, nowy)
                        else:
                            gracz.eq[gdzie][0] = nowy
        elif key == "o":
            typ, gdzie, przedmiot = pobierz_wybrany_przedmiot(wiersz, kolumna)

            if przedmiot:
                cena = max(1, przedmiot.price // 2)

                if pytanie(f"Sprzedać {przedmiot.name} za {cena} gold?"):
                    gracz.gold += cena
                    usun_jeden_wybrany(wiersz, kolumna)
        elif key == "x":
            typ, gdzie, przedmiot = pobierz_wybrany_przedmiot(wiersz, kolumna)

            if przedmiot:
                if pytanie(f"Wyrzucić {przedmiot.name}?"):
                    usun_jeden_wybrany(wiersz, kolumna)
        elif key == "p":
            PRZEPISY = [
                (ITEMY["dandelion"],  5,  ITEMY["healing_potion"],    1),
                (ITEMY["cactus"],     16, ITEMY["strength_potion"],   1),
                (ITEMY["lily"],       16, ITEMY["resistance_potion"], 1),
            ]
            wykonano = False
            for skladnik, ilosc_skl, produkt, ilosc_prod in PRZEPISY:
                dostepne = sum(slot[1] for slot in gracz.eq if slot and slot[0] == skladnik)
                if dostepne >= ilosc_skl:
                    do_usuniecia = ilosc_skl
                    for slot in gracz.eq:
                        if slot and slot[0] == skladnik:
                            zabierz = min(slot[1], do_usuniecia)
                            slot[1] -= zabierz
                            do_usuniecia -= zabierz
                            if slot[1] == 0:
                                gracz.eq[gracz.eq.index(slot)] = None
                            if do_usuniecia == 0:
                                break
                    gracz.add_to_eq(deepcopy(produkt), ilosc_prod)
                    wykonano = True
                    break
            if not wykonano:
                print("brak składników do craftowania")
                mc.getwch()

        elif key == "c":
            typ, gdzie, przedmiot = pobierz_wybrany_przedmiot(wiersz, kolumna)
            if przedmiot == ITEMY["healing_potion"]:
                gracz.hp = min(gracz.max_hp, gracz.hp + 50)
                usun_jeden_wybrany(wiersz, kolumna)
            elif przedmiot == ITEMY["strength_potion"]:
                gracz.dmg_mulitiplier["strength_potion"] = 1.5
                usun_jeden_wybrany(wiersz, kolumna)
            elif przedmiot == ITEMY["resistance_potion"]:
                gracz.defense += 20
                usun_jeden_wybrany(wiersz, kolumna)
            elif przedmiot and przedmiot.item_slot in ["right_hand", "left_hand", "helmet", "chestplate", "leggings", "boots"]:
                stary = getattr(gracz, przedmiot.item_slot)
                setattr(gracz, przedmiot.item_slot, przedmiot)
                usun_jeden_wybrany(wiersz, kolumna)
                if stary:
                    gracz.add_to_eq(stary, 1)
            else:
                print("nie można użyć tego przedmiotu")
                mc.getwch()


        elif key in ["\x1b", "q", "e"]:
            return

        if wiersz < 0:
            wiersz = 2
        if wiersz > 2:
            wiersz = 0

        max_kol = 5 if wiersz == 0 else 9
        if kolumna < 0:
            kolumna = max_kol
        if kolumna > max_kol:
            kolumna = 0


def rysuj_turtle():
    skala = 500 / max(ustawienia.world_size)

    ekran = turtle.Screen()
    ekran.title(f"Trasa - {gracz.name}")
    ekran.bgcolor("black")
    ekran.setup(600, 600)

    t = turtle.Turtle()
    t.hideturtle()
    t.speed(0)
    t.pensize(1)

    t.penup()
    t.goto(0, 0)
    t.pendown()
    t.color("gray")
    sx, sy = ustawienia.world_size
    for px, py in [(0,0),(sx*skala,0),(sx*skala,-sy*skala),(0,-sy*skala),(0,0)]:
        t.goto(px - sx*skala/2, py + sy*skala/2)

    t.penup()
    mx = (ustawienia.world_size[0]-5)*skala - sx*skala/2
    my = -(5)*skala + sy*skala/2
    t.goto(mx, my)
    t.color("magenta")
    t.dot(8)
    t.color("magenta")
    t.write("META", font=("Arial", 8, "normal"))

    t.color("cyan")
    t.pensize(1)
    for nr, pos in enumerate(stan_gry.path):
        px = pos[0]*skala - sx*skala/2
        py = -pos[1]*skala + sy*skala/2
        if nr == 0:
            t.penup()
            t.goto(px, py)
            t.color("green")
            t.dot(10)
            t.write(f" start ({pos[0]},{pos[1]})", font=("Arial", 8, "normal"))
            t.color("cyan")
            t.pendown()
        else:
            t.goto(px, py)

    t.penup()
    t.color("red")
    t.dot(8)
    t.write(f" koniec ({gracz.position[0]},{gracz.position[1]})", font=("Arial", 8, "normal"))

    ekran.mainloop()
                

def update():
    komunikat = ""
    koniec = ""

    #=== ekran startowy ===
    sys.stdout.write("\033[3J\033[2J\033[H"*2)
    sys.stdout.write(Color.BRIGHT_YELLOW + "=== POCZĄTEK WYPRAWY ===\n\n" + Color.RESET)
    sys.stdout.write(f"  Bohater:          {gracz.name} ({gracz.player_type})\n")
    sys.stdout.write(f"  Pozycja startowa: x={gracz.position[0]}, y={gracz.position[1]}\n")
    sys.stdout.write(f"  Kierunek:         {gracz.direction}° (N=0, E=90, S=180, W=270)\n")
    sys.stdout.write(f"  HP:               {gracz.hp}/{gracz.max_hp}\n")
    sys.stdout.write(f"  Życia:            {gracz.lives}\n")
    sys.stdout.write(f"  Złoto:            {gracz.gold}\n\n")
    sys.stdout.write(f"  Rozmiar świata:   {ustawienia.world_size[0]}x{ustawienia.world_size[1]}\n")
    sys.stdout.write(f"  Granice:          x: 0–{ustawienia.world_size[0]-1},  y: 0–{ustawienia.world_size[1]-1}\n")
    sys.stdout.write(f"  Trudność:         {['łatwy','średni','trudny'][ustawienia.difficulty]}\n")
    sys.stdout.write(f"  Seed:             {ustawienia.seed}\n\n")
    sys.stdout.write(f"  Cel:              dotrzeć do mety na x={ustawienia.world_size[0]-5}, y=5\n\n")
    sys.stdout.write(Color.BRIGHT_YELLOW + "  Naciśnij dowolny klawisz, aby rozpocząć...\n" + Color.RESET)
    sys.stdout.flush()
    mc.getwch()

    while True:
        rysuj_mape(swiat.load_chunk(gracz.position), komunikat=komunikat or None)
        komunikat = ""
        chunk_enemies = swiat.get_enemies_in_chunk(gracz.position[0]//10, gracz.position[1]//10)
        sys.stdout.flush()
        key = mc.getwch().lower()

        match key:
            case "w":
                gracz.direction = 0
                enemy = next((e for e in swiat.enemies if e.position == (gracz.position[0], gracz.position[1] - 1)), None)
                if enemy:
                    enemy.take_dmg((gracz.right_hand.atk_damage if gracz.right_hand else 1)*prod(gracz.dmg_mulitiplier.values()))
                else:
                    if not (chunk_enemies and gracz.position[1]%10 == 0):
                        gracz.position = (gracz.position[0], gracz.position[1]-1)
                        stan_gry.path.append(gracz.position)
                    else:
                        komunikat = "pokonaj wszystkich przeciwników, aby iść dalej"
                        continue
            case "s":
                gracz.direction = 180
                enemy = next((e for e in swiat.enemies if e.position == (gracz.position[0], gracz.position[1] + 1)), None)
                if enemy:
                    enemy.take_dmg((gracz.right_hand.atk_damage if gracz.right_hand else 1)*prod(gracz.dmg_mulitiplier.values()))
                else:
                    if not (chunk_enemies and gracz.position[1]%10 == 9):
                        gracz.position = (gracz.position[0], gracz.position[1]+1)
                        stan_gry.path.append(gracz.position)
                    else:
                        komunikat = "pokonaj wszystkich przeciwników, aby iść dalej"
                        continue
            case "a":
                gracz.direction = 270
                enemy = next((e for e in swiat.enemies if e.position == (gracz.position[0] - 1, gracz.position[1])), None)
                if enemy:
                    enemy.take_dmg((gracz.right_hand.atk_damage if gracz.right_hand else 1)*prod(gracz.dmg_mulitiplier.values()))
                else:
                    if not (chunk_enemies and gracz.position[0]%10 == 0):
                        gracz.position = (gracz.position[0]-1, gracz.position[1])
                        stan_gry.path.append(gracz.position)
                    else:
                        komunikat = "pokonaj wszystkich przeciwników, aby iść dalej"
                        continue
            case "d":
                gracz.direction = 90
                enemy = next((e for e in swiat.enemies if e.position == (gracz.position[0] + 1, gracz.position[1])), None)
                if enemy:
                    enemy.take_dmg((gracz.right_hand.atk_damage if gracz.right_hand else 1)*prod(gracz.dmg_mulitiplier.values()))
                else:
                    if not (chunk_enemies and gracz.position[0]%10 == 9):
                        gracz.position = (gracz.position[0]+1, gracz.position[1])
                        stan_gry.path.append(gracz.position)
                    else:
                        komunikat = "pokonaj wszystkich przeciwników, aby iść dalej"
                        continue

            case "e":
                ekwipunek()
                continue


        if gracz.position[0] < 0:
            gracz.position = (gracz.position[0]+1, gracz.position[1])
            komunikat = "nie wychodź poza świat"
            continue
        elif gracz.position[1] < 0:
            gracz.position = (gracz.position[0], gracz.position[1]+1)
            komunikat = "nie wychodź poza świat"
            continue
        elif gracz.position[0] >= ustawienia.world_size[0]:
            gracz.position = (gracz.position[0]-1, gracz.position[1])
            komunikat = "nie wychodź poza świat"
            continue
        elif gracz.position[1] >= ustawienia.world_size[1]:
            gracz.position = (gracz.position[0], gracz.position[1]-1)
            komunikat = "nie wychodź poza świat"
            continue

        
        
        

        drop = next((d for d in swiat.objects if (d[1], d[2]) == gracz.position), None)
        if drop:
            for i in drop[0][:]: #([(Item, ilość)], x, y)
                full = gracz.add_to_eq(i[0], i[1])
                if full:
                    komunikat = "pełny ekwipunek"
                    break
                else:
                    drop[0].remove(i)
            if not drop[0]:
                swiat.objects.remove(drop)

        dmg = 0
        for e in swiat.enemies[:]:
            if e.is_dead():
                stan_gry.kills += 1
                swiat.enemy_dies(e)
                continue

            ex, ey = e.position
            gx, gy = gracz.position
            if (ex, ey) == (gx - 1, gy):
                hp_before = deepcopy(gracz.hp)
                gracz.take_dmg((e.right_hand.atk_damage if e.right_hand else 1)*e.dmg_multiplier)
                dmg += hp_before-gracz.hp
            elif (ex, ey) == (gx + 1, gy):
                hp_before = deepcopy(gracz.hp)
                gracz.take_dmg((e.right_hand.atk_damage if e.right_hand else 1)*e.dmg_multiplier)
                dmg += hp_before-gracz.hp
            elif (ex, ey) == (gx, gy + 1):
                hp_before = deepcopy(gracz.hp)
                gracz.take_dmg((e.right_hand.atk_damage if e.right_hand else 1)*e.dmg_multiplier)
                dmg += hp_before-gracz.hp
            elif (ex, ey) == (gx, gy - 1):
                hp_before = deepcopy(gracz.hp)
                gracz.take_dmg((e.right_hand.atk_damage if e.right_hand else 1)*e.dmg_multiplier)
                dmg += hp_before-gracz.hp
        if dmg:
            komunikat = f"straciłeś {round(dmg, 2)} hp"

        los = random.random()
        if los < 0.005:
            komunikat = "Pioruny! Ty i wszyscy przeciwnicy tracicie 10hp"
            gracz.hp -= 10
        elif los < 0.01:
            komunikat = "Bogactwo! Wszyscy przeciwniy wyrzucają więcej złota"
            for i in swiat.enemies:
                i.gold_drop += 10

        if gracz.position == (ustawienia.world_size[0]-5, 5):
            koniec = "Wygrana, doszedłeś do mety"
            break

        if gracz.hp <= 0:
            if gracz.left_hand != ITEMY["totem_of_undying"]:
                stan_gry.deaths += 1
                if gracz.lives > 1:
                    gracz.lives -= 1
                    gracz.hp = gracz.max_hp
                    gracz.position = (4,ustawienia.world_size[1]-5)
                    komunikat = "zginąłeś"
                else:
                    koniec = "Przegrana, straciłeś wszystkie życia"
                    break
            else:
                gracz.hp = gracz.max_hp*0.2

    #=== Podsumowanie ===
    wartosc_eq = sum(
        slot[0].price * slot[1]
        for slot in gracz.eq if slot
    )
    wartosc_gear = sum(
        getattr(gracz, s).price
        for s in ["right_hand", "left_hand", "helmet", "chestplate", "leggings", "boots"]
        if getattr(gracz, s)
    )
    wynik = (
        stan_gry.kills  * 50  +
        gracz.gold      * 2   +
        wartosc_eq              +
        wartosc_gear            -
        stan_gry.deaths * 200
    ) * (2 if "Wygrana" in koniec else 1)

    print("\033[3J\033[2J\033[H"*2)
    print(f"Koniec twojej przygody graczu {gracz.name}")
    print(koniec+"\n")
    print("śmierci:",             stan_gry.deaths)
    print("pokonani przeciwnicy:", stan_gry.kills)
    print("kroki:",               len(stan_gry.path))
    print("złoto:",               gracz.gold)
    print("wartość ekwipunku:",   wartosc_eq + wartosc_gear)
    print("\nWYNIK CAŁKOWITY:",   max(0, wynik))

    rysuj_turtle()
    mc.getch()
    
            





def przypisz(seed, trudnosc, rozmiar_swiata, imie, typ_postaci):
    global ustawienia, stan_gry, swiat, gracz
    try:
        seed = int(seed)
    except Exception:
        seed = random.randint(-999999999, 999999999)
    match rozmiar_swiata:
        case 0:
            rs = (50, 50)
        case 1:
            rs = (100, 100)
        case 2:
            rs = (200, 200)
    ustawienia = Settings(rs, trudnosc, seed)
    random.seed(seed)

    gracz = Player(imie, typ_postaci, (4,rs[1]-5))
    match typ_postaci:
        case "wojownik":
            gracz.max_hp *= 1.2
            gracz.hp = gracz.max_hp
            gracz.right_hand = deepcopy(ITEMY["rare_sword"])
            gracz.left_hand = deepcopy(ITEMY["epic_shield"])
            gracz.helmet = deepcopy(ITEMY["uncommon_helmet"])
            gracz.chestplate = deepcopy(ITEMY["rare_chestplate"])
            gracz.leggings = deepcopy(ITEMY["rare_leggings"])
            gracz.boots = deepcopy(ITEMY["uncommon_boots"])
        case "mnich":
            gracz.right_hand = deepcopy(ITEMY["rare_dagger"])
            gracz.helmet = deepcopy(ITEMY["rare_helmet"])
            gracz.chestplate = deepcopy(ITEMY["uncommon_chestplate"])
            gracz.leggings = deepcopy(ITEMY["uncommon_leggings"])
            gracz.boots = deepcopy(ITEMY["rare_boots"])
            gracz.add_to_eq(deepcopy(ITEMY["healing_potion"]), 2)
        case "zabójca":
            gracz.max_hp *= 0.70
            gracz.hp = gracz.max_hp
            gracz.dmg_mulitiplier["player_type"] = 1.5
            gracz.right_hand = deepcopy(ITEMY["epic_dagger"])
            gracz.left_hand = deepcopy(ITEMY["totem_of_undying"])
            gracz.helmet = deepcopy(ITEMY["uncommon_helmet"])
            gracz.chestplate = deepcopy(ITEMY["common_chestplate"])
            gracz.leggings = deepcopy(ITEMY["common_leggings"])
            gracz.boots = deepcopy(ITEMY["common_boots"])
            



    stan_gry = GameState()
    stan_gry.first_chunk_tile = tuple(i % 10 for i in gracz.position)
    stan_gry.path.append(gracz.position)

    swiat = World()

    #=== tworzenie przeciwników ===
    for i in range(ustawienia.world_size[0]//10):
        for j in range(ustawienia.world_size[1]//10):
            los = rng(i, j, 2)
            for k in range(los.randint(0,2+ustawienia.difficulty)):
                x = los.randint(0,9)
                y = los.randint(0,9)
                biom = swiat.get_biom(x+i*10,y+j*10)
                match biom:
                    case "łąka":
                        typ = "rycerz"
                    case "pustynia":
                        typ = "mumia"
                    case "bagno":
                        typ = "topielec"
                    case "tundra":
                        typ = "mrożon"
                sila = 1+(i*0.2/(ustawienia.world_size[0]/100) + abs((ustawienia.world_size[1]/10)-j)*0.2/(ustawienia.world_size[1]/100))
                hp = float((10+ustawienia.difficulty*5) * sila)
                los2 = rng(x, y, 3)
                zloto = int(los2.randint(15,25)*sila)
                swiat.enemies.append(Enemy(typ, (x+i*10,y+j*10), hp, hp, zloto))

                wrog = swiat.enemies[-1]
                nr_rzadkosci = min(int((sila - 1)*1.5), 6)
                rzadkosc = RZADKOSCI[nr_rzadkosci]

                match typ:
                    case "rycerz":
                        wrog.right_hand  = deepcopy(ITEMY[rzadkosc + "_sword"])
                        wrog.left_hand   = deepcopy(ITEMY[rzadkosc + "_shield"])
                    case "mumia" | "topielec":
                        wrog.right_hand  = deepcopy(ITEMY[rzadkosc + "_dagger"])
                    case "mrożon":
                        wrog.right_hand  = deepcopy(ITEMY[rzadkosc + "_sword"])

                wrog.helmet      = deepcopy(ITEMY[rzadkosc + "_helmet"])
                wrog.chestplate  = deepcopy(ITEMY[rzadkosc + "_chestplate"])
                wrog.leggings    = deepcopy(ITEMY[rzadkosc + "_leggings"])
                wrog.boots       = deepcopy(ITEMY[rzadkosc + "_boots"])

    max_i = ustawienia.world_size[0] // 10 - 1
    max_j = ustawienia.world_size[1] // 10 - 1

    swiat.enemies = [
        e for e in swiat.enemies
        if not (
            (e.position[0] // 10 == 0     and e.position[1] // 10 == max_j) or
            (e.position[0] // 10 == max_i and e.position[1] // 10 == 0    )
        )
    ]

    #=== tworzenie roślin ===
    for i in range(ustawienia.world_size[0]//10):
        for j in range(ustawienia.world_size[1]//10):
            los = rng(i, j, 2)
            for k in range(los.randint(0,4)):
                x = los.randint(0,9)+i*10
                y = los.randint(0,9)+j*10
                biom = swiat.get_biom(x,y)
                match biom:
                    case "łąka":
                        typ = "dandelion"
                    case "pustynia":
                        typ = "cactus"
                    case "bagno":
                        typ = "lily"
                    case "tundra":
                        continue
                swiat.objects.append(([(deepcopy(ITEMY[typ]), los.randint(1,3))], x, y))
    

def utwoz():
    seed = ""
    trudnosc = {"options": ["łatwy", "średni", "trudny"], "index": 0}
    rozmiar_swiata = {"options": ["pomniejszony", "normalny", "powiększony"], "index": 1}
    imie = ""
    typ_postaci = {"options": ["wojownik", "mnich", "zabójca"], "index": 0}
    opcja = 0
    while True:
        sys.stdout.write("\033[3J\033[2J\033[H"*2)
        sys.stdout.write("  Seed: "+ (f"  {seed}  \n" if opcja!=0 else Color.BRIGHT_YELLOW+f"< {seed} >\n"+Color.RESET))
        sys.stdout.write("  Trudność: "+ (f"  {trudnosc['options'][trudnosc['index']]}  \n" if opcja!=1 else Color.BRIGHT_YELLOW+f"< {trudnosc['options'][trudnosc['index']]} >\n" +Color.RESET))
        sys.stdout.write("  Rozmiar świata: "+ (f"  {rozmiar_swiata['options'][rozmiar_swiata['index']]}  \n" if opcja!=2 else Color.BRIGHT_YELLOW+f"< {rozmiar_swiata['options'][rozmiar_swiata['index']]} >\n" +Color.RESET))
        sys.stdout.write("  Imię bohatera: "+ (f"  {imie}  \n" if opcja!=3 else Color.BRIGHT_YELLOW+f"< {imie} >\n"+Color.RESET))
        sys.stdout.write("  Typ postaci: "+ (f"  {typ_postaci['options'][typ_postaci['index']]}  \n" if opcja!=4 else Color.BRIGHT_YELLOW+f"< {typ_postaci['options'][typ_postaci['index']]} >\n" +Color.RESET))
        sys.stdout.write("  kontynuuj\n" if opcja!=5 else Color.BRIGHT_YELLOW+f"< kontynuuj >\n" +Color.RESET)
        sys.stdout.flush()
        key = mc.getwch().lower()
        if key == "w":
            opcja -= 1
        elif key == "s":
            opcja += 1
        elif key == "a":
            match opcja:
                case 1:
                    trudnosc["index"] -= 1
                    if trudnosc["index"] > 2:
                        trudnosc["index"] = 0
                case 2:
                    rozmiar_swiata["index"] -= 1
                    if rozmiar_swiata["index"] > 2:
                        rozmiar_swiata["index"] = 0
                case 4:
                    typ_postaci["index"] -= 1
                    if typ_postaci["index"] > 2:
                        typ_postaci["index"] = 0
        elif key == "d":
            match opcja:
                case 1:
                    trudnosc["index"] += 1
                    if trudnosc["index"] < 0:
                        trudnosc["index"] = 2
                case 2:
                    rozmiar_swiata["index"] += 1
                    if rozmiar_swiata["index"] < 0:
                        rozmiar_swiata["index"] = 2
                case 4:
                    typ_postaci["index"] += 1
                    if typ_postaci["index"] < 0:
                        typ_postaci["index"] = 2
        elif key == "\r":
            match opcja:
                case 0:
                    seed = wpisywanie(seed, 6, 11)
                case 3:
                    imie = wpisywanie(imie, 3, 20)
                case 5:
                    przypisz(seed, trudnosc["index"], rozmiar_swiata["index"], imie, typ_postaci["options"][typ_postaci["index"]])
                    update()
                    break
        
        if opcja < 0:
            opcja = 5
        if opcja > 5:
            opcja = 0






if __name__ == "__main__":
    sys.stdout.write("\033[3J\033[2J\033[H"*2)
    if os.name != "nt":
        print("Wymagane uchomienie na Windows")
        exit()
    #=== sprawdzanie rozmiaru terminala ===
    while True:
        kolu, rzed = shutil.get_terminal_size()
        if kolu < 140 or rzed < 70:
            print(f"Terminal musi mieć wymiary co najmniej 140x70, a aktulnie jest {kolu}x{rzed}")
            print("Powiększ okno terminala lub zwiększ wymiary przytrzymając ctrl i naciskając -")
        else:
            break
        mc.getch()

    
    #=== menu główne ===
    opcja = 0
    while True:
        
        sys.stdout.write("\033[3J\033[2J\033[H"*2)
        sys.stdout.write(Color.BRIGHT_GREEN+Color.BOLD+"DROGA BOHATERA\n\n"+Color.RESET)
        sys.stdout.write("  Nowa gra  \n" if opcja!=0 else Color.BRIGHT_YELLOW+"< Nowa gra >\n"+Color.RESET)
        sys.stdout.write("  Wyjdź  \n"    if opcja!=1 else Color.BRIGHT_YELLOW+"< Wyjdź >\n"   +Color.RESET)
        sys.stdout.flush()
        key = mc.getwch().lower()
        if key == "w":
            opcja -= 1
        elif key == "s":
            opcja += 1
        elif key == "\r":
            match opcja:
                case 0:
                    utwoz()
                case 1:
                    exit()
        
        if opcja < 0:
            opcja = 1
        if opcja > 1:
            opcja = 0

    