

# Converted from https://github.com/hgc-tpg/cmssw/blob/13521116bd042e2988ddf3d51fe8c972a84ac88a/Geometry/HGCalCommonData/src/HGCalGeomRotation.cc#L121-L155
def rotate_to_sector0(u, v):
    sector = 0;
    if u > 0 and v >= 0:
        if v < u:
            sector = 0
        else:
            sector = 1
    elif u >= v and v < 0:
        if u >= 0:
            sector = 5;
        else:
            sector = 4;
    else:
        if v > 0:
            sector = 2;
        else:
            sector = 3;

    u0 = u
    v0 = v
    for rot in range(sector):
        u_tmp = v0;
        v_tmp = v0 - u0;
        u0 = u_tmp
        v0 = v_tmp
    return sector,u0,v0
