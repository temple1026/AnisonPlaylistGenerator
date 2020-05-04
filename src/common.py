import mojimoji as moji


def trim(name):
    name = moji.zen_to_han(name)
    name = name.replace("\n", "").replace('\'', '_').replace(" ", "").replace("\x00", "").replace("\"", "")
    return name.lower()
