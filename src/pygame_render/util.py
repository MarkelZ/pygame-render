from math import radians, cos, sin


# Convert from 0-255 to 0-1, and also process the different ways
# in which arguments may be given (an int tuple vs four separate ints)
def normalize_color_arguments(R: (int | tuple[int]), G: int, B: int, A: int):
    if isinstance(R, tuple):
        if len(R) == 3:
            R, G, B = R
        elif len(R) == 4:
            R, G, B, A = R
        else:
            raise ValueError(
                'Error: The tuple must contain either RGB or RGBA values.')

    return (R/255., G/255., B/255., A/255.)


# Convert from 0-1 to 0-255
def denormalize_color(col):
    return (int(x * 255) for x in col)


def create_rotated_rect(position, width, height, scale, angle, flip):
    # Scale rect
    w = scale[0] * width
    h = scale[1] * height

    # Rotate rect
    angle_rad = radians(angle)
    cos_a, sin_a = cos(angle_rad), sin(angle_rad)

    half_w, half_h = w / 2, h / 2

    half_w_cos = half_w * cos_a
    half_w_sin = half_w * sin_a
    half_h_cos = half_h * cos_a
    half_h_sin = half_h * sin_a

    p1 = (half_w_cos - half_h_sin, half_w_sin + half_h_cos)
    p2 = (-half_w_cos - half_h_sin, -half_w_sin + half_h_cos)
    p3 = (-half_w_cos + half_h_sin, -half_w_sin - half_h_cos)
    p4 = (half_w_cos + half_h_sin, half_w_sin - half_h_cos)

    # Flip horizontally
    if flip[0]:
        p3, p4 = p4, p3
        p1, p2 = p2, p1

    # Flip vertically
    if flip[1]:
        p2, p3 = p3, p2
        p1, p4 = p4, p1

    # Translate vertices
    x, y = position
    x += half_w
    y += half_h
    ps = [(px + x, py + y) for (px, py) in [p1, p2, p3, p4]]

    return ps


def to_dest_coords(p: tuple[float, float], dest_width: float, dest_height: float):
    return (2. * p[0] / dest_width - 1., 1. - 2. * p[1] / dest_height)


def to_source_coords(p: tuple[float, float], source_width: float, source_height: float):
    return (p[0] / source_width, p[1] / source_height)
