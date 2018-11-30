""" Core utilities for handling GEOS-Chem data """

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

import xarray as xr
import xbpch
import numpy as np

def open_dataset(filename, **kwargs):
    """ Load and decode a dataset from an output file generated by GEOS-Chem

    This method inspects a GEOS-Chem output file and chooses a way to load it
    into memory as an xarray Dataset. Because two different libraries to
    support BPCH and netCDF outputs, you may need to pass additional keyword
    arguments to the function. See the Examples below.

    Parameters
    ----------
    filename : str
        Path to a GEOS-Chem output file (netCDF or BPCH format) which can be
        loaded through either xarray or xbpch. Note that xarray conventions for
        netCDF files apply.
    **kwargs
        Additional keyword arguments to be passed directly to
        `xarray.open_dataset` or `xbpch.open_bpchdataset`.

    Returns
    -------
    dataset : xarray.Dataset
        The dataset loaded from the referenced filename.

    See Also
    --------
    xarray.open_dataset
    xbpch.open_bpchdataset
    open_mfdataset

    Examples
    --------

    Open a legacy BPCH output file:

    >>> ds = open_dataset("my_GEOS-Chem_run.bpch",
    ...                   tracerinfo_file='tracerinfo.dat',
    ...                   diaginfo_file='diaginfo.dat')

    Open a netCDF output file, but disable metadata decoding:
    >>> ds = open_dataset("my_GCHP_data.nc",
    ...                   decode_times=False, decode_cf=False)

    """

    basename, file_extension = os.path.splitext(filename)

    if file_extension == '.bpch':
        _opener = xbpch.open_bpchdataset
    elif file_extension == '.nc':
        _opener = xr.open_dataset
    else:
        raise ValueError("Found unknown file extension ({}); please pass a "
                         "BPCH or netCDF file with extension 'bpch' or 'nc'."
                         .format(file_extension))

    return _opener(filename, **kwargs)


def open_mfdataset(filenames, concat_dim='time', compat='no_conflicts',
                   preprocess=None, lock=None, **kwargs):
    """ Load and decode multiple GEOS-Chem output files as a single Dataset.

    Parameters
    ----------
    filenames : list of strs
        Paths to GEOS-Chem output files to load. Must have the same extension
        and be able to be concatenated along some common axis.
    concat_dim : str, default='time'
        Dimension to concatenate Datasets over. We default to "time" since this
        is how GEOS-Chem splits output files.
    compat : {'identical', 'equals', 'broadcast_equals',
              'no_conflicts'}, optional
        String indicating how to compare variables of the same name for
        potential conflicts when merging:
        - 'broadcast_equals': all values must be equal when variables are
          broadcast against each other to ensure common dimensions.
        - 'equals': all values and dimensions must be the same.
        - 'identical': all values, dimensions and attributes must be the
          same.
        - 'no_conflicts': only values which are not null in both datasets
          must be equal. The returned dataset then contains the combination
          of all non-null values.
    preprocess : callable (optional)
        A pre-processing function to apply to each Dataset prior to
        concatenation
    lock : False, True, or threading.Lock (optional)
        Passed to :py:func:`dask.array.from_array`. By default, xarray
        employs a per-variable lock when reading data from NetCDF files,
        but this model has not yet been extended or implemented for bpch files
        and so this is not actually used. However, it is likely necessary
        before dask's multi-threaded backend can be used
    **kwargs
        Additional keyword arguments to be passed directly to
        `xbpch.open_mfbpchdataset` or `xarray.open_mfdataset`.

    Returns
    -------
    dataset : xarray.Dataset
        A dataset containing the data in the specified input filenames.

    See Also
    --------
    xarray.open_mfdataset
    xbpch.open_mfbpchdataset
    open_dataset

    """

    try:
        test_fn = filenames[0]
    except:
        raise ValueError("Must pass a list with at least one filename")

    basename, file_extension = os.path.splitext(test_fn)

    if file_extension == '.bpch':
        _opener = xbpch.open_mfbpchdataset
    elif file_extension == '.nc':
        _opener = xr.open_mfdataset
    else:
        raise ValueError("Found unknown file extension ({}); please pass a "
                         "BPCH or netCDF file with extension 'bpch' or 'nc'."
                         .format(file_extension))

    return _opener(filenames, concat_dim=concat_dim, compat=compat,
                   preprocess=preprocess, lock=lock, **kwargs)

def get_gcc_filepath(outputdir, collection, day, time):
    if collection == 'Emissions':
        filepath = os.path.join(outputdir, 'HEMCO_diagnostics.{}{}.nc'.format(day,time))
    else:
        filepath = os.path.join(outputdir, 'GEOSChem.{}.{}_{}z.nc4'.format(collection,day,time))
    return filepath

def check_paths( refpath, devpath):
    if not os.path.exists(refpath):
        print('ERROR! Path 1 does not exist: {}'.format(refpath))
    else:
        print('Path 1 exists: {}'.format(refpath))
    if not os.path.exists(devpath):
        print('ERROR! Path 2 does not exist: {}'.format(devpath))
    else:
        print('Path 2 exists: {}'.format(devpath))

def compare_varnames(refdata, devdata):
    # Find common variables in collection by generating lists and list overlap
    refvars = [k for k in refdata.data_vars.keys()]
    devvars= [k for k in devdata.data_vars.keys()]
    commonvars = sorted(list(set(refvars).intersection(set(devvars))))
    refonly = [v for v in refvars if v not in devvars]
    devonly = [v for v in devvars if v not in refvars]
    dimmismatch = [v for v in commonvars if refdata[v].ndim != devdata[v].ndim]
    commonvars1D = [v for v in commonvars if refdata[v].ndim == 2]
    commonvars2D = [v for v in commonvars if refdata[v].ndim == 3]
    commonvars3D = [v for v in commonvars if devdata[v].ndim == 4]
    
    # Print information on common and mismatching variables, as well as dimensions
    print('{} common variables'.format(len(commonvars)))
    if len(refonly) > 0:
        print('{} variables in ref only (skip)'.format(len(refonly)))
        print('   Variable names: {}'.format(refonly))
    else:
        print('0 variables in ref only')
    if len(devonly) > 0:
        print('{} variables in dev only (skip)'.format(len(devonly)))
        print('   Variable names: {}'.format(devonly))
    else:
        print('0 variables in dev only')
    if len(dimmismatch) > 0:
        print('{} common variables have different dimensions'.format(len(dimmismatch)))
        print('   Variable names: {}'.format(dimmismatch))
    else:
        print('All variables have same dimensions in ref and dev')

    return [commonvars, commonvars1D, commonvars2D, commonvars3D]

def compare_stats(refdata, refstr, devdata, devstr, varname):
    refvar = refdata[varname]
    devvar = devdata[varname]
    units = refdata[varname].units
    print('Data units:')
    print('    {}:  {}'.format(refstr,units))
    print('    {}:  {}'.format(devstr,units))
    print('Array sizes:')
    print('    {}:  {}'.format(refstr,refvar.shape))
    print('    {}:  {}'.format(devstr,devvar.shape))
    print('Global stats:')
    print('  Mean:')
    print('    {}:  {}'.format(refstr,np.round(refvar.values.mean(),20)))
    print('    {}:  {}'.format(devstr,np.round(devvar.values.mean(),20)))
    print('  Min:')
    print('    {}:  {}'.format(refstr,np.round(refvar.values.min(),20)))
    print('    {}:  {}'.format(devstr,np.round(devvar.values.min(),20)))
    print('  Max:')
    print('    {}:  {}'.format(refstr,np.round(refvar.values.max(),20)))
    print('    {}:  {}'.format(devstr,np.round(devvar.values.max(),20)))
    print('  Sum:')
    print('    {}:  {}'.format(refstr,np.round(refvar.values.sum(),20)))
    print('    {}:  {}'.format(devstr,np.round(devvar.values.sum(),20)))

def get_collection_data(datadir, collection, day, time):
    datafile = get_gcc_filepath(datadir, collection, day, time)
    if not os.path.exists(datafile):
        print('ERROR! File does not exist: {}'.format(datafile))
    data_ds = xr.open_dataset(datafile)
    return data_ds

def make_grid_LL(llres):
    [dlat,dlon] = list(map(float, llres.split('x')))
    lon_b = np.linspace(-180 - dlon/2, 180 - dlon/2, int(360/dlon) + 1, endpoint=True)
    lat_b = np.linspace(-90 - dlat/2, 90 + dlat/2, int(180/dlat) + 2, endpoint=True).clip(-90,90)
    lat = (lat_b[1:] + lat_b[:-1]) / 2
    lon = (lon_b[1:] + lon_b[:-1]) / 2
    llgrid = {'lat': lat, 
              'lon': lon, 
              'lat_b': lat_b, 
              'lon_b': lon_b}
    return llgrid

def convert_bpch_names_to_netcdf_names(ds, inplace=True, verbose=False):

    '''
    Function to convert the non-standard bpch diagnostic names
    to names used in the GEOS-Chem netCDF diagnostic outputs.
    
    Arguments:
    ds      : The xarray Dataset object whose names are to be replaced.
    
    inplace : If inplace=True (which is the default setting), then 
              the variable names in ds will be renamed in-place.
              Otherwise a copy of ds will be created.

    verbose : Turns on verbose print output

    NOTE: Only the diagnostic names needed for the 1-month benchmark
    plots have been added at this time.  To make this a truly general
    tool, we can consider adding the diagnostic names for the GEOS-Chem
    specialtiy simulations later on.
    '''

    # Names dictionary (key = bpch id, value[0] = netcdf id,
    # value[1] = action to create full name using id)
    names = {'IJ_AVG_S_':         ['SpeciesConc',                   'append' ],
             'OD_MAP_S_OPD1550':  ['AODDust550nm_bin1',             'replace'],
             'OD_MAP_S_OPD2550':  ['AODDust550nm_bin2',             'replace'],
             'OD_MAP_S_OPD3550':  ['AODDust550nm_bin3',             'replace'],
             'OD_MAP_S_OPD4550':  ['AODDust550nm_bin4',             'replace'],
             'OD_MAP_S_OPD5550':  ['AODDust550nm_bin5',             'replace'],
             'OD_MAP_S_OPD6550':  ['AODDust550nm_bin6',             'replace'],
             'OD_MAP_S_OPD7550':  ['AODDust550nm_bin7',             'replace'],
             'OD_MAP_S_OPSO4550': ['AODHyg550nm_SO4',               'replace'],
             'OD_MAP_S_OPBC550':  ['AODHyg550nm_BCPI',              'replace'],
             'OD_MAP_S_OPOC550':  ['AODHyg550nm_OCPI',              'replace'],
             'OD_MAP_S_OPSSa550': ['AODHyg550nm_SALA',              'replace'],
             'OD_MAP_S_OPSSc550': ['AODHyg550nm_SALC',              'replace'],
             'OD_MAP_S_ODSLA':    ['AODStratLiquidAer550nm',        'replace'],
             'ACETSRCE_ACETbg':   ['EmisACET_DirectBio',            'replace'],
             'ACETSRCE_ACETmb':   ['EmisACET_MethylBut',            'replace'],
             'ACETSRCE_ACETmo':   ['EmissACET_Monoterp',            'replace'],
             'ACETSRCE_ACETop':   ['EmissACET_Ocean',               'replace'],
             'ANTHSRCE_':         ['Anthro',                        'append' ],
             'BC_ANTH_BLKC':      ['EmisBC_Anthro',                 'skip'   ],
             'BC_BIOB_BLKC':      ['EmisBC_BioBurn',                'skip'   ],
             'BC_BIOF_BLKC':      ['EmisBC_Biofuel',                'skip'   ],
             'BIOBSRCE_':         ['BioBurn',                       'append' ],
             'BIOFSRCE_':         ['Biofuel',                       'append' ],
             'BIOGSRCE_':         ['Biogenic',                      'append' ],
             'BXHGHT_S_':         ['Met',                           'append' ],
             'CHEM_L_S_OH':       ['OHconcAfterChem',               'replace'],
             'CHEM_L_S_HO2':      ['HO2concAfterChem',              'replace'],
             'CHEM_L_S_O1D':      ['O1DconcAfterChem',              'replace'],
             'CHEM_L_S_O':        ['O3PconcAfterChem',              'replace'],
             'CO__SRCE_COanth':   ['EmisCO_Anthro',                 'skip'   ],
             'CO__SRCE_CObb':     ['EmisCO_BioBurn',                'skip'   ],
             'CO__SRCE_CObf':     ['EmisCO_Biofuel',                'skip'   ],
             'CO__SRCE_COmono':   ['EmisCO_Monoterp',               'replace'],
             'CO__SRCE_COship':   ['EmisCO_Ship',                   'replace'],
             'CV_FLUX_':          ['CloudConvFlux',                 'append' ],
             'DAO_3D_S_':         ['Met',                           'append' ],
             'DAO_FLDS_PS_PBL':   ['Met_PBLH',                      'skip'   ],
             'DAO_FLDS_':         ['Met',                           'append' ],
             'DMS_BIOG_DMS':      ['EmisDMS_Ocean',                 'replace'],
             'DRYD_FLX_':         ['DryDep',                        'append' ],
             'DRYD_VEL_':         ['DryDepVel',                     'append' ],
             'DUST_SRC_':         ['TBD',                           'skip'   ],
             'DUSTSRCE_DST1':     ['EmisDST1_Natural',              'replace'],
             'DUSTSRCE_DST2':     ['EmisDST2_Natural',              'replace'],
             'DUSTSRCE_DST3':     ['EmisDST3_Natural',              'replace'],
             'DUSTSRCE_DST4':     ['EmisDST4_Natural',              'replace'],
             'DXYP_DXYP':         ['Met_AREAM2',                    'replace'],
             'ECIL_SRC_':         ['TBD',                           'skip'   ],
             'ECOB_SRC_':         ['TBD',                           'skip'   ],
             'EW_FLX_S_':         ['AdvFluxZonal',                  'append' ],
             'FJX_FLUX_':         ['TBD',                           'skip'   ],
             'IJ_24H_S_':         ['TBD',                           'skip'   ],
             'IJ_MAX_S_':         ['TBD',                           'skip'   ],
             'IJ_SOA_S_':         ['AerMass',                       'append' ],
             'INST_MAP_':         ['TBD',                           'skip'   ],
             'ISRPIA_S_ISORPH':   ['Chem_PHSAV',                    'replace'],
             'ISRPIA_S_ISORH+':   ['Chem_HPLUSSAV',                 'replace'],
             'ISRPIA_S_ISORH2O':  ['Chem_WATERSAV',                 'replace'],
             'JV_MAP_S_':         ['JNoon',                         'append' ],
             'LFLASH_':           ['TBD',                           'skip'   ],
             'NH3_ANTH_NH3':      ['EmisNH3_Anthro',                'skip'   ],
             'NH3_NATU_NH3':      ['EmisNH3_Natural',               'replace'],
             'NK_EMISS_':         ['TBD',                           'skip'   ],
             'MC_FRC_S_':         ['WetLossConvFrac',               'append' ],
             'NO_AC_S_NO':        ['EmisNO_Aircraft',               'replace'],
             'NO_AN_S_NO':        ['EmisNO_Anthro',                 'skip'   ],
             'NO_FERT_NO':        ['EmisNO_Fert',                   'replace'],
             'NO_LI_S_NO':        ['EmisNO_Lightning',              'replace'],
             'NO_SOIL_NO':        ['EmisNO_Soil',                   'replace'],
             'NS_FLX_S_':         ['AdvFluxMerid',                  'append' ],
             'OC_ANTH_ORGC':      ['EmisOC_Anthro',                 'replace'],
             'OC_LIMO_LIMO':      ['TBD',                           'skip'   ],
             'OC_MTPA_MTPA':      ['TBD',                           'skip'   ],
             'OC_MTPO_MTPO':      ['TBD',                           'skip'   ],
             'OC_SESQ_SESQ':      ['TBD',                           'skip'   ],
             'OCIL_SRC_':         ['TBD',                           'skip'   ],
             'OCOB_SRC_':         ['TBD',                           'skip'   ],
             'OD_MAP_S_OPD':      ['Met_OPTD',                      'replace'],
             'OD_MAP_S_CLDTOT':   ['Met_CLDF',                      'replace'],
             'OD_MAP_S_OPTD':     ['AODDust',                       'replace'],
             'OD_MAP_S_SD':       ['AerSurfAreaDust',               'replace'],
             'OD_MAP_S_HGSO4':    ['AerHygroscopicGrowth_SO4',      'replace'],
             'OD_MAP_S_HGBC':     ['AerHygroscopicGrowth_BCPI',     'replace'],
             'OD_MAP_S_HGOC':     ['AerHygroscopicGrowth_OCPI',     'replace'],
             'OD_MAP_S_HGSSa':    ['AerHygroscopicGrowth_SALA',     'replace'],
             'OD_MAP_S_HGSSc':    ['AerHygroscopicGrowth_SALC',     'replace'],
             'OD_MAP_S_SSO4':     ['AerSurfAreaHyg_SO4',            'replace'],
             'OD_MAP_S_SBC':      ['AerSurfAreaHyg_BCPI',           'replace'],
             'OD_MAP_S_SOC':      ['AerSurfAreaHyg_OCPI',           'replace'],
             'OD_MAP_S_SSSa':     ['AerSurfAreaHyg_SALA',           'replace'],
             'OD_MAP_S_SSSc':     ['AerSurfAreaHyg_SALC',           'replace'],
             'OD_MAP_S_SASLA':    ['AerSurfAreaStratLiquid',        'replace'],
             'OD_MAP_S_NDSLA':    ['AerNumDensityStratLiquid',      'replace'],
             'OD_MAP_S_ODSPA':    ['AODPolarStratCloud550nm',       'replace'],
             'OD_MAP_S_SASPA':    ['AerSurfAreaPolarStratCloud',    'replace'],
             'OD_MAP_S_NDSPA':    ['AerNumDensityStratParticulate', 'replace'],
             'OD_MAP_S_ISOPAOD':  ['AODSOAfromAqIsoprene550nm',     'replace'],
             'OD_MAP_S_AQAVOL':   ['AerAqueousVolume',              'replace'],
             'PBLDEPTH_':         ['TBD',                           'skip'   ],
             'PEDGE_S_PSURF':     ['TBD',                           'skip'   ],
             'PG_SRCE_':          ['TBD',                           'skip'   ],
             'PG_PP_':            ['TBD',                           'skip'   ],
             'PL_BC_S_BLKC':      ['ProdBCPIfromBCPO',              'replace'],
             'PL_OC_S_ORGC' :     ['ProdOCPIfromOCPO',              'replace'],
             'PL_OC_S_ASOA' :     ['Prodfrom',                      'skip'   ],
             'PL_OC_S_ISOA' :     ['Prodfrom',                      'skip'   ],
             'PL_OC_S_TSOA' :     ['Prodfrom',                      'skip'   ],
             'PL_SUL_S_SO2dms':   ['ProdSO2fromDMSandOH',           'replace'],
             'PL_SUL_S_SO2no3':   ['ProdSO2fromDMSandNO3',          'replace'],
             'PL_SUL_S_SO2tot':   ['ProdSO2fromDMS',                'replace'],
             'PL_SUL_S_MSAdms':   ['ProdMSAfromDMS',                'replace'],
             'PL_SUL_S_SO4gas':   ['ProdSO4fromGasPhase',           'replace'],
             'PL_SUL_S_SO4h2o2':  ['ProdSO4fromH2O2inCloud',        'replace'],
             'PL_SUL_S_SO4o3s':   ['ProdSO4fromO3s',                'replace'],
             'PL_SUL_S_SO4o3':    ['ProdSO4fromO3inCloud',          'replace'],
             'PL_SUL_S_SO4ss':    ['ProdSO4fromO3inSeaSalt',        'replace'],
             'PL_SUL_S_SO4dust':  ['ProdSO4fromOxidationOnDust',    'replace'],
             'PL_SUL_S_NITdust':  ['ProdNITfromHNO3uptakeOnDust',   'replace'],
             'PL_SUL_S_H2SO4dus': ['ProdSO4fromUptakeOfH2SO4g',     'replace'],
             'PL_SUL_S_HNO3ss':   ['LossHNO3onSeaSalt',             'replace'],
             'PL_SUL_S_SO4hobr':  ['ProdSO4fromHOBrInCloud',        'replace'],
             'PL_SUL_S_SO4sro3':  ['ProdSO4fromSRO3',               'replace'],
             'PL_SUL_S_SO4srhob': ['ProdSO4fromSRHObr',             'replace'],
             'PORL_L_S_PCO_CH4':  ['ProdCObyCH4',                   'skip'   ],
             'PORL_L_S_PCO_NMVO': ['ProdCObyNMVOC',                 'skip'   ],
             'PORL_L_S_PO3':      ['Prod_O3',                       'replace'],
             'PORL_L_S_PCO':      ['Prod_CO',                       'replace'],
             'PORL_L_S_PSO4':     ['Prod_SO4',                      'replace'],
             'PORL_L_S_POx':      ['Prod_Ox',                       'replace'],
             'PORL_L_S_LO3':      ['Loss_O3',                       'replace'],
             'PORL_L_S_LCO':      ['Loss_CO',                       'replace'],
             'PORL_L_S_LOx':      ['Loss_Ox',                       'replace'],
             'RADMAP_':           ['TBD',                           'skip'   ],
             'RN_SRCE_Rn':        ['EmisRn_Soil',                   'replace'],
             'RN_SRCE_Pb':        ['PbFromRnDecay',                 'replace'],
             'RN_SRCE_Be7':       ['EmisBe_Cosmic',                 'replace'],
             'RN_DECAY_':         ['RadDecay',                      'append' ],
             'SALTSRCE_SALA':     ['EmisSALA_Natural',              'replace'],
             'SALTSRCE_SALC':     ['EmisSALC_Natural',              'replace'],
             'SHIP_SSS_':         ['TBD',                           'skip'   ],
             'SO2_AC_S_SO2':      ['EmisSO2_Aircraft',              'replace'],
             'SO2_AN_S_SO2':      ['EmisSO2_Anthro',                'skip'   ],
             'SO2_EV_S_SO2':      ['EmisSO2_EVOL',                  'replace'],
             'SO2_NV_S_SO2':      ['EmisSO2_NVOL',                  'replace'],
             'SO2_SHIP_SO2':      ['EmisSO2_Ship',                  'replace'],
             'SO4_AN_S_SO4':      ['EmisSO4_Anthro',                'skip'   ],
             'SO4_BIOF_SO4':      ['EmisSO4_Biofuel',               'replace'],
             'SF_EMIS_':          ['TBD',                           'skip'   ],
             'SS_EMIS_':          ['TBD',                           'skip'   ],
             'THETA_S_THETA':     ['Met_THETA',                     'replace'],
             'TIME_TPS_TIMETROP': ['TBD',                           'skip'   ],
             'TMS_COND_':         ['TBD',                           'skip'   ],
             'TMS_COAG_':         ['TBD',                           'skip'   ],
             'TMS_NUCL_':         ['TBD',                           'skip'   ],
             'TMS_AQOX_':         ['TBD',                           'skip'   ],
             'AERO_FIX_':         ['TBD',                           'skip'   ],
             'TMS_SOA_':          ['TBD',                           'skip'   ],
             'TR_PAUSE_TP_HGHT':  ['Met_TropHt',                    'replace'],
             'TR_PAUSE_TP_LEVEL': ['Met_TropLev',                   'replace'],
             'TR_PAUSE_TP_PRESS': ['Met_TROPP',                     'replace'],
             'UP_FLX_S_':         ['AdvFluxVert',                   'append' ],
             'WETDCV_S_':         ['WetLossConv',                   'append' ],
             'WETDLS_S_':         ['WetLossLS',                     'append' ],
             'PG-PP_S_':          ['POPS',                          'append' ],
             'NH3_BIOB_NH3':      ['EmisNH3_BioBurn',               'skip'   ],
             'NH3_BIOF_NH3':      ['EmisNH3_Biofuel',               'skip'   ],
             'NO_BIOB_NO':        ['EmisNO_BioBurn',                'skip'   ],
             'NO_BIOF_NO':        ['EmisNO_Biofuel',                'skip'   ],
             'OC_BIOB_ORGC':      ['EmisOC_BioBurn',                'skip'   ],
             'OC_BIOF_ORGC':      ['EmisOC_Biofuel',                'skip'   ],
             'OC_BIOG_ORGC':      ['EmisOC_Biogenic',               'skip'   ],
             'SO2_BIOB_SO2':      ['EmisSO2_BioBurn',               'skip'   ],
             'SO2_BIOF_SO2':      ['EmisSO2_Biofuel',               'skip'   ]}

    # define some special variable to overwrite above
    special_vars = {'AerMassPM25'  : 'PM25',
                    'AerMassbiogOA': 'TotalBiogenicOA',
                    'AerMasssumOA' : 'TotalOA',
                    'AerMasssumOC' : 'TotalOC',
                    'AerMassBNO'   : 'BetaNO',
                    'AerMassOC'    : 'OC',
                    'Met_AIRNUMDE' : 'Met_AIRNUMDEN',
                    'Met_UWND'     : 'Met_U',
                    'Met_VWND'     : 'Met_V',
                    'Met_CLDTOP'   : 'Met_CLDTOPS',
                    'Met_GWET'     : 'Met_GWETTOP',
                    'Met_PRECON'   : 'Met_PRECCON',
                    'Met_PREACC'   : 'Met_PRECTOT',
                    'Met_PBL'      : 'Met_PBLH' }

    # Python dictionary for variable name replacement
    old_to_new = {}

    # Loop over all variable names in the data set
    for variable_name in ds.data_vars:

        # Check if name matches anything in dictionary. Give warning if not.
        oldid = ''
        newid = ''
        idaction = ''
        for key in names:
            if key in variable_name:
                if names[key][1] == 'skip':
                    # Verbose output
                    if verbose:
                        print("WARNING: skipping {}".format(key))
                else:
                    oldid = key
                    newid = names[key][0]
                    idaction = names[key][1]
                break

        # Go to the next line if no definition was found
        if oldid == '' or newid == '' or idaction == '':
            continue

        # If fullname replacement:
        if idaction == 'replace':
            oldvar = oldid
            newvar = newid

            # Update the dictionary of names with this pair
            old_to_new.update({variable_name : newvar})

        # For all the rest:
        else:
            linearr = variable_name.split("_")
            varstr = linearr[-1]
            oldvar = oldid + varstr

            # Most append cases just append with underscore
            if oldid in ['IJ_AVG_S_', 'RN_DECAY_', 'WETDCV_S_', 'WETDLS_S_', 'BXHGHT_S_', 'DAO_FLDS_', 
                         'DAO_3D_S_', 'PL_SUL_',   'CV_FLX_S_', 'EW_FLX_S_', 'NS_FLX_S_', 'UP_FLX_S_',
                         'MC_FRC_S_', 'JV_MAP_S_' ]:
     
                # Skip certain fields that will cause conflicts w/ netCDF
                if oldid in [ 'DAO_FLDS_PS_PBL', 'DAO_FLDS_TROPPRAW' ]:

                    # Verbose output
                    if verbose:
                        print( 'Skipping: {}'.format(oldid) )
                else:
                    newvar = newid + '_' +varstr

            # IJ_SOA_S_
            elif oldid == 'IJ_SOA_S_':
                newvar = newid + varstr
            
            # DRYD_FLX_, DRYD_VEL_
            elif 'DRYD_' in oldid:
                newvar = newid + '_' + varstr[:-2]

            # BIOBSRCE_, BIOFSRCE_, BIOGSRCE_. ANTHSRCE_
            elif oldid in ['BIOBSRCE_', 'BIOFSRCE_', 'BIOGSRCE_', 
                           'ANTHSRCE_' ]:
                newvar = 'Emis' + varstr +'_' + newid
            
            # If nothing found...
            else:
                
                # Verbose output
                if verbose:
                    print("WARNING: Nothing defined for: {}".format(variable_name))
                continue

          # Overwrite certain variable names
            if newvar in special_vars:
                newvar = special_vars[newvar]

            # Update the dictionary of names with this pair
            old_to_new.update({variable_name : newvar})

    # Verbose output
    if verbose:
        print("\nList of bpch names and netCDF names")
        for key in old_to_new:
            print("{} ==> {}".format(key.ljust(25),old_to_new[key].ljust(40)))

    # Rename the variables in the dataset
    if verbose:
        print( "\nRenaming variables in the data...")
    ds = ds.rename(name_dict=old_to_new, inplace=inplace)
    
    # Return the dataset
    return ds

# Define function to add a new variable to a data set using known units, name, and existing vars to sum.
def add_species_to_dataset(ds, varname, varlist, units, verbose=False, overwrite=False ):
    if varname in ds.data_vars and overwrite:
        ds.drop(key)
    else:
        assert varname not in ds.data_vars, '{} already in dataset!'.format(varname)
    if verbose: print('Creating {}'.format(varname))
    darr = ds[varlist[0][0]] * varlist[0][1]
    for i in range(len(varlist)):
        if verbose: print(' -> {}'.format(varlist[i][0]))
        if i==0: continue
        darr = darr + ds[varlist[i][0]]*varlist[i][1]
    darr.name = varname
    darr.attrs['units'] = units
    ds = xr.merge([ds,darr])
    return ds






