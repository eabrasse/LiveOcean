# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 16:02:43 2016

@author: PM5

Module of basic utilities for plotting.  The goal is to make the code in
pfun less cumbersome to write and edit.

"""

# setup
import os
import sys
alp = os.path.abspath('../alpha')
if alp not in sys.path:
    sys.path.append(alp)
import Lfun
Ldir = Lfun.Lstart()
import zrfun
import zfun

import numpy as np

if Ldir['lo_env'] == 'pm_mac': # mac version
    pass
else: # regular (remote, linux) version
    import matplotlib as mpl
    mpl.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.path as mpath
import pandas as pd

def topfig():
    """
    Positions the figure at the top left of the screen, and puts it
    on top of the Spyder window.  Copied from Stack Overflow.
    """
    try:
        figmgr = plt.get_current_fig_manager()
        figmgr.canvas.manager.window.raise_()
        geom = figmgr.window.geometry()
        x,y,dx,dy = geom.getRect()
        figmgr.window.setGeometry(10, 10, dx, dy)
    except AttributeError:
        # this only works, and is only needed, in Spyder
        # so working from the terminal we just skip it.
        pass

def dar(ax):
    """
    Fixes the plot aspect ratio to be locally Cartesian.
    """
    yl = ax.get_ylim()
    yav = (yl[0] + yl[1])/2
    ax.set_aspect(1/np.sin(np.pi*yav/180))

def add_coast(ax, dir0=Ldir['data'], color='k'):
    fn = dir0 + 'coast/coast_pnw.p'
    C = pd.read_pickle(fn)
    ax.plot(C['lon'].values, C['lat'].values, '-', color=color, linewidth=0.5)

def get_coast(dir0=Ldir['data']):
    fn = dir0 + 'coast/coast_pnw.p'
    C = pd.read_pickle(fn)
    lon = C['lon'].values
    lat = C['lat'].values
    return lon, lat

def auto_lims(fld):
    """
    A convenience function for automatically setting color limits.
    Input: a numpy array (masked OK)
    Output: tuple of good-guess colorscale limits for a pcolormesh plot.    
    """
    from warnings import filterwarnings
    filterwarnings('ignore') # skip some warning messages
    flo = np.nanmax([np.nanmean(fld) - 3*np.nanstd(fld), np.nanmin(fld)])
    fhi = np.nanmin([np.nanmean(fld) + 3*np.nanstd(fld), np.nanmax(fld)])
    return (flo, fhi)

def get_units(ds, vn):
    try:
        units = ds[vn].units
    except AttributeError:
        units = ''
    return units

def add_bathy_contours(ax, ds, depth_levs = [], txt=False):
    # this should work with ds being a history file Dataset, or the G dict.
    h = ds['h'][:]
    lon = ds['lon_rho'][:]
    lat = ds['lat_rho'][:]
    c1 = 'k'
    c2 = 'k'
    if len(depth_levs) == 0:
        ax.contour(lon, lat, h, [200], colors=c1, linewidths=0.5)
        ax.contour(lon, lat, h, [2000], colors=c2, linewidths=0.5)
        if txt==True:
            ax.text(.95, .95, '200 m', color=c1,
                    horizontalalignment='right',
                    transform=ax.transAxes)
            ax.text(.95, .92, '2000 m', color=c2,
                    horizontalalignment='right',transform=ax.transAxes)
    else:
        ax.contour(lon, lat, h, depth_levs, colors='g')

def add_map_field(ax, ds, varname, slev=-1, vlims=(), cmap='rainbow',
                  fac=1, alpha=1, do_mask_salish=False):
    cmap = plt.get_cmap(name=cmap)
    if 'lon_rho' in ds[varname].coordinates:
        x = ds['lon_psi'][:]
        y = ds['lat_psi'][:]
        v = ds[varname][0, slev, 1:-1, 1:-1].squeeze()
    elif 'lon_v' in ds[varname].coordinates:
        x = ds['lon_u'][:]
        y = ds['lat_u'][:]
        v = ds[varname][0, slev, :, 1:-1].squeeze()
    elif 'lon_u' in ds[varname].coordinates:
        x = ds['lon_v'][:]
        y = ds['lat_v'][:]
        v = ds[varname][0, slev, 1:-1, :].squeeze()
    if len(vlims) == 0:
        vlims = auto_lims(v)
    
    if do_mask_salish:
        v = mask_salish(v, ds['lon_rho'][1:-1, 1:-1], ds['lat_rho'][1:-1, 1:-1])  
    
    cs = ax.pcolormesh(x, y, v*fac, vmin=vlims[0], vmax=vlims[1], cmap=cmap, alpha=alpha)
    return cs, vlims

def add_velocity_vectors(ax, ds, fn, v_scl=3, v_leglen=0.5, nngrid=80, zlev=0, center=(.7,.05)):
    # v_scl: scale velocity vector (smaller to get longer arrows)
    # v_leglen: m/s for velocity vector legend
    xc = center[0]
    yc = center[1]
    # GET DATA
    G = zrfun.get_basic_info(fn, only_G=True)
    if zlev == 0:
        u = ds['u'][0, -1, :, :].squeeze()
        v = ds['v'][0, -1, :, :].squeeze()
    else:
        zfull_u = get_zfull(ds, fn, 'u')
        zfull_v = get_zfull(ds, fn, 'v')
        u = get_laym(ds, zfull_u, ds['mask_u'][:], 'u', zlev).squeeze()
        v = get_laym(ds, zfull_v, ds['mask_v'][:], 'v', zlev).squeeze()
    # ADD VELOCITY VECTORS
    # set masked values to 0
    ud = u.data; ud[u.mask]=0
    vd = v.data; vd[v.mask]=0
    # create interpolant
    import scipy.interpolate as intp
    ui = intp.interp2d(G['lon_u'][0, :], G['lat_u'][:, 0], ud)
    vi = intp.interp2d(G['lon_v'][0, :], G['lat_v'][:, 0], vd)
    # create regular grid
    aaa = ax.axis()
    daax = aaa[1] - aaa[0]
    daay = aaa[3] - aaa[2]
    axrat = np.cos(np.deg2rad(aaa[2])) * daax / daay
    x = np.linspace(aaa[0], aaa[1], round(nngrid * axrat))
    y = np.linspace(aaa[2], aaa[3], nngrid)
    xx, yy = np.meshgrid(x, y)
    # interpolate to regular grid
    uu = ui(x, y)
    vv = vi(x, y)
    mask = uu != 0
    # plot velocity vectors
    ax.quiver(xx[mask], yy[mask], uu[mask], vv[mask],
        units='y', scale=v_scl, scale_units='y', color='k')
    ax.quiver([xc, xc] , [yc, yc], [v_leglen, v_leglen],
              [v_leglen, v_leglen],
        units='y', scale=v_scl, scale_units='y', color='k',
        transform=ax.transAxes)
    ax.text(xc+.05, yc, str(v_leglen) + ' $ms^{-1}$',
        horizontalalignment='left', transform=ax.transAxes)

def add_windstress_flower(ax, ds, t_scl=0.2, t_leglen=0.1, center=(.85,.25)):
    # ADD MEAN WINDSTRESS VECTOR
    # t_scl: scale windstress vector (smaller to get longer arrows)
    # t_leglen: # Pa for wind stress vector legend
    taux = ds['sustr'][:].squeeze()
    tauy = ds['svstr'][:].squeeze()
    tauxm = taux.mean()
    tauym = tauy.mean()
    x = center[0]
    y = center[1]
    ax.quiver([x, x] , [y, y], [tauxm, tauxm], [tauym, tauym],
        units='y', scale=t_scl, scale_units='y', color='k',
        transform=ax.transAxes)
    tt = 1./np.sqrt(2)
    t_alpha = 0.3
    ax.quiver([x, x] , [y, y],
        t_leglen*np.array([0,tt,1,tt,0,-tt,-1,-tt]),
        t_leglen*np.array([1,tt,0,-tt,-1,-tt,0,tt]),
        units='y', scale=t_scl, scale_units='y', color='k', alpha=t_alpha,
        transform=ax.transAxes)
    ax.text(x, y-.13,'Windstress',
        horizontalalignment='center', alpha=t_alpha, transform=ax.transAxes)
    ax.text(x, y-.1, str(t_leglen) + ' Pa',
        horizontalalignment='center', alpha=t_alpha, transform=ax.transAxes)

def add_info(ax, fn, fs=12):
    # put info on plot
    T = zrfun.get_basic_info(fn, only_T=True)
    ax.text(.95, .075, T['tm'].strftime('%Y-%m-%d'),
        horizontalalignment='right' , verticalalignment='bottom',
        transform=ax.transAxes, fontsize=fs)
    ax.text(.95, .065, T['tm'].strftime('%H:%M') + ' UTC',
        horizontalalignment='right', verticalalignment='top',
        transform=ax.transAxes, fontsize=fs)
    ax.text(.06, .04, fn.split('/')[-3],
        verticalalignment='bottom', transform=ax.transAxes,
        rotation='vertical', fontsize=fs)

def get_aa(ds):
    x = ds['lon_psi'][0,:]
    y = ds['lat_psi'][:,0]
    aa = [x[0], x[-1], y[0], y[-1]]
    return aa
    
def get_aa_ex(ds):
    x = ds['lon_psi_ex'][0,:]
    y = ds['lat_psi_ex'][:,0]
    aa = [x[0], x[-1], y[0], y[-1]]
    return aa

def get_zfull(ds, fn, which_grid):
    # get zfull field on "which_grid" ('rho', 'u', or 'v')
    G, S, T = zrfun.get_basic_info(fn)
    zeta = 0 * ds.variables['zeta'][:].squeeze()
    zr_mid = zrfun.get_z(G['h'], zeta, S, only_rho=True)
    zr_bot = -G['h'].reshape(1, G['M'], G['L']).copy()
    zr_top = zeta.reshape(1, G['M'], G['L']).copy()
    zfull0 = make_full((zr_bot, zr_mid, zr_top))
    if which_grid == 'rho':
        zfull = zfull0
    elif which_grid == 'u':
        zfull = zfull0[:, :, 0:-1] + np.diff(zfull0, axis=2)/2
    elif which_grid == 'v':
        zfull = zfull0[:, 0:-1, :] + np.diff(zfull0, axis=1)/2
    return zfull

def get_laym(ds, zfull, mask, vn, zlev):
    # make the layer
    fld_mid = ds[vn][:].squeeze()
    fld = make_full((fld_mid,))
    zlev_a = zlev * np.ones(1)
    lay = get_layer(fld, zfull, zlev_a)
    lay[mask == False] = np.nan
    laym = np.ma.masked_where(np.isnan(lay), lay)
    return laym

def get_layer(fld, zfull, which_z):
    """
    Creates a horizontal slice through a 3D ROMS data field.  It is very fast
    because of the use of "choose"
    Input:
        fld (3D ndarray) of the data field to slice
        z (3D ndarray) of z values (like from make_full)
        which_z (ndarray of length 1) of the z value for the layer
    Output:
        lay (2D ndarray) fld on z == which_z,
            with np.nan where it is not defined
    """
    N, M, L = fld.shape # updates N for full fields
    Nmax = 30
    ii = np.arange(0,N,Nmax)
    ii = np.concatenate((ii,np.array([N,])))
    fld0 = np.nan * np.zeros((M, L), dtype=int)
    fld1 = np.nan * np.zeros((M, L), dtype=int)
    z0 = np.nan * np.zeros((M, L), dtype=int)
    z1 = np.nan * np.zeros((M, L), dtype=int)
    # NOTE: need fewer than 32 layers to use "choose"
    # so we split the operation into steps in this loop
    j = 0
    while j < len(ii)-1:
        i_lo = ii[j]
        i_hi = min(ii[j+1] + 1, ii[-1]) # overlap by 1
        NN = i_hi - i_lo # the number of levels in this chunk
        this_zr = zfull[i_lo:i_hi].copy()
        this_fld = fld[i_lo:i_hi].copy()
        zm = this_zr < which_z
        ind0 = np.zeros((M, L), dtype=int)
        ind1 = np.zeros((M, L), dtype=int)
        ind0 = (zm == True).sum(0) - 1 # index of points below which_z
        ind1 = ind0 + 1 # index of points above which_z
        # dealing with out-of-bounds issues
        # note 0 <= ind0 <= NN-1
        # and  1 <= ind1 <= NN
        # make ind1 = ind0 for out of bounds cases
        ind0[ind0 == -1] = 0 # fix bottom case
        ind1[ind1 == NN] = NN-1 # fix top case
        # and now cells that should be masked have equal indices
        this_mask = ind0 != ind1
        this_fld0 = ind0.choose(this_fld)
        this_fld1 = ind1.choose(this_fld)
        this_z0 = ind0.choose(this_zr)
        this_z1 = ind1.choose(this_zr)
        fld0[this_mask] = this_fld0[this_mask]
        fld1[this_mask] = this_fld1[this_mask]
        z0[this_mask] = this_z0[this_mask]
        z1[this_mask] = this_z1[this_mask]
        j += 1
    # do the interpolation
    dz = z1 - z0
    dzf = which_z - z0
    dz[dz == 0] = np.nan
    fr = dzf / dz
    lay = fld0*(1 - fr) + fld1*fr
    return lay

def make_full(flt):
    """
    Adds top and bottom layers to array fld. This is intended for 3D ROMS data
    fields that are on the vertical rho grid, and where we want (typically for
    plotting purposes) to extend this in a smart way to the sea floor and the
    sea surface.
    NOTE: input is always a tuple.  If just sending a single array pack it
    as zfun.make_full((arr,))
    Input:
        flt is a tuple with either 1 ndarray (fld_mid,),
        or 3 ndarrays (fld_bot, fld_mid, fld_top)
    Output: fld is the "full" field
    """
    if len(flt)==3:
       fld = np.concatenate(flt, axis=0)
    elif len(flt)==1:
        if len(flt[0].shape) == 3:
            fld_mid = flt[0]
            N, M, L = fld_mid.shape
            fld_bot = fld_mid[0].copy()
            fld_bot = fld_bot.reshape(1, M, L).copy()
            fld_top = fld_mid[-1].copy()
            fld_top = fld_top.reshape(1, M, L).copy()
            fld = np.concatenate((fld_bot, fld_mid, fld_top), axis=0)
        elif len(flt[0].shape) == 2:
            fld_mid = flt[0]
            N, M = fld_mid.shape
            fld_bot = fld_mid[0].copy()
            fld_bot = fld_bot.reshape(1, M).copy()
            fld_top = fld_mid[-1].copy()
            fld_top = fld_top.reshape(1, M).copy()
            fld = np.concatenate((fld_bot, fld_mid, fld_top), axis=0)
        elif len(flt[0].shape) == 1:
            fld_mid = flt[0]
            fld_bot = fld_mid[0].copy()
            fld_top = fld_mid[-1].copy()
            fld = np.concatenate((fld_bot, fld_mid, fld_top), axis=0)
    return fld
    
def mask_salish(fld, lon, lat):
    """
    Mask out map fields inside the Salish Sea.   
    Input:
        2D fields of data (masked array), and associated lon and lat
        all must be the same shap
    Output:
        The data field, now masked in the Salish Sea.
    """
    x = [-125.5, -123.5, -122, -122]
    y = [50, 46.8, 46.8, 50]
    V = np.ones((len(x),2))
    V[:,0] = x
    V[:,1] = y
    P = mpath.Path(V)
    Rlon = lon.flatten()
    Rlat = lat.flatten()
    R = np.ones((len(Rlon),2))
    R[:,0] = Rlon
    R[:,1] = Rlat
    RR = P.contains_points(R) # boolean    
    fld = np.ma.masked_where(RR.reshape(lon.shape), fld)
    return fld
    
def get_section(ds, vn, x, y, in_dict):
    
    # PLOT CODE
    from warnings import filterwarnings
    filterwarnings('ignore') # skip a warning message

    # GET DATA
    G, S, T = zrfun.get_basic_info(in_dict['fn'])
    h = G['h']
    zeta = ds['zeta'][:].squeeze()
    zr = zrfun.get_z(h, zeta, S, only_rho=True)

    sectvar = ds[vn][:].squeeze()

    L = G['L']
    M = G['M']
    N = S['N']

    lon = G['lon_rho']
    lat = G['lat_rho']
    mask = G['mask_rho']
    maskr = mask.reshape(1, M, L).copy()
    mask3 = np.tile(maskr, [N, 1, 1])
    zbot = -h # don't need .copy() because of the minus operation

    # make sure fields are masked
    zeta[mask==False] = np.nan
    zbot[mask==False] = np.nan
    sectvar[mask3==False] = np.nan

    # create dist
    earth_rad = zfun.earth_rad(np.mean(lat[:,0])) # m
    xrad = np.pi * x /180
    yrad = np.pi * y / 180
    dx = earth_rad * np.cos(yrad[1:]) * np.diff(xrad)
    dy = earth_rad * np.diff(yrad)
    ddist = np.sqrt(dx**2 + dy**2)
    dist = np.zeros(len(x))
    dist[1:] = ddist.cumsum()/1000 # km
    # find the index of zero
    i0, i1, fr = zfun.get_interpolant(np.zeros(1), dist)
    idist0 = i0
    distr = dist.reshape(1, len(dist)).copy()
    dista = np.tile(distr, [N, 1]) # array
    # pack fields to process in dicts
    d2 = dict()
    d2['zbot'] = zbot
    d2['zeta'] = zeta
    d2['lon'] = lon
    d2['lat'] = lat
    d3 = dict()
    d3['zr'] = zr
    d3['sectvar'] = sectvar
    # get vectors describing the (plaid) grid
    xx = lon[1,:]
    yy = lat[:,1]
    col0, col1, colf = zfun.get_interpolant(x, xx)
    row0, row1, rowf = zfun.get_interpolant(y, yy)
    # and prepare them to do the bilinear interpolation
    colff = 1 - colf
    rowff = 1 - rowf
    # now actually do the interpolation
    # 2-D fields
    v2 = dict()
    for fname in d2.keys():
        fld = d2[fname]
        fldi = (rowff*(colff*fld[row0, col0] + colf*fld[row0, col1])
        + rowf*(colff*fld[row1, col0] + colf*fld[row1, col1]))
        if type(fldi) == np.ma.core.MaskedArray:
            fldi = fldi.data # just the data, not the mask
        v2[fname] = fldi
    # 3-D fields
    v3 = dict()
    for fname in d3.keys():
        fld = d3[fname]
        fldi = (rowff*(colff*fld[:, row0, col0] + colf*fld[:, row0, col1])
        + rowf*(colff*fld[:, row1, col0] + colf*fld[:, row1, col1]))
        if type(fldi) == np.ma.core.MaskedArray:
            fldid = fldi.data # just the data, not the mask
            fldid[fldi.mask == True] = np.nan
        v3[fname] = fldid
    v3['dist'] = dista # distance in km
    # make "full" fields by padding top and bottom
    nana = np.nan * np.ones((N + 2, len(dist))) # blank array
    v3['zrf'] = nana.copy()
    v3['zrf'][0,:] = v2['zbot']
    v3['zrf'][1:-1,:] = v3['zr']
    v3['zrf'][-1,:] = v2['zeta']
    #
    v3['sectvarf'] = nana.copy()
    v3['sectvarf'][0,:] = v3['sectvar'][0,:]
    v3['sectvarf'][1:-1,:] = v3['sectvar']
    v3['sectvarf'][-1,:] = v3['sectvar'][-1,:]
    #
    v3['distf'] = nana.copy()
    v3['distf'][0,:] = v3['dist'][0,:]
    v3['distf'][1:-1,:] = v3['dist']
    v3['distf'][-1,:] = v3['dist'][-1,:]    
    
    # attempt to skip over nan's
    v3.pop('zr')
    v3.pop('sectvar')
    v3.pop('dist')
    mask3 = ~np.isnan(v3['sectvarf'][:])
    #print(mask3.shape)
    mask2 = mask3[-1,:]
    dist = dist[mask2]
    NC = len(dist)
    NR = mask3.shape[0]
    for k in v2.keys():
        #print('v2 key: ' + k)
        v2[k] = v2[k][mask2]
    for k in v3.keys():
        #print('v3 key: ' + k)
        v3[k] = v3[k][mask3]
        v3[k] = v3[k].reshape((NR, NC))
        #print(v3[k].shape)
    
    return v2, v3, dist, idist0





