#! /usr/bin/env python3

# Adapted from http://kitchingroup.cheme.cmu.edu/blog/2013/02/18/Nonlinear-curve-fitting/

import glob
import numpy as np
import pandas as pd
from scipy.optimize import leastsq
from pymatgen.io.vasp import Vasprun
from vasppy import Poscar
from vasppy.summary import find_vasp_calculations

def read_data():
    dir_list = find_vasp_calculations()
    data = []
    for d in dir_list:
        try:
            vasprun = Vasprun( d + 'vasprun.xml', parse_potcar_file=False )
        except:
            continue
        poscar = Poscar.from_file( d + 'POSCAR' )
        data.append( np.array( [ poscar.scaling, vasprun.final_structure.volume, vasprun.final_energy ] ) )
    df = pd.DataFrame( data, columns=[ 'scaling', 'volume', 'energy' ] ).sort_values( by='scaling' )
    df = df.reset_index( drop=True )
    df['scaling_factor'] = df.volume / df.scaling**3
    scaling_factor_round = 5
    assert( len( set( df.scaling_factor.round( scaling_factor_round ) ) ) == 1 )
    print( df )
    return df

def murnaghan( vol, e0, b0, bp, v0 ):
    """
    Calculate the energy as a function of volume, using the Murnaghan equation of state
    [Murnaghan, Proc. Nat. Acad. Sci. 30, 244 (1944)]
    https://en.wikipedia.org/wiki/Murnaghan_equation_of_state
    cf. Fu and Ho, Phys. Rev. B 28, 5480 (1983).

    Args:
        vol (float): this volume.
        e0 (float):  energy at the minimum-energy volume, E0.
        b0 (float):  bulk modulus at the minimum-energy volume, B0.
        bp (float):  pressure-derivative of the bulk modulus at the minimum-energy volume, B0'.
        v0 (float):  volume at the minimum-energy volume, V0.
        
    Returns:
        (float): The energy at this volume. 
    """
    energy = e0 + b0 * vol / bp * (((v0 / vol)**bp) / (bp - 1) + 1) - v0 * b0 / (bp - 1.0)
    return energy

def objective( pars, y, x ):
    #we will minimize this function
    err =  y - murnaghan( x, *pars )
    return err

def fit( df ):
    x0 = [ df.energy[0], df.volume[0], 2.0, 16.5] #initial guess of parameters
    plsq = leastsq( objective, x0, args=( df.energy, df.volume ) )
    return plsq

if __name__ == '__main__':
    df = read_data()
    e0, b0, bp, v0 = fit( df )[0]
    print( "E0: {:.4f}".format( e0 ) )
    print( "V0: {:.4f}".format( v0 ) )
    print( "opt. scaling: {:.5f}".format( ( v0 / df.scaling_factor.mean() )**(1/3) ) )
