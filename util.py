def get_legends():
    legends = []
    with open("poke") as f:
        for line in f.readlines():
            legends.append(line.strip())

    return legends