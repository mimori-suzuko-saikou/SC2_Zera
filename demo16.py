def get_fitted_stretched_rect(ref_orig, boundary, target_orig):
    """
    1. 先按参考比例变形
    2. 再等比缩放至触碰边界(Aspect Fit)
    :param ref_orig: 原始参考系 (100, 100)
    :param boundary: 拉伸上限/边界 (262, 258)
    :param target_orig: 想要放大的不定长矩形 (w, h)
    """
    # Step 1: 计算基础拉伸比例 (sx, sy)
    sx_base = boundary[0] / ref_orig[0]
    sy_base = boundary[1] / ref_orig[1]

    # Step 2: 目标矩形经过“初始变形”后的逻辑尺寸
    target_deformed_w = target_orig[0] * sx_base
    target_deformed_h = target_orig[1] * sy_base

    # Step 3: 计算缩放因子 k，使得变形后的矩形适配 boundary
    k = min(boundary[0] / target_deformed_w, boundary[1] / target_deformed_h)

    # Step 4: 计算最终尺寸
    final_w = target_deformed_w * k
    final_h = target_deformed_h * k

    # 计算相对于原始 target_orig 的总面积比
    final_area_ratio = (final_w * final_h) / (target_orig[0] * target_orig[1])

    return {
        "final_dimensions": (round(final_w, 2), round(final_h, 2)),
        "limiting_factor": "Width" if (boundary[0] / target_deformed_w) < (
                    boundary[1] / target_deformed_h) else "Height",
        "total_area_ratio": round(final_area_ratio, 4)
    }


def Margin(size, layout_size):
    x, y = size
    l_x, l_y = layout_size
    if x == l_x:
        Margin_x = 0
    else:
        Margin_x = round(l_x - x) / 2

    if y == l_y:
        Margin_y = 0
    else:
        Margin_y = round(l_y - y) / 2
    return (Margin_x, Margin_y)


def map_coordinate(source_pos, source_size, target_size, margin_size):
    """
    将大地图坐标映射到小地图坐标
    :param source_pos: (x, y) 大地图上的坐标
    :param source_size: (width, height) 大地图的总尺寸
    :param target_size: (width, height) 小地图的总尺寸
    :return: (x, y) 映射后的坐标
    """
    src_x, src_y = source_pos[0] - margin_size[0], source_pos[1] - margin_size[1]
    print("src_x ---25.93920898--", src_x)
    print("src_y ---138.2319336--", src_y)
    src_w, src_h = source_size

    tgt_w, tgt_h = target_size
    print("tgt_w --172--", tgt_w)
    print("tgt_h --180--", tgt_h)

    map_x = src_x * (tgt_w / src_w)
    map_y = src_y * (tgt_h / src_h)
    print("--map_x,map_y--", map_x, map_y)
    return (map_x, map_y)


def map_crood_execute(map_size, camera_size, layout_size, coord, margin_size):
    # 关键修改：将原来的 (262, 257) 替换为 layout_size
    stretched_size = get_fitted_stretched_rect((101, 100), layout_size, (172, 180))['final_dimensions']
    layout_x, layout_y = stretched_size[0], stretched_size[1]
    coord_x, coord_y = coord
    margin_size_x, margin_size_y = margin_size
    x = (coord_x - margin_size_x) / camera_size[0] * layout_x
    y = (coord_y - margin_size_y) / camera_size[1] * layout_y

    test = Margin(stretched_size, layout_size)
    x = test[0] + x
    y = test[1] + y
    return (x, y)


if __name__ == "__main__":
    stretched_size = get_fitted_stretched_rect((101, 100), (262,257), (172,180))['final_dimensions']
    print(stretched_size)