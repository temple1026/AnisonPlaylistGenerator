import mojimoji as moji


def trim(name):
    name = name.replace("\n", "").replace('\'', '_').replace(" ", "").replace("\x00", "").replace("\"", "")
    name = moji.zen_to_han(name)
    return name.lower()
