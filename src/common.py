import mojimoji as moji

def trim(name):
    name = name.replace("\n", "").replace('\'', '\'\'').replace(" ", " ").replace("\x00", "").replace("\"", "")
    return name

def trim_reverse(name):
    while "\'\'" in name:
        name = name.replace("\'\'", "\'")

    return name
