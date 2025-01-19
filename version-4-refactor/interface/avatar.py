import py_avataaars as pa
import random

def get_random_enum(enum_class):
    """Get a random value from an enum class"""
    values = list(enum_class)
    return random.choice(values)

def create_avatar_random(name):
    """
    Create Random Avatar images for the model
    """
    mouths_enum = pa.MouthType
    mouths = [(2,1),(5,6),(10,8)]
    mouths_selected = random.choices(mouths)

    parametres = {
        'style': pa.AvatarStyle.CIRCLE,
        'skin_color': get_random_enum(pa.SkinColor),
        'hair_color': get_random_enum(pa.HairColor),
        'facial_hair_type': get_random_enum(pa.FacialHairType),
        'facial_hair_color': get_random_enum(pa.HairColor),
        'top_type': get_random_enum(pa.TopType),
        'hat_color': get_random_enum(pa.Color),
        'eye_type': get_random_enum(pa.EyesType),
        'eyebrow_type': get_random_enum(pa.EyebrowType),
        'nose_type': get_random_enum(pa.NoseType),
        'accessories_type': get_random_enum(pa.AccessoriesType),
        'clothe_type': get_random_enum(pa.ClotheType),
        'clothe_color': get_random_enum(pa.Color),
        'clothe_graphic_type': get_random_enum(pa.ClotheGraphicType)
    }

    avatar = pa.PyAvataaar(**parametres, mouth_type=mouths_enum(mouths_selected[0][0]))
    avatar.render_png_file(f'./model-avatars/avatar_basic_{name}.png')

    avatar = pa.PyAvataaar(**parametres, mouth_type=mouths_enum(mouths_selected[0][1]))
    avatar.render_png_file(f'./model-avatars/avatar_open_{name}.png')


def create_avatar_basic(name):
    """
    Create avatar images for the model
    """
    mouths_enum = pa.MouthType
    mouths = [(2,1),(5,6),(10,8)]
    mouths_selected = random.choices(mouths)

    avatar = pa.PyAvataaar(
        style=pa.AvatarStyle.CIRCLE,
        skin_color=pa.SkinColor.LIGHT,
        hair_color=pa.HairColor.BROWN,
        facial_hair_type=pa.FacialHairType.DEFAULT,
        facial_hair_color=pa.HairColor.BLACK,
        top_type=pa.TopType.SHORT_HAIR_SHORT_FLAT,
        hat_color=pa.Color.BLACK,
        mouth_type= mouths_enum(mouths_selected[0][0]),
        eye_type=pa.EyesType.DEFAULT,
        eyebrow_type=pa.EyebrowType.DEFAULT,
        nose_type=pa.NoseType.DEFAULT,
        accessories_type=pa.AccessoriesType.DEFAULT,
        clothe_type=pa.ClotheType.GRAPHIC_SHIRT,
        clothe_color=pa.Color.HEATHER,
        clothe_graphic_type=pa.ClotheGraphicType.BAT,
    )
    avatar.render_png_file(f'./model-avatars/avatar_basic_{name}.png')

    avatar = pa.PyAvataaar(
        style=pa.AvatarStyle.CIRCLE,
        skin_color=pa.SkinColor.LIGHT,
        hair_color=pa.HairColor.BROWN,
        facial_hair_type=pa.FacialHairType.DEFAULT,
        facial_hair_color=pa.HairColor.BLACK,
        top_type=pa.TopType.SHORT_HAIR_SHORT_FLAT,
        hat_color=pa.Color.BLACK,
        mouth_type=mouths_enum(mouths_selected[0][1]),
        eye_type=pa.EyesType.DEFAULT,
        eyebrow_type=pa.EyebrowType.DEFAULT,
        nose_type=pa.NoseType.DEFAULT,
        accessories_type=pa.AccessoriesType.DEFAULT,
        clothe_type=pa.ClotheType.GRAPHIC_SHIRT,
        clothe_color=pa.Color.HEATHER,
        clothe_graphic_type=pa.ClotheGraphicType.BAT,
    )
    avatar.render_png_file(f'./model-avatars/avatar_open_{name}.png')