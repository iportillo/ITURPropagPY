# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import os
from astropy import units as u

from iturpropag.models.iturp1144.bilinear_2D_interpolator import bilinear_2D_interpolator
from iturpropag.models.iturp1144.bicubic_2D_interpolator import bicubic_2D_interpolator
from iturpropag.utils import load_data, dataset_dir, prepare_input_array,\
    prepare_output_array, memory


class __ITU1510():
    """Annual mean surface temperature

    Available versions include:
    * P.1510-0 (02/01) (Current version)
    """
    # This is an abstract class that contains an instance to a version of the
    # ITU-R P.1510 recommendation.

    def __init__(self, version=1):
        if version == 1:
            self.instance = _ITU1510_1()
        elif version == 0:
            self.instance = _ITU1510_0()
        else:
            raise ValueError('Version ' + str(version) + ' is not implemented'
                             ' for the ITU-R P.1510 model.')

    @property
    def __version__(self):
        return self.instance.__version__

    def surface_month_mean_temperature(self, lat, lon, m):
        # Abstract method to compute the monthly surface mean temperature
        fcn = np.vectorize(self.instance.surface_month_mean_temperature,
                           excluded=[0, 1], otypes=[np.ndarray])
        return np.array(fcn(lat, lon, m).tolist())


class _ITU1510_1():

    def __init__(self):
        self.__version__ = 1
        self.year = 2017
        self.month = 6
        self.link = 'https://www.p.int/rec/R-REC-P.1510/' +\
                    'recommendation.asp?lang=en&parent=R-REC-P.1510-1-201706-I'

        self.__months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        self._month_temperature = {}

    def month_temperature(self, lat, lon, m):
        if not self._month_temperature:
            lats = load_data(os.path.join(dataset_dir, 'p1510/v1_Lat.h5'))
            lons = load_data(os.path.join(dataset_dir, 'p1510/v1_Lon.h5'))
            for _m in self.__months:
                vals = load_data(os.path.join(dataset_dir,
                                              'p1510/v1_T_Month{0:02d}.h5')
                                 .format(_m))
                self._month_temperature[_m] = bilinear_2D_interpolator(
                            np.flipud(lats), lons, np.flipud(vals))

        lon[lon > 180] = lon[lon > 180] - 360
        return self._month_temperature[m](
            np.array([lat.ravel(), lon.ravel()]).T).reshape(lat.shape)

    def surface_month_mean_temperature(self, lat, lon, m):
        return self.month_temperature(lat, lon, m)


class _ITU1510_0():

    def __init__(self):
        self.__version__ = 0
        self.year = 2001
        self.month = 2
        self.link = 'https://www.p.int/rec/R-REC-P.1510/' +\
                    'recommendation.asp?lang=en&parent=R-REC-P.1510-0-200102-I'

        self._temperature = {}

    def surface_month_mean_temperature(self, lat, lon, m):
        raise NotImplementedError('The monthly mean temperature is not'
                                  'implemented in recomendation ITU-R P.1510'
                                  '-{0}'.format(self.__version__))


__model = __ITU1510()


def change_version(new_version):
    """
    Change the version of the ITU-R P.1510 recommendation currently being used.


    Parameters
    ----------
    - new_version : int
            Number of the version to use.
            Valid values are:
            * 1: P.1510-1 (02/01) (Current version)
            * 0: P.1510-0
    """
    global __model
    __model = __ITU1510(new_version)
    memory.clear()


def get_version():
    """
    Obtain the version of the ITU-R P.1510 recommendation currently being used.
    """
    global __model
    return __model.__version__


@memory.cache
def surface_month_mean_temperature(lat, lon, m):
    """
    A method to estimate the annual mean surface temperature (K) at 2 m
    above the surface of the Earth


    Parameters
    ----------
    - lat : number, sequence, or numpy.ndarray
            Latitudes of the receiver points
    - lon : number, sequence, or numpy.ndarray
            Longitudes of the receiver points
    - m: number
            An integer shows the number of the month

    Returns
    -------
    - temperature: numpy.ndarray
            Annual mean surface temperature (K)


    References
    ----------
    [1] Annual mean surface temperature:
    https://www.p.int/rec/R-REC-P.1510/en

    """
    global __model
    type_output = type(lat)
    lat = prepare_input_array(lat)
    lon = prepare_input_array(lon)
    lon = np.mod(lon, 360)
    val = __model.surface_month_mean_temperature(lat, lon, m)
    return prepare_output_array(val, type_output) * u.Kelvin
