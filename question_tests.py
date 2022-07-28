# Scratch for testing question code
def reference_semantics():
    """Tests awareness of list mutability"""
    # x = y = [2, 2]
    # x = y = [2]
    # x.append(2)
    x = [2] * 2
    y = x.copy()
    # x = [2, 2]
    # y = x
    a = min(x)
    x.pop()
    x.pop()
    a == min(y)


def mutable_keys():
    """Tests understanding that dict keys cannot be mutable"""
    x = [1, 2]
    # x.pop()
    # x = [str(el) for el in x]
    # hash(x)
    x = tuple(x)
    {x: 1}


mutable_keys()


def tuple_trickery():
    """
    A nasty one

    Tests understanding of mutable object behavior within immutable
    objects
    """
    x = ([1], [2])
    # y = x.copy
    # y = x
    y = (x[0].copy(), x[1].copy())
    # y = (x[0], x[1])
    # y = list(x)
    x[0].pop()
    min(y[0])
