#!/usr/bin/env python
"""
@package glider.py
@file glider.py
@author Stuart Pearce & Chris Wingard
@brief Module containing parser scripts for glider data set agents
"""
__author__ = 'Stuart Pearce, Chris Wingard, Nick Almonte'
__license__ = 'Apache 2.0'

import re
import ntplib
from math import copysign, isnan
from mi.core.log import get_logger, get_logging_metaclass
from mi.core.common import BaseEnum
from mi.core.exceptions import SampleException, UnexpectedDataException, RecoverableSampleException
from mi.core.instrument.data_particle import DataParticle, DataParticleKey
from mi.dataset.dataset_parser import SimpleParser
from mi.dataset.parser import utilities

# start the logger
log = get_logger()

class StateKey(BaseEnum):
    POSITION = 'position'
    SENT_METADATA = 'sent_metadata'


class DataParticleType(BaseEnum):
    # Data particle types for the Open Ocean (aka Global) and Coastal gliders.
    # ADCPA data will parsed by a different parser (adcpa.py)
    DOSTA_ABCDJM_GLIDER_INSTRUMENT = 'dosta_abcdjm_glider_instrument'
    DOSTA_ABCDJM_GLIDER_RECOVERED = 'dosta_abcdjm_glider_recovered'
    CTDGV_M_GLIDER_INSTRUMENT = 'ctdgv_m_glider_instrument'
    CTDGV_M_GLIDER_INSTRUMENT_RECOVERED = 'ctdgv_m_glider_instrument_recovered'
    FLORD_M_GLIDER_INSTRUMENT = 'flord_m_glider_instrument'
    FLORD_M_GLIDER_INSTRUMENT_RECOVERED = 'flord_m_glider_instrument_recovered'
    FLORT_M_GLIDER_INSTRUMENT = 'flort_m_glider_instrument'
    FLORT_M_GLIDER_RECOVERED = 'flort_m_glider_recovered'
    PARAD_M_GLIDER_INSTRUMENT = 'parad_m_glider_instrument'
    PARAD_M_GLIDER_RECOVERED = 'parad_m_glider_recovered'
    GLIDER_ENG_TELEMETERED = 'glider_eng_telemetered'
    GLIDER_ENG_METADATA = 'glider_eng_metadata'
    GLIDER_ENG_RECOVERED = 'glider_eng_recovered'
    GLIDER_ENG_SCI_TELEMETERED = 'glider_eng_sci_telemetered'
    GLIDER_ENG_SCI_RECOVERED = 'glider_eng_sci_recovered'
    GLIDER_ENG_METADATA_RECOVERED = 'glider_eng_metadata_recovered'


class GliderParticleKey(BaseEnum):
    """
    Common glider particle parameters
    """
    M_PRESENT_SECS_INTO_MISSION = 'm_present_secs_into_mission'
    M_PRESENT_TIME = 'm_present_time'  # you need the m_ timestamps for lats & lons
    SCI_M_PRESENT_TIME = 'sci_m_present_time'
    SCI_M_PRESENT_SECS_INTO_MISSION = 'sci_m_present_secs_into_mission'

    @classmethod
    def science_parameter_list(cls):
        """
        Get a list of all science parameters
        """
        result = []
        for key in cls.list():
            if key not in GliderParticleKey.list():
                result.append(key)

        return result


class GliderParticle(DataParticle):
    """
    Base particle for glider data. Glider files are
    publishing as a particle rather than a raw data string. This is in
    part to solve the dynamic nature of a glider file and not having to
    hard code >2000 variables in a regex.

    This class should be a parent class to all the data particle classes
    associated with the glider.
    """

    # It is possible that record could be parsed, but they don't
    # contain actual science data for this instrument. This flag
    # will be set to true if we have found data when parsed.
    common_parameters = GliderParticleKey.list()

    def _parsed_values(self, key_list):
        if not isinstance(self.raw_data, dict):
            raise SampleException(
                "%s: Object Instance is not a Glider Parsed Data \
                 dictionary" % self._data_particle_type)
        empty_set = {float('nan'), None}

        value_list = [self.raw_data.get(key, None) for key in key_list]
        value_set = set(value_list)
        if value_set == empty_set:
            log.error("No parameters from particle found in input row of Raw Data, particle cannot be created!")
            raise SampleException("No data for particle found")

        result = []
        for key, value in zip(key_list, value_list):
            if type(value) is float and isnan(value):
                value = None
            result.append({DataParticleKey.VALUE_ID: key,
                           DataParticleKey.VALUE: value})

        return result


class CtdgvParticleKey(GliderParticleKey):
    # science data made available via telemetry or Glider recovery
    SCI_CTD41CP_TIMESTAMP = 'sci_ctd41cp_timestamp'
    SCI_WATER_COND = 'sci_water_cond'
    SCI_WATER_PRESSURE = 'sci_water_pressure'
    SCI_WATER_TEMP = 'sci_water_temp'


class CtdgvTelemeteredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.CTDGV_M_GLIDER_INSTRUMENT
    science_parameters = CtdgvParticleKey.science_parameter_list()

    def _build_parsed_values(self):
        """
        Extracts CTDGV data from the glider data dictionary initialized with
        the particle class and puts the data into a CTDGV Telemetered Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        return self._parsed_values(CtdgvParticleKey.list())


class CtdgvRecoveredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.CTDGV_M_GLIDER_INSTRUMENT_RECOVERED
    science_parameters = CtdgvParticleKey.science_parameter_list()

    def _build_parsed_values(self):
        """
        Extracts CTDGV data from the glider data dictionary initialized with
        the particle class and puts the data into a CTDGV Recovered Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        return self._parsed_values(CtdgvParticleKey.list())


class DostaTelemeteredParticleKey(GliderParticleKey):
    # science data made available via telemetry
    SCI_OXY4_OXYGEN = 'sci_oxy4_oxygen'
    SCI_OXY4_SATURATION = 'sci_oxy4_saturation'


class DostaRecoveredParticleKey(GliderParticleKey):
    # science data made available via glider recovery
    SCI_OXY4_OXYGEN = 'sci_oxy4_oxygen'
    SCI_OXY4_SATURATION = 'sci_oxy4_saturation'
    SCI_OXY4_TIMESTAMP = 'sci_oxy4_timestamp'
    SCI_OXY4_C1AMP = 'sci_oxy4_c1amp'
    SCI_OXY4_C1RPH = 'sci_oxy4_c1rph'
    SCI_OXY4_C2AMP = 'sci_oxy4_c2amp'
    SCI_OXY4_C2RPH = 'sci_oxy4_c2rph'
    SCI_OXY4_CALPHASE = 'sci_oxy4_calphase'
    SCI_OXY4_RAWTEMP = 'sci_oxy4_rawtemp'
    SCI_OXY4_TCPHASE = 'sci_oxy4_tcphase'
    SCI_OXY4_TEMP = 'sci_oxy4_temp'
    SCI_WATER_COND = 'sci_water_cond'
    SCI_WATER_PRESSURE = 'sci_water_pressure'
    SCI_WATER_TEMP = 'sci_water_temp'


class DostaTelemeteredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.DOSTA_ABCDJM_GLIDER_INSTRUMENT
    science_parameters = DostaTelemeteredParticleKey.science_parameter_list()

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts DOSTA data from the
        data dictionary and puts the data into a DOSTA Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        return self._parsed_values(DostaTelemeteredParticleKey.list())


class DostaRecoveredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.DOSTA_ABCDJM_GLIDER_RECOVERED
    science_parameters = DostaRecoveredParticleKey.science_parameter_list()

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts DOSTA data from the
        data dictionary and puts the data into a DOSTA Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        return self._parsed_values(DostaRecoveredParticleKey.list())


class FlordParticleKey(GliderParticleKey):
    # science data made available via telemetry or glider recovery
    SCI_FLBB_TIMESTAMP = 'sci_flbb_timestamp'
    SCI_FLBB_BB_REF = 'sci_flbb_bb_ref'
    SCI_FLBB_BB_SIG = 'sci_flbb_bb_sig'
    SCI_FLBB_BB_UNITS = 'sci_flbb_bb_units'
    SCI_FLBB_CHLOR_REF = 'sci_flbb_chlor_ref'
    SCI_FLBB_CHLOR_SIG = 'sci_flbb_chlor_sig'
    SCI_FLBB_CHLOR_UNITS = 'sci_flbb_chlor_units'
    SCI_FLBB_THERM = 'sci_flbb_therm'


class FlordTelemeteredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.FLORD_M_GLIDER_INSTRUMENT
    science_parameters = FlordParticleKey.science_parameter_list()

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts FLORD data from the
        data dictionary and puts the data into a FLORD Telemetered Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        return self._parsed_values(FlordParticleKey.list())


class FlordRecoveredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.FLORD_M_GLIDER_INSTRUMENT_RECOVERED
    science_parameters = FlordParticleKey.science_parameter_list()

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts FLORD data from the
        data dictionary and puts the data into a FLORD Recovered Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        return self._parsed_values(FlordParticleKey.list())


class FlortTelemeteredParticleKey(GliderParticleKey):
    # science data made available via telemetry
    SCI_FLBBCD_BB_UNITS = 'sci_flbbcd_bb_units'
    SCI_FLBBCD_CDOM_UNITS = 'sci_flbbcd_cdom_units'
    SCI_FLBBCD_CHLOR_UNITS = 'sci_flbbcd_chlor_units'


class FlortRecoveredParticleKey(GliderParticleKey):
    # science data made available via glider recovery
    SCI_FLBBCD_TIMESTAMP = 'sci_flbbcd_timestamp'
    SCI_FLBBCD_BB_REF = 'sci_flbbcd_bb_ref'
    SCI_FLBBCD_BB_SIG = 'sci_flbbcd_bb_sig'
    SCI_FLBBCD_BB_UNITS = 'sci_flbbcd_bb_units'
    SCI_FLBBCD_CDOM_REF = 'sci_flbbcd_cdom_ref'
    SCI_FLBBCD_CDOM_SIG = 'sci_flbbcd_cdom_sig'
    SCI_FLBBCD_CDOM_UNITS = 'sci_flbbcd_cdom_units'
    SCI_FLBBCD_CHLOR_REF = 'sci_flbbcd_chlor_ref'
    SCI_FLBBCD_CHLOR_SIG = 'sci_flbbcd_chlor_sig'
    SCI_FLBBCD_CHLOR_UNITS = 'sci_flbbcd_chlor_units'
    SCI_FLBBCD_THERM = 'sci_flbbcd_therm'


class FlortTelemeteredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.FLORT_M_GLIDER_INSTRUMENT
    science_parameters = FlortTelemeteredParticleKey.science_parameter_list()

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts FLORT data from the
        data dictionary and puts the data into a FLORT Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        return self._parsed_values(FlortTelemeteredParticleKey.list())


class FlortRecoveredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.FLORT_M_GLIDER_RECOVERED
    science_parameters = FlortRecoveredParticleKey.science_parameter_list()

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts FLORT data from the
        data dictionary and puts the data into a FLORT Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        return self._parsed_values(FlortRecoveredParticleKey.list())


class ParadTelemeteredParticleKey(GliderParticleKey):
    # science data made available via telemetry
    SCI_BSIPAR_PAR = 'sci_bsipar_par'


class ParadRecoveredParticleKey(GliderParticleKey):
    # science data made available via glider recovery
    SCI_BSIPAR_PAR = 'sci_bsipar_par'
    SCI_BSIPAR_SENSOR_VOLTS = 'sci_bsipar_sensor_volts'
    SCI_BSIPAR_SUPPLY_VOLTS = 'sci_bsipar_supply_volts'
    SCI_BSIPAR_TEMP = 'sci_bsipar_temp'


class ParadTelemeteredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.PARAD_M_GLIDER_INSTRUMENT
    science_parameters = ParadTelemeteredParticleKey.science_parameter_list()

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts PARAD data from the
        data dictionary and puts the data into a PARAD Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        return self._parsed_values(ParadTelemeteredParticleKey.list())


class ParadRecoveredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.PARAD_M_GLIDER_RECOVERED
    science_parameters = ParadRecoveredParticleKey.science_parameter_list()

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts PARAD data from the
        data dictionary and puts the data into a PARAD Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        return self._parsed_values(ParadRecoveredParticleKey.list())


class EngineeringRecoveredParticleKey(GliderParticleKey):
    # engineering data made available via glider recovery
    M_ALTITUDE = 'm_altitude'
    M_DEPTH = 'm_depth'
    M_GPS_LAT = 'm_gps_lat'
    M_GPS_LON = 'm_gps_lon'
    M_LAT = 'm_lat'
    M_LON = 'm_lon'
    C_AIR_PUMP = 'c_air_pump'
    C_BALLAST_PUMPED = 'c_ballast_pumped'
    C_BATTPOS = 'c_battpos'
    C_BATTROLL = 'c_battroll'
    C_BSIPAR_ON = 'c_bsipar_on'
    C_DE_OIL_VOL = 'c_de_oil_vol'
    C_DVL_ON = 'c_dvl_on'
    C_FLBBCD_ON = 'c_flbbcd_on'
    C_HEADING = 'c_heading'
    C_OXY3835_WPHASE_ON = 'c_oxy3835_wphase_on'
    C_PITCH = 'c_pitch'
    C_PROFILE_ON = 'c_profile_on'
    C_WPT_LAT = 'c_wpt_lat'
    C_WPT_LON = 'c_wpt_lon'
    M_1MEG_PERSISTOR = 'm_1meg_persistor'
    M_AGROUND_WATER_DEPTH = 'm_aground_water_depth'
    M_AIR_FILL = 'm_air_fill'
    M_AIR_PUMP = 'm_air_pump'
    M_ALTIMETER_STATUS = 'm_altimeter_status'
    M_ALTIMETER_VOLTAGE = 'm_altimeter_voltage'
    M_ALTITUDE_RATE = 'm_altitude_rate'
    M_APPEAR_TO_BE_AT_SURFACE = 'm_appear_to_be_at_surface'
    M_ARGOS_IS_XMITTING = 'm_argos_is_xmitting'
    M_ARGOS_ON = 'm_argos_on'
    M_ARGOS_SENT_DATA = 'm_argos_sent_data'
    M_ARGOS_TIMESTAMP = 'm_argos_timestamp'
    M_AT_RISK_DEPTH = 'm_at_risk_depth'
    M_AVBOT_ENABLE = 'm_avbot_enable'
    M_AVBOT_POWER = 'm_avbot_power'
    M_AVG_CLIMB_RATE = 'm_avg_climb_rate'
    M_AVG_DEPTH_RATE = 'm_avg_depth_rate'
    M_AVG_DIVE_RATE = 'm_avg_dive_rate'
    M_AVG_DOWNWARD_INFLECTION_TIME = 'm_avg_downward_inflection_time'
    M_AVG_SPEED = 'm_avg_speed'
    M_AVG_SYSTEM_CLOCK_LAGS_GPS = 'm_avg_system_clock_lags_gps'
    M_AVG_UPWARD_INFLECTION_TIME = 'm_avg_upward_inflection_time'
    M_AVG_YO_TIME = 'm_avg_yo_time'
    M_BALLAST_PUMPED = 'm_ballast_pumped'
    M_BALLAST_PUMPED_ENERGY = 'm_ballast_pumped_energy'
    M_BALLAST_PUMPED_VEL = 'm_ballast_pumped_vel'
    M_BATTERY = 'm_battery'
    M_BATTERY_INST = 'm_battery_inst'
    M_BATTPOS = 'm_battpos'
    M_BATTPOS_VEL = 'm_battpos_vel'
    M_BATTROLL = 'm_battroll'
    M_BATTROLL_VEL = 'm_battroll_vel'
    M_BPUMP_FAULT_BIT = 'm_bpump_fault_bit'
    M_CERTAINLY_AT_SURFACE = 'm_certainly_at_surface'
    M_CHARS_TOSSED_BY_ABEND = 'm_chars_tossed_by_abend'
    M_CHARS_TOSSED_WITH_CD_OFF = 'm_chars_tossed_with_cd_off'
    M_CHARS_TOSSED_WITH_POWER_OFF = 'm_chars_tossed_with_power_off'
    M_CLIMB_TOT_TIME = 'm_climb_tot_time'
    M_CONSOLE_CD = 'm_console_cd'
    M_CONSOLE_ON = 'm_console_on'
    M_COP_TICKLE = 'm_cop_tickle'
    M_COULOMB_AMPHR = 'm_coulomb_amphr'
    M_COULOMB_AMPHR_RAW = 'm_coulomb_amphr_raw'
    M_COULOMB_AMPHR_TOTAL = 'm_coulomb_amphr_total'
    M_COULOMB_CURRENT = 'm_coulomb_current'
    M_COULOMB_CURRENT_RAW = 'm_coulomb_current_raw'
    M_CYCLE_NUMBER = 'm_cycle_number'
    M_DEPTH_RATE = 'm_depth_rate'
    M_DEPTH_RATE_AVG_FINAL = 'm_depth_rate_avg_final'
    M_DEPTH_RATE_RUNNING_AVG = 'm_depth_rate_running_avg'
    M_DEPTH_RATE_RUNNING_AVG_N = 'm_depth_rate_running_avg_n'
    M_DEPTH_RATE_SUBSAMPLED = 'm_depth_rate_subsampled'
    M_DEPTH_REJECTED = 'm_depth_rejected'
    M_DEPTH_STATE = 'm_depth_state'
    M_DEPTH_SUBSAMPLED = 'm_depth_subsampled'
    M_DEVICE_DRIVERS_CALLED_ABNORMALLY = 'm_device_drivers_called_abnormally'
    M_DEVICE_ERROR = 'm_device_error'
    M_DEVICE_ODDITY = 'm_device_oddity'
    M_DEVICE_WARNING = 'm_device_warning'
    M_DE_OIL_VOL = 'm_de_oil_vol'
    M_DE_OIL_VOL_POT_VOLTAGE = 'm_de_oil_vol_pot_voltage'
    M_DE_PUMP_FAULT_COUNT = 'm_de_pump_fault_count'
    M_DIGIFIN_CMD_DONE = 'm_digifin_cmd_done'
    M_DIGIFIN_CMD_ERROR = 'm_digifin_cmd_error'
    M_DIGIFIN_LEAKDETECT_READING = 'm_digifin_leakdetect_reading'
    M_DIGIFIN_MOTORSTEP_COUNTER = 'm_digifin_motorstep_counter'
    M_DIGIFIN_RESP_DATA = 'm_digifin_resp_data'
    M_DIGIFIN_STATUS = 'm_digifin_status'
    M_DISK_FREE = 'm_disk_free'
    M_DISK_USAGE = 'm_disk_usage'
    M_DIST_TO_WPT = 'm_dist_to_wpt'
    M_DIVE_DEPTH = 'm_dive_depth'
    M_DIVE_TOT_TIME = 'm_dive_tot_time'
    M_DR_FIX_TIME = 'm_dr_fix_time'
    M_DR_POSTFIX_TIME = 'm_dr_postfix_time'
    M_DR_SURF_X_LMC = 'm_dr_surf_x_lmc'
    M_DR_SURF_Y_LMC = 'm_dr_surf_y_lmc'
    M_DR_TIME = 'm_dr_time'
    M_DR_X_ACTUAL_ERR = 'm_dr_x_actual_err'
    M_DR_X_INI_ERR = 'm_dr_x_ini_err'
    M_DR_X_POSTFIX_DRIFT = 'm_dr_x_postfix_drift'
    M_DR_X_TA_POSTFIX_DRIFT = 'm_dr_x_ta_postfix_drift'
    M_DR_Y_ACTUAL_ERR = 'm_dr_y_actual_err'
    M_DR_Y_INI_ERR = 'm_dr_y_ini_err'
    M_DR_Y_POSTFIX_DRIFT = 'm_dr_y_postfix_drift'
    M_DR_Y_TA_POSTFIX_DRIFT = 'm_dr_y_ta_postfix_drift'
    M_EST_TIME_TO_SURFACE = 'm_est_time_to_surface'
    M_FIN = 'm_fin'
    M_FINAL_WATER_VX = 'm_final_water_vx'
    M_FINAL_WATER_VY = 'm_final_water_vy'
    M_FIN_VEL = 'm_fin_vel'
    M_FLUID_PUMPED = 'm_fluid_pumped'
    M_FLUID_PUMPED_AFT_HALL_VOLTAGE = 'm_fluid_pumped_aft_hall_voltage'
    M_FLUID_PUMPED_FWD_HALL_VOLTAGE = 'm_fluid_pumped_fwd_hall_voltage'
    M_FLUID_PUMPED_VEL = 'm_fluid_pumped_vel'
    M_FREE_HEAP = 'm_free_heap'
    M_GPS_DIST_FROM_DR = 'm_gps_dist_from_dr'
    M_GPS_FIX_X_LMC = 'm_gps_fix_x_lmc'
    M_GPS_FIX_Y_LMC = 'm_gps_fix_y_lmc'
    M_GPS_FULL_STATUS = 'm_gps_full_status'
    M_GPS_HEADING = 'm_gps_heading'
    M_GPS_IGNORED_LAT = 'm_gps_ignored_lat'
    M_GPS_IGNORED_LON = 'm_gps_ignored_lon'
    M_GPS_INVALID_LAT = 'm_gps_invalid_lat'
    M_GPS_INVALID_LON = 'm_gps_invalid_lon'
    M_GPS_MAG_VAR = 'm_gps_mag_var'
    M_GPS_NUM_SATELLITES = 'm_gps_num_satellites'
    M_GPS_ON = 'm_gps_on'
    M_GPS_POSTFIX_X_LMC = 'm_gps_postfix_x_lmc'
    M_GPS_POSTFIX_Y_LMC = 'm_gps_postfix_y_lmc'
    M_GPS_STATUS = 'm_gps_status'
    M_GPS_SPEED = 'm_gps_speed'
    M_GPS_TOOFAR_LAT = 'm_gps_toofar_lat'
    M_GPS_TOOFAR_LON = 'm_gps_toofar_lon'
    M_GPS_UNCERTAINTY = 'm_gps_uncertainty'
    M_GPS_UTC_DAY = 'm_gps_utc_day'
    M_GPS_UTC_HOUR = 'm_gps_utc_hour'
    M_GPS_UTC_MINUTE = 'm_gps_utc_minute'
    M_GPS_UTC_MONTH = 'm_gps_utc_month'
    M_GPS_UTC_SECOND = 'm_gps_utc_second'
    M_GPS_UTC_YEAR = 'm_gps_utc_year'
    M_GPS_X_LMC = 'm_gps_x_lmc'
    M_GPS_Y_LMC = 'm_gps_y_lmc'
    M_HDG_DERROR = 'm_hdg_derror'
    M_HDG_ERROR = 'm_hdg_error'
    M_HDG_IERROR = 'm_hdg_ierror'
    M_HDG_RATE = 'm_hdg_rate'
    M_HEADING = 'm_heading'
    M_INITIAL_WATER_VX = 'm_initial_water_vx'
    M_INITIAL_WATER_VY = 'm_initial_water_vy'
    M_IRIDIUM_ATTEMPT_NUM = 'm_iridium_attempt_num'
    M_IRIDIUM_CALL_NUM = 'm_iridium_call_num'
    M_IRIDIUM_CONNECTED = 'm_iridium_connected'
    M_IRIDIUM_CONSOLE_ON = 'm_iridium_console_on'
    M_IRIDIUM_DIALED_NUM = 'm_iridium_dialed_num'
    M_IRIDIUM_ON = 'm_iridium_on'
    M_IRIDIUM_REDIALS = 'm_iridium_redials'
    M_IRIDIUM_SIGNAL_STRENGTH = 'm_iridium_signal_strength'
    M_IRIDIUM_STATUS = 'm_iridium_status'
    M_IRIDIUM_WAITING_REDIAL_DELAY = 'm_iridium_waiting_redial_delay'
    M_IRIDIUM_WAITING_REGISTRATION = 'm_iridium_waiting_registration'
    M_IS_BALLAST_PUMP_MOVING = 'm_is_ballast_pump_moving'
    M_IS_BATTPOS_MOVING = 'm_is_battpos_moving'
    M_IS_BATTROLL_MOVING = 'm_is_battroll_moving'
    M_IS_DE_PUMP_MOVING = 'm_is_de_pump_moving'
    M_IS_FIN_MOVING = 'm_is_fin_moving'
    M_IS_FPITCH_PUMP_MOVING = 'm_is_fpitch_pump_moving'
    M_IS_SPEED_ESTIMATED = 'm_is_speed_estimated'
    M_IS_THERMAL_VALVE_MOVING = 'm_is_thermal_valve_moving'
    M_LAST_YO_TIME = 'm_last_yo_time'
    M_LEAK = 'm_leak'
    M_LEAKDETECT_VOLTAGE = 'm_leakdetect_voltage'
    M_LEAKDETECT_VOLTAGE_FORWARD = 'm_leakdetect_voltage_forward'
    M_LEAK_FORWARD = 'm_leak_forward'
    M_LITHIUM_BATTERY_RELATIVE_CHARGE = 'm_lithium_battery_relative_charge'
    M_LITHIUM_BATTERY_STATUS = 'm_lithium_battery_status'
    M_LITHIUM_BATTERY_TIME_TO_CHARGE = 'm_lithium_battery_time_to_charge'
    M_LITHIUM_BATTERY_TIME_TO_DISCHARGE = 'm_lithium_battery_time_to_discharge'
    M_MIN_FREE_HEAP = 'm_min_free_heap'
    M_MIN_SPARE_HEAP = 'm_min_spare_heap'
    M_MISSION_AVG_SPEED_CLIMBING = 'm_mission_avg_speed_climbing'
    M_MISSION_AVG_SPEED_DIVING = 'm_mission_avg_speed_diving'
    M_MISSION_START_TIME = 'm_mission_start_time'
    M_NUM_HALF_YOS_IN_SEGMENT = 'm_num_half_yos_in_segment'
    M_PITCH = 'm_pitch'
    M_PITCH_ENERGY = 'm_pitch_energy'
    M_PITCH_ERROR = 'm_pitch_error'
    M_PRESSURE = 'm_pressure'
    M_PRESSURE_RAW_VOLTAGE_SAMPLE0 = 'm_pressure_raw_voltage_sample0'
    M_PRESSURE_RAW_VOLTAGE_SAMPLE19 = 'm_pressure_raw_voltage_sample19'
    M_PRESSURE_VOLTAGE = 'm_pressure_voltage'
    M_RAW_ALTITUDE = 'm_raw_altitude'
    M_RAW_ALTITUDE_REJECTED = 'm_raw_altitude_rejected'
    M_ROLL = 'm_roll'
    M_SCIENCE_CLOTHESLINE_LAG = 'm_science_clothesline_lag'
    M_SCIENCE_ON = 'm_science_on'
    M_SCIENCE_READY_FOR_CONSCI = 'm_science_ready_for_consci'
    M_SCIENCE_SENT_SOME_DATA = 'm_science_sent_some_data'
    M_SCIENCE_SYNC_TIME = 'm_science_sync_time'
    M_SCIENCE_UNREADINESS_FOR_CONSCI = 'm_science_unreadiness_for_consci'
    M_SPARE_HEAP = 'm_spare_heap'
    M_SPEED = 'm_speed'
    M_STABLE_COMMS = 'm_stable_comms'
    M_STROBE_CTRL = 'm_strobe_ctrl'
    M_SURFACE_EST_CMD = 'm_surface_est_cmd'
    M_SURFACE_EST_CTD = 'm_surface_est_ctd'
    M_SURFACE_EST_FW = 'm_surface_est_fw'
    M_SURFACE_EST_GPS = 'm_surface_est_gps'
    M_SURFACE_EST_IRID = 'm_surface_est_irid'
    M_SURFACE_EST_TOTAL = 'm_surface_est_total'
    M_SYSTEM_CLOCK_LAGS_GPS = 'm_system_clock_lags_gps'
    M_TCM3_IS_CALIBRATED = 'm_tcm3_is_calibrated'
    M_TCM3_MAGBEARTH = 'm_tcm3_magbearth'
    M_TCM3_POLL_TIME = 'm_tcm3_poll_time'
    M_TCM3_RECV_START_TIME = 'm_tcm3_recv_start_time'
    M_TCM3_RECV_STOP_TIME = 'm_tcm3_recv_stop_time'
    M_TCM3_STDDEVERR = 'm_tcm3_stddeverr'
    M_TCM3_XCOVERAGE = 'm_tcm3_xcoverage'
    M_TCM3_YCOVERAGE = 'm_tcm3_ycoverage'
    M_TCM3_ZCOVERAGE = 'm_tcm3_zcoverage'
    M_THERMAL_ACC_PRES = 'm_thermal_acc_pres'
    M_THERMAL_ACC_PRES_VOLTAGE = 'm_thermal_acc_pres_voltage'
    M_THERMAL_ACC_VOL = 'm_thermal_acc_vol'
    M_THERMAL_ENUF_ACC_VOL = 'm_thermal_enuf_acc_vol'
    M_THERMAL_PUMP = 'm_thermal_pump'
    M_THERMAL_UPDOWN = 'm_thermal_updown'
    M_THERMAL_VALVE = 'm_thermal_valve'
    M_TIME_TIL_WPT = 'm_time_til_wpt'
    M_TOT_BALLAST_PUMPED_ENERGY = 'm_tot_ballast_pumped_energy'
    M_TOT_HORZ_DIST = 'm_tot_horz_dist'
    M_TOT_NUM_INFLECTIONS = 'm_tot_num_inflections'
    M_TOT_ON_TIME = 'm_tot_on_time'
    M_VACUUM = 'm_vacuum'
    M_VEHICLE_TEMP = 'm_vehicle_temp'
    M_VEH_OVERHEAT = 'm_veh_overheat'
    M_VEH_TEMP = 'm_veh_temp'
    M_VMG_TO_WPT = 'm_vmg_to_wpt'
    M_VX_LMC = 'm_vx_lmc'
    M_VY_LMC = 'm_vy_lmc'
    M_WATER_COND = 'm_water_cond'
    M_WATER_DELTA_VX = 'm_water_delta_vx'
    M_WATER_DELTA_VY = 'm_water_delta_vy'
    M_WATER_DEPTH = 'm_water_depth'
    M_WATER_PRESSURE = 'm_water_pressure'
    M_WATER_TEMP = 'm_water_temp'
    M_WATER_VX = 'm_water_vx'
    M_WATER_VY = 'm_water_vy'
    M_WHY_STARTED = 'm_why_started'
    M_X_LMC = 'm_x_lmc'
    M_Y_LMC = 'm_y_lmc'
    X_LAST_WPT_LAT = 'x_last_wpt_lat'
    X_LAST_WPT_LON = 'x_last_wpt_lon'
    X_SYSTEM_CLOCK_ADJUSTED = 'x_system_clock_adjusted'


class EngineeringScienceRecoveredParticleKey(GliderParticleKey):
    # science data made available via glider recovery
    SCI_M_DISK_FREE = 'sci_m_disk_free'
    SCI_M_DISK_USAGE = 'sci_m_disk_usage'
    SCI_M_FREE_HEAP = 'sci_m_free_heap'
    SCI_M_MIN_FREE_HEAP = 'sci_m_min_free_heap'
    SCI_M_MIN_SPARE_HEAP = 'sci_m_min_spare_heap'
    SCI_M_SCIENCE_ON = 'sci_m_science_on'
    SCI_CTD41CP_IS_INSTALLED = 'sci_ctd41cp_is_installed'
    SCI_BSIPAR_IS_INSTALLED = 'sci_bsipar_is_installed'
    SCI_FLBBCD_IS_INSTALLED = 'sci_flbbcd_is_installed'
    SCI_OXY3835_WPHASE_IS_INSTALLED = 'sci_oxy3835_wphase_is_installed'
    SCI_OXY4_IS_INSTALLED = 'sci_oxy4_is_installed'
    SCI_DVL_IS_INSTALLED = 'sci_dvl_is_installed'
    SCI_M_SPARE_HEAP = 'sci_m_spare_heap'
    SCI_REQD_HEARTBEAT = 'sci_reqd_heartbeat'
    SCI_SOFTWARE_VER = 'sci_software_ver'
    SCI_WANTS_COMMS = 'sci_wants_comms'
    SCI_WANTS_SURFACE = 'sci_wants_surface'
    SCI_X_DISK_FILES_REMOVED = 'sci_x_disk_files_removed'
    SCI_X_SENT_DATA_FILES = 'sci_x_sent_data_files'


class EngineeringMetadataParticleKey(GliderParticleKey):
    # science data made available via glider recovery
    GLIDER_ENG_FILENAME = 'glider_eng_filename'
    GLIDER_MISSION_NAME = 'glider_mission_name'
    GLIDER_ENG_FILEOPEN_TIME = 'glider_eng_fileopen_time'


class EngineeringTelemeteredParticleKey(GliderParticleKey):
    # engineering data made available via telemetry
    M_GPS_LAT = 'm_gps_lat'
    M_GPS_LON = 'm_gps_lon'
    M_LAT = 'm_lat'
    M_LON = 'm_lon'
    C_BATTPOS = 'c_battpos'
    C_BALLAST_PUMPED = 'c_ballast_pumped'
    C_DE_OIL_VOL = 'c_de_oil_vol'
    C_DVL_ON = 'c_dvl_on'
    C_HEADING = 'c_heading'
    C_PITCH = 'c_pitch'
    C_WPT_LAT = 'c_wpt_lat'
    C_WPT_LON = 'c_wpt_lon'
    M_AIR_PUMP = 'm_air_pump'
    M_ALTITUDE = 'm_altitude'
    M_BALLAST_PUMPED = 'm_ballast_pumped'
    M_BATTERY = 'm_battery'
    M_BATTPOS = 'm_battpos'
    M_COULOMB_AMPHR = 'm_coulomb_amphr'
    M_COULOMB_AMPHR_TOTAL = 'm_coulomb_amphr_total'
    M_COULOMB_CURRENT = 'm_coulomb_current'
    M_DEPTH = 'm_depth'
    M_DE_OIL_VOL = 'm_de_oil_vol'
    M_FIN = 'm_fin'
    M_HEADING = 'm_heading'
    M_LITHIUM_BATTERY_RELATIVE_CHARGE = 'm_lithium_battery_relative_charge'
    M_PITCH = 'm_pitch'
    M_PRESSURE = 'm_pressure'
    M_SPEED = 'm_speed'
    M_RAW_ALTITUDE = 'm_raw_altitude'
    M_ROLL = 'm_roll'
    M_VACUUM = 'm_vacuum'
    M_WATER_DEPTH = 'm_water_depth'
    M_WATER_VX = 'm_water_vx'
    M_WATER_VY = 'm_water_vy'


class EngineeringScienceTelemeteredParticleKey(GliderParticleKey):
    # engineering data made available via telemetry
    SCI_M_DISK_FREE = 'sci_m_disk_free'
    SCI_M_DISK_USAGE = 'sci_m_disk_usage'


class EngineeringTelemeteredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.GLIDER_ENG_TELEMETERED
    science_parameters = EngineeringTelemeteredParticleKey.science_parameter_list()
    
    keys_exclude_sci_times = EngineeringTelemeteredParticleKey.list()
    keys_exclude_sci_times.remove(GliderParticleKey.SCI_M_PRESENT_TIME)
    keys_exclude_sci_times.remove(GliderParticleKey.SCI_M_PRESENT_SECS_INTO_MISSION)

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts engineering data from the
        data dictionary and puts the data into a engineering Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        # need to exclude sci times
        return self._parsed_values(EngineeringTelemeteredDataParticle.keys_exclude_sci_times)


class EngineeringMetadataDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.GLIDER_ENG_METADATA
    science_parameters = EngineeringMetadataParticleKey.science_parameter_list()

    keys_exclude_times = EngineeringMetadataParticleKey.list()
    keys_exclude_times.remove(GliderParticleKey.M_PRESENT_TIME)
    keys_exclude_times.remove(GliderParticleKey.M_PRESENT_SECS_INTO_MISSION)
    keys_exclude_times.remove(GliderParticleKey.SCI_M_PRESENT_TIME)
    keys_exclude_times.remove(GliderParticleKey.SCI_M_PRESENT_SECS_INTO_MISSION)

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts engineering metadata from the
        header and puts the data into a Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        # need to exclude m times
        return self._parsed_values(EngineeringMetadataDataParticle.keys_exclude_times)


class EngineeringMetadataRecoveredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.GLIDER_ENG_METADATA_RECOVERED
    science_parameters = EngineeringMetadataParticleKey.science_parameter_list()

    keys_exclude_times = EngineeringMetadataParticleKey.list()
    keys_exclude_times.remove(GliderParticleKey.M_PRESENT_TIME)
    keys_exclude_times.remove(GliderParticleKey.M_PRESENT_SECS_INTO_MISSION)
    keys_exclude_times.remove(GliderParticleKey.SCI_M_PRESENT_TIME)
    keys_exclude_times.remove(GliderParticleKey.SCI_M_PRESENT_SECS_INTO_MISSION)

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts engineering metadata from the
        header and puts the data into a Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        # need to exclude all times
        return self._parsed_values(EngineeringMetadataDataParticle.keys_exclude_times)


class EngineeringScienceTelemeteredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.GLIDER_ENG_SCI_TELEMETERED
    science_parameters = EngineeringScienceTelemeteredParticleKey.science_parameter_list()
    
    keys_exclude_times = EngineeringScienceTelemeteredParticleKey.list()
    keys_exclude_times.remove(GliderParticleKey.M_PRESENT_TIME)
    keys_exclude_times.remove(GliderParticleKey.M_PRESENT_SECS_INTO_MISSION)

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts engineering data from the
        data dictionary and puts the data into a engineering Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        # need to exclude m times
        return self._parsed_values(EngineeringScienceTelemeteredDataParticle.keys_exclude_times)


class EngineeringRecoveredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.GLIDER_ENG_RECOVERED
    science_parameters = EngineeringRecoveredParticleKey.science_parameter_list()
    
    keys_exclude_sci_times = EngineeringRecoveredParticleKey.list()
    keys_exclude_sci_times.remove(GliderParticleKey.SCI_M_PRESENT_TIME)
    keys_exclude_sci_times.remove(GliderParticleKey.SCI_M_PRESENT_SECS_INTO_MISSION)

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts engineering data from the
        data dictionary and puts the data into a engineering Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        # need to exclude sci times
        return self._parsed_values(EngineeringRecoveredDataParticle.keys_exclude_sci_times)


class EngineeringScienceRecoveredDataParticle(GliderParticle):
    _data_particle_type = DataParticleType.GLIDER_ENG_SCI_RECOVERED
    science_parameters = EngineeringScienceRecoveredParticleKey.science_parameter_list()
    
    keys_exclude_times = EngineeringScienceRecoveredParticleKey.list()
    keys_exclude_times.remove(GliderParticleKey.M_PRESENT_TIME)
    keys_exclude_times.remove(GliderParticleKey.M_PRESENT_SECS_INTO_MISSION)

    def _build_parsed_values(self):
        """
        Takes a GliderParser object and extracts engineering data from the
        data dictionary and puts the data into a engineering Data Particle.

        @returns result a list of dictionaries of particle data
        @throws SampleException if the data is not a glider data dictionary
        """
        # need to exclude m times
        return self._parsed_values(EngineeringScienceRecoveredDataParticle.keys_exclude_times)


class GliderParser(SimpleParser):
    """
    GliderParser parses a Slocum Electric Glider data file that has been
    converted to ASCII from binary and merged with it's corresponding flight or
    science data file, and holds the self describing header data in a header
    dictionary and the data in a data dictionary using the column labels as the
    dictionary keys. These dictionaries are used to build the particles.
    """
    def __init__(self,
                 config,
                 stream_handle,
                 exception_callback):

        self._stream_handle = stream_handle
        self._record_buffer = []  # holds tuples of (record, state)
        self._header_dict = {}

        # Read and store the configuration found in the 14 line header
        self._read_file_definition()
        # Read and store the information found in the 3 lines of column labels
        self._read_column_labels()


        super(GliderParser, self).__init__(config,
                                           self._stream_handle,
                                           exception_callback)


    def _read_file_definition(self):
        """
        Read the first 14 lines of the data file for the file definitions, values
        are colon delimited key value pairs. The pairs are parsed and stored in
        header_dict member.
        """
        row_count = 0
        #
        # THIS METHOD ASSUMES A 14 ROW HEADER
        # If the number of header row lines in the glider ASCII input file changes from 14,
        # this method will NOT WORK
        num_hdr_lines = 14

        header_pattern = r'(.*): (.*)$'
        header_re = re.compile(header_pattern)

        while row_count < num_hdr_lines:
            line = self._stream_handle.readline()

            # check if this line is empty
            if len(line) == 0:
                raise SampleException("GliderParser._read_file_definition(): Header line is empty")

            match = header_re.match(line)

            if match:
                key = match.group(1)
                value = match.group(2)
                value = value.strip()
                #log.debug("header key: %s, value: %s", key, value)

                # update num_hdr_lines based on the header info.
                if key in ['num_ascii_tags', 'num_label_lines', 'sensors_per_cycle']:
                    value = int(value)

                    # create a dictionary of these 3 key/value pairs integers from
                    # the header rows that need to be saved for future use
                    self._header_dict[key] = value

                elif key in ['filename_label', 'mission_name', 'fileopen_time']:

                    # create a dictionary of these 3 key/value pairs strings from
                    # the header rows that need to be saved for future use
                    self._header_dict[key] = value

            else:
                log.warn("Failed to parse header row: %s.", line)

            row_count += 1

        num_ascii_tags_value = self._header_dict.get('num_ascii_tags')

        if num_ascii_tags_value != num_hdr_lines:
            raise UnexpectedDataException("GliderParser._read_file_definition(): "
                                          "Header is not 14 rows, num_ascii_tags = %s" % num_ascii_tags_value)


    def _read_column_labels(self):
        """
        Read the next three lines to populate column data.

        1st Row (row 15 of file) == labels
        2nd Row (row 16 of file) == units
        3rd Row (row 17 of file) == column byte size

        Currently we are only able to support 3 label line rows. If num_label_lines != 3 then raise an exception.
        """
        num_columns = self._header_dict['sensors_per_cycle']

        num_label_lines_value = self._header_dict.get('num_label_lines')

        if num_label_lines_value != 3:
            raise SampleException("There must be 3 Label lines from the header for this parser")

        label_list = self._stream_handle.readline().strip().split()
        label_list_length = len(label_list)

        if label_list_length != num_columns:
            raise SampleException("The number of Label values must equal the number of columns defined by "
                                  "sensors_per_cycle, %s does not equal %d"
                                  % (label_list_length, num_label_lines_value))
        else:
            self._header_dict['labels'] = label_list

        data_unit_list = self._stream_handle.readline().strip().split()
        data_unit_list_length = len(data_unit_list)

        if data_unit_list_length != num_columns:
            raise SampleException("The number of Units values must equal the number of columns defined by "
                                  "sensors_per_cycle, %s does not equal %d"
                                  % (data_unit_list_length, num_label_lines_value))
        else:
            self._header_dict['data_units'] = data_unit_list

        # read the next line from the file (should be at row 17 of the file at this point)
        num_of_bytes_list = self._stream_handle.readline().strip().split()
        num_of_bytes_list_length = len(num_of_bytes_list)

        if num_of_bytes_list_length != num_columns:
            raise SampleException("The number of Byte values must equal the number of columns defined by "
                                  "sensors_per_cycle, %s does not equal %d"
                                  % (num_of_bytes_list_length, num_label_lines_value))
        else:
            # convert each number of bytes string value into an int
            num_of_bytes_list = map(int, num_of_bytes_list)
            self._header_dict['num_of_bytes'] = num_of_bytes_list

        log.debug("Label count: %d", len(self._header_dict['labels']))
        log.trace("Labels: %s", self._header_dict['labels'])
        log.trace("Data units: %s", self._header_dict['data_units'])
        log.trace("Bytes: %s", self._header_dict['num_of_bytes'])

        log.debug("End of header, position: %d", self._stream_handle.tell())

    def _read_data(self, data_record):
        """
        Read in the column labels, data type, number of bytes of each
        data type, and the data from an ASCII glider data file.
        @throws SampleException if the number of columns does not match the expected number
        """
        data_dict = {}
        num_columns = self._header_dict['sensors_per_cycle']
        data_labels = self._header_dict['labels']
        num_bytes = self._header_dict['num_of_bytes']
        data = data_record.strip().split()

        if num_columns != len(data):
            err_msg = "GliderParser._read_data(): Num Of Columns NOT EQUAL to Num of Data items: " + \
                      "Expected Columns= %s vs Actual Data= %s" % (num_columns, len(data))
            log.error(err_msg)
            raise SampleException(err_msg)

        # extract record to dictionary
        for ii, value in enumerate(data):
            nbytes = num_bytes[ii]
            label = data_labels[ii]

            if value == 'NaN':
                value = float(value)
            elif '_lat' in label or '_lon' in label:
                value = self._string_to_ddegrees(value)
            else:
                if nbytes in [1, 2]:
                    value = int(value)
                elif nbytes in [4, 8]:
                    value = float(value)

            data_dict[label] = value

        return data_dict

    def parse_file(self):
        """
        Create particles out of chunks and raise an event
        @retval a list of tuples with sample particles encountered in this
            parsing, plus the state. An empty list is returned if nothing was
            parsed.
        """
        for line in self._stream_handle:
            try:
                # create the dictionary of key/value pairs composed of the labels and the values from the
                # record being parsed
                # ex: data_dict = {'sci_bsipar_temp':10.67, n1, n2, nn}
                data_dict = self._read_data(line)
                timestamp = ntplib.system_to_ntp_time(data_dict['m_present_time'])

            except SampleException as e:
                log.error('Exception parsing line: %s', e)
                self._exception_callback(e)
                continue

            except KeyError as e:
                log.error('KEY ERROR: %s', e)
                self._exception_callback(SampleException("GliderParser.parse_chunks(): unable to find timestamp in data"))
                continue

            if self._has_science_data(data_dict, self._particle_class):
                # create the particle
                self._record_buffer.append(self._extract_sample(self._particle_class, None, data_dict, timestamp))

    def _has_science_data(self, data_dict, particle_class):
        """
        Examine the data_dict to see if it contains particle parameters
        """
        for key, value in data_dict.iteritems():
                if not isnan(value) and key in particle_class.science_parameters:
                    return True

    def _string_to_ddegrees(self, pos_str):
        """
        Converts the given string from this data stream into a more
        standard latitude/longitude value in decimal degrees.
        @param pos_str The position (latitude or longitude) string in the
           format "DDMM.MMMM" for latitude and "DDDMM.MMMM" for longitude. A
           positive or negative sign to the string indicates northern/southern
           or eastern/western hemispheres, respectively.
        @retval The position in decimal degrees
        """
        # As a stop gap fix add a .0 to integers that don't contain a decimal.  This
        # should only affect the engineering stream as the science data streams shouldn't
        # contain lat lon
        if not "." in pos_str:
            pos_str += ".0"

        # if there are not enough numbers to fill in DDMM, prepend zeros
        str_words = pos_str.split('.')
        adj_zeros = 4 - len(str_words[0])
        if adj_zeros > 0:
            for i in range(0, adj_zeros):
                pos_str = '0' + pos_str

        regex = r'(-*\d{2,3})(\d{2}.\d+)'
        regex_matcher = re.compile(regex)
        latlon_match = regex_matcher.match(pos_str)

        if latlon_match is None:
            log.error("Failed to parse lat/lon value: '%s'", pos_str)
            self._exception_callback(SampleException("GliderParser._string_to_ddegrees(): Failed to parse lat/lon value: '%s'" % pos_str))
            ddegrees = None
        else:
            degrees = float(latlon_match.group(1))
            minutes = float(latlon_match.group(2))
            ddegrees = copysign((abs(degrees) + minutes / 60.), degrees)

        return ddegrees


class GliderEngineeringParser(GliderParser):
    def __init__(self,
                 config,
                 stream_handle,
                 exception_callback):

        super(GliderEngineeringParser, self).__init__(config,
                                                      stream_handle,
                                                      exception_callback)

        self.list_of_particles_to_produce = config.get('particle_class', [])
        self._metadata_sent = False

    def parse_file(self):
        """
        Create particles out of chunks and raise an event
        @retval a list of tuples with sample particles encountered in this
            parsing, plus the state. An empty list is returned if nothing was
            parsed.
        """
        for data_record in self._stream_handle:
            try:
                # create the dictionary of key/value pairs composed of the labels and the values from the
                # record being parsed
                data_dict = self._read_data(data_record)
                timestamp = ntplib.system_to_ntp_time(data_dict['m_present_time'])

            except SampleException as e:
                self._exception_callback(e)
                log.warn("GliderEngineeringParser.parse_chunks(): "
                         "Sample Exception, problem creating data dict from raw data %s", e)
                continue

            except KeyError:
                self._exception_callback(SampleException(" ## ## ## GliderEngineeringParser.parse_chunks(): "
                                                         "unable to find timestamp in data"))
                continue

            for particle in self.list_of_particles_to_produce:
                # handle this particle if it is an engineering metadata particle
                if not self._metadata_sent:
                    self._record_buffer.extend(self.handle_metadata_particle(particle, timestamp))

                # check for the presence of any particle data in the raw data row before continuing
                if self._has_science_data(data_dict, particle):
                    try:
                        self._record_buffer.append(self._extract_sample(particle, None, data_dict, timestamp))
                    except RecoverableSampleException:
                        self._exception_callback(
                            RecoverableSampleException("GliderEngineeringParser.parse_chunks(): "
                                                       "Particle class not defined in glider module"))

    def handle_metadata_particle(self, particle, timestamp):
        """
        Check if this particle is an engineering metadata particle that hasn't already been produced, ensure the
        metadata particle is produced only once
        """
        header_info_data_dict = self.get_header_info_dict()

        try:
            particle = self._extract_sample(particle, None, header_info_data_dict, timestamp)
            self._metadata_sent = True
            return [particle]
        except RecoverableSampleException:
            self._exception_callback(
                RecoverableSampleException("GliderEngineeringParser.handle_metadata_particle(): "
                                           "Particle class not defined in glider module"))
            return []


    def get_header_info_dict(self):
        """
        Add the three file information attributes to the data dictionary (file name,
        mission name, time the file was opened)
        """

        # data_dict holds key, value pairs where
        # key = particle attribute name
        # value = value of particle data item
        #
        filename_label_value = self._header_dict.get('filename_label')
        mission_name_value = self._header_dict.get('mission_name')
        fileopen_time_value = self._header_dict.get('fileopen_time')

        # ADD the three dicts to the data dict
        header_data_dict = {}
        header_data_dict['glider_eng_filename'] = filename_label_value
        header_data_dict['glider_mission_name'] = mission_name_value
        header_data_dict['glider_eng_fileopen_time'] = fileopen_time_value

        return header_data_dict
