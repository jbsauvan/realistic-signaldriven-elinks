#! /usr/bin/env python3

import pandas as pd
from common import rotate_to_sector0, uv2u0v0


def read_module_mapping(file_name):
    df = pd.read_csv(file_name, sep=' ', names=['layer', 'u', 'v', 'modid'])
    df = df[df.modid!=0].set_index(['layer', 'modid'])
    return df

def read_unconstrained_elinks(file_name):
    df = pd.read_csv(file_name, sep=' ', names=['layer', 'modid', 'elinks'])
    df = df[df.modid!=0]
    return df

def read_constrained_elinks(file_name):
    df = pd.read_csv(file_name)
    return df

def module2uv(row, module_mapping):
    if module_mapping.index.isin([(int(row.layer), int(row.modid))]).any():
        return module_mapping.loc[(int(row.layer), int(row.modid))]
    else:
        return pd.Series([np.nan, np.nan], index=['u', 'v'])


def apply_mapping(module_mapping, df):
    dfout = df.copy()
    dfout[['u', 'v']] = dfout.apply(lambda x:module2uv(x,module_mapping), axis=1)
    dfout[['u0', 'v0']] = dfout.apply(uv2u0v0, axis=1)
    dfout = dfout.dropna()
    return dfout

def uv2elinks(row, elinks,capping=-1):
    layer = int(row.layer)
    u = int(row.u)
    v = int(row.v)
    # Rotation is only valid in the CE-E. with wafer centred layers
    sector,u0,v0 = rotate_to_sector0(u, v)
    if layer<=28 and sector>1:
        print('WARNING: sector>1 in the CE-E')
    # Apply the change of elinks only in the CE-E
    if layer<=28 and elinks.index.isin([(layer, u0, v0)]).any():
        elinks = int(elinks.loc[(layer, u0, v0)])
        if capping!=-1:
            elinks = min(elinks, capping)
        return elinks
        #  return 999
    else:
        return row.elinks

def apply_new_links(constrained_elinks, df, capping=-1):
    dfout = df.copy()
    dfout['elinks'] = dfout.apply(lambda x:uv2elinks(x,constrained_elinks,capping=capping), axis=1)
    return dfout


def main(cfg):
    capping = cfg['capping']
    module_mapping = read_module_mapping(cfg['module_mapping'])
    unconstrained_elinks = read_unconstrained_elinks(cfg['elinks_unconstrained'])
    constrained_elinks = read_constrained_elinks(cfg['elinks_constrained'])
    constrained_elinks = constrained_elinks.set_index(['layer', 'u', 'v'])
    unconstrained_elinks = apply_mapping(module_mapping, unconstrained_elinks)
    new_elinks = apply_new_links(constrained_elinks, unconstrained_elinks, capping=capping)
    new_elinks.to_csv(cfg['output'],
            sep=' ', columns=['layer', 'modid', 'elinks'], header=False, index=False)
            #  sep=' ')


if __name__=='__main__':
    import optparse
    import yaml
    parser = optparse.OptionParser()
    parser.add_option("--cfg",type="string", dest="cfg", help="select the path to the parameters file")
    (opt, args) = parser.parse_args()
    cfg_file_name = opt.cfg
    with open(cfg_file_name, 'r') as cfg_file:
        cfg = yaml.safe_load(cfg_file)
    main(cfg)

