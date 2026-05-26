"""
▘ ▝
▖ ▗
▛ ▜
▟ ▙
█ 
▀ ▄
▌ ▐
"""


przeciwnik = [
"   ██   ",
" █▀██▀█ ",
"  ▟██▙  ",
"  █  █  ",
]

gracz = [
"   ██   ",
" ▐▀██▀▌ ",
"  ▗██▖  ",
"  ▐  ▌  ",
]


pola = {
"drop": [
" ✦     ✦",
"    ✦   ",
"✦     ✦ ",
"  ✦    ✦",
],

"mniszek": [
" ✿     ✿",
"    ✿   ",
"✿     ✿ ",
"  ✿    ✿",
],

"kaktus": [
"   ▄    ",
" ▄ █ █  ",
" █▄█▀▀  ",
"   █    ",
],

"lilia": [
" ❃   ❃  ",
" |   /  ",
"❃      ❃",
" \\     |",
],
}

if __name__ == "__main__":
    for i in przeciwnik:
        print(i)
    print()

    for i in gracz:
        print(i)
    print()

    for i in pola["drop"]:
        print(i)
    print()

    for i in pola["mniszek"]:
        print(i)
    print()

    for i in pola["kaktus"]:
        print(i)
    print()

    for i in pola["lilia"]:
        print(i)