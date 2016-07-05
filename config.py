
# not sure this is at all useful currently

def load_data():

    raw_data = [line.strip().split() for line in open('i10chicconfig.txt')]
    lengths = []
    for i in raw_data[0][1:]:
        lengths.append(eval(i))
    path = []
    for i in raw_data[1][1:]:
        path.append(eval(i)) # this won't work

    return lengths, path

def positions():

    pos = [0]
    pos.extend(np.cumsum(load_data()[0]))

    return pos
    
def locate_detector():
    return positions()[8]


