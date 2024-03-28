import struct

class ITSConverter(object):
    class ITSConverterError(Exception):
        def __init__(self, message, ex=None):
            self.__ex = ex
            self.__message = message

        def error_message(self):
            return self.__message

    EL_BASE_STATION_HEADER_SIZE = 6
    EL_MOBILE_STATION_HEADER_SIZE = 1
    EL_HEADER_SIZE = EL_BASE_STATION_HEADER_SIZE
    COMMON_SIZE = 8
    TIME_SIZE = 4
    POSITION_SIZE = 11
    VEHICLE_STATUS_SIZE = 9
    VEHICLE_ATTRIBUTE_SIZE = 4
    POSITION_OPTION_SIZE = 2
    GNSS_STAT_OPTION_SIZE = 4
    POSITION_ACQUISITION_OPTION_SIZE = 2
    VEHICLE_STATUS_OPTION_SIZE = 7
    INTERSECTION_OPTION_SIZE = 10
    EXTENDED_INFORMATION_OPTION_SIZE = 1

    APP_OPTION_SIZE = 1 
    INDIV_APP_DATA_MANAGEMENT_INFO_SIZE = 3

    EL_MOBILE_STATION_HEADER_KC = '0'
    EL_MOBILE_STATION_HEADER = '1'
    EL_BASE_STATION_HEADER = '2'

    @classmethod
    def complement(cls, val, bits):
        return -(val & (1 << (bits-1))) | val

    def __init__(self):
        self._reset()

    def _reset(self):
        self.output = {}
        self.ptr = 0
        self.is_prepared = False

    def __dump_common(self, packet_data):
        if len(packet_data) < self.COMMON_SIZE:
            raise self.ITSConverterError('Data length is too short. '
                                         '[COMMON]Length : {}, Expected : {}'.format(len(packet_data),
                                                                                     self.COMMON_SIZE))

        # 1-1 DE_CommonServiceStandardID (3bit)
        comServStdId = (packet_data[0] & 0xe0) >> 5
        self.output['CommonServiceStandardID'] = str(comServStdId)

        # 1-2 DE_MessageID (2bit)
        msgID = (packet_data[0] & 0x18) >> 3
        self.output['MessageID'] = str(msgID)

        # 1-3 DE_Version (3bit)
        Ver =   (packet_data[0] & 0x07)
        self.output['Version'] = Ver

        # 1-4 DE_VehicleID (32bit)
        vID = ''
        for i in range(1, 5):
            vID += '{:02x}'.format(packet_data[i])
        self.output['VehicleID'] = vID

        # 1-5 DE_IncrementCounter (8bit)
        increCount = packet_data[5]
        self.output['IncrementCounter'] = increCount

        # 1-6 DE_CommonAppDataLength (8bit)
        comAppDataLenCommon = packet_data[6]
        self.output['AppDataLength'] = comAppDataLenCommon

        # 1-7 DE_OptionFlag (8bit)
        optFlg = packet_data[7]
        self.output['OptionFlag'] = optFlg
        self.output['PositionOption'] = str(optFlg & 0x01)
        self.output['GNSSOption'] = str((optFlg & 0x02) >> 1)
        self.output['PositionAcquisitionOption'] = str((optFlg & 0x04) >> 2)
        self.output['VehicleStatusOption'] = str((optFlg & 0x08) >> 3)
        self.output['IntersectionOption'] = str((optFlg & 0x10) >> 4)
        self.output['ExtendedInformationOption'] = str((optFlg & 0x20) >> 5)
        self.output['ExtendedOption'] = str((optFlg & 0x40) >> 6)
        self.output['ApplicationOption'] = str((optFlg & 0x80) >> 7)

        self.ptr += self.COMMON_SIZE

    def __dump_time(self, packet_data):
        if len(packet_data) < self.TIME_SIZE:
            raise self.ITSConverterError('Data length is too short. '
                                         '[TIME]Length : {}, Expected : {}'.format(len(packet_data),
                                                                                     self.TIME_SIZE))
        # 2-1 DE_LeapSecondsCorrectionAvailability (1bit)
        leapSecondsCorrection = str((packet_data[0] & 0x80) >> 7)
        # 2-2 DE_Hour (7bit)
        tHour = packet_data[0] & 0x7f
        # 2-3 DE_Minute (8bit)
        tMin = packet_data[1]
        # 2-4 DE_Second (16bit)
        tSec = packet_data[2] * 256 + packet_data[3]

        self.output['LeapSecondsCorrection'] = leapSecondsCorrection
        self.output['Hour'] = tHour
        self.output['Minute'] = tMin
        self.output['Second'] = tSec / 1000

        self.ptr += self.TIME_SIZE

    def __dump_position(self, packet_data):
        if len(packet_data) < self.POSITION_SIZE:
            raise self.ITSConverterError('Data length is too short. '
                                         '[POSITION]Length : {}, Expected : {}'.format(len(packet_data),
                                                                                     self.POSITION_SIZE))

        # 3-1 DE_Latitude (32bit)
        lat = struct.unpack('>l', packet_data[0:4])[0] / 10000000
        # 3-2 DE_Longitude (32bit)
        long = struct.unpack('>l', packet_data[4:8])[0] / 10000000
        # 3-3 DE_Elevation (16bit)
        if packet_data[8] & 0xf0 == 0xf0:
            elevation = struct.unpack('>h', packet_data[8:10])[0]
        else:
            elevation = struct.unpack('>H', packet_data[8:10])[0]
        elevation = elevation / 10

        # 3-4 DE_PositionConfidence (4bit)
        position_confidence = str(packet_data[10] >> 4)
        # 3-5 DE_ElevationConfidence (4bit)
        elevation_confidence = str(packet_data[10] & 0x0f)

        self.output['Latitude'] = lat
        self.output['Longitude'] = long
        self.output['Elevation'] = elevation
        self.output['PositionConfidence'] = position_confidence
        self.output['ElevationConfidence'] = elevation_confidence

        self.ptr += self.POSITION_SIZE

    def __dump_vehicle_status(self, packet_data):
        if len(packet_data) < self.VEHICLE_STATUS_SIZE:
            raise self.ITSConverterError('Data length is too short. '
                                         '[VEHICLE STATUS]Length : {}, Expected : {}'.format(len(packet_data),
                                                                                     self.VEHICLE_STATUS_SIZE))

        # 4-1 DE_Speed (16bit)
        speed = struct.unpack('>H', packet_data[0:2])[0]
        # 4-2 DE_Heading (16bit)
        head = struct.unpack('>H', packet_data[2:4])[0]
        # 4-3 DE_Acceleration (16bit)
        accelerator = struct.unpack('>h', packet_data[4:6])[0]
        # 4-4 DE_SpeedConfidence (3bit)
        speed_confidence = str(packet_data[6] >> 5)
        # 4-5 DE_HeadingConfidence (3bit)
        heading_confidence = str((packet_data[6] & 0x1c ) >> 2)
        # 4-6 DE_AccelerationConfidence (3bit)
        acceleration_confidence = str(((packet_data[6] & 0x03 ) << 1) + ((packet_data[7] & 0x80) >> 7))
        # 4-7 DE_TransmissionState (3bit)
        transmission_state = str((packet_data[7] & 0x70) >> 4)
        # 4-8 DE_SteeringWheel Angle (12bit)
        steering_wheel_angle = ((packet_data[7] & 0x000f) << 8) + packet_data[8]
        steering_wheel_angle = self.complement(steering_wheel_angle, 12) * 1.5

        self.output['Speed'] = speed / 100
        self.output['Heading'] = head * 125 / 10000
        self.output['Acceleration'] = accelerator / 100
        self.output['SpeedConfidence'] = speed_confidence
        self.output['HeadingConfidence'] = heading_confidence
        self.output['AccelerationConfidence'] = acceleration_confidence
        self.output['TransmissionState'] = transmission_state
        self.output['SteeringWheelAngle'] = steering_wheel_angle

        self.ptr += self.VEHICLE_STATUS_SIZE

    def __dump_vehicle_attribute(self, packet_data):
        if len(packet_data) < self.VEHICLE_ATTRIBUTE_SIZE:
            raise self.ITSConverterError('Data length is too short. '
                                         '[VEHICLE ATTRIBUTE]Length : {}, Expected : {}'.format(len(packet_data),
                                                                                     self.VEHICLE_ATTRIBUTE_SIZE))

        # 5-1 DE_VehicleSizeClassification (4bit)
        self.output['SizeClass'] = str((packet_data[0] & 0xf0) >> 4)
        # 5-2 DE_VehicleRoleClassification (4bit)
        self.output['RoleClass'] = str(packet_data[0] & 0x0f)

        # 5-3 DE_VehicleWidth (10bit)
        self.output['VehicleWidth'] = (((packet_data[1] << 2) + ((packet_data[2] & 0xc0) >> 6))) / 100
        # 5-4 DE_VehicleLength (10bit)
        self.output['VehicleLength'] =  (struct.unpack('>H', packet_data[2:4])[0] & 0x3fff) / 100

        self.ptr += self.VEHICLE_ATTRIBUTE_SIZE

    def __dump_position_option(self, packet_data):
        if self.__is_option_available('PositionOption'):
            if len(packet_data) < self.POSITION_OPTION_SIZE:
                raise self.ITSConverterError('Data length is too short. '
                                             '[POSITION OPTION]Length : {}, Expected : {}'.format(len(packet_data),
                                                                                                  self.POSITION_OPTION_SIZE))
            # 6-1 DE_PositionDelay (5bit)
            self.output['PositionOption.Delay'] = ((packet_data[0] & 0xf8) >> 3) * 100
            # 6-1 DE_RevisionCounter (5bit)
            position_revision_counter = ((packet_data[0] & 0x07) << 2) + ((packet_data[1] & 0xc0) >> 6)
            self.output['PositionOption.DelayRevisionCounter'] = position_revision_counter * 100

            # 6-3 DE_RoadFacilities (3bit)
            self.output['PositionOption.RoadFacilities'] = str((packet_data[1] & 0x38) >> 3)
            # 6-4 DE_RoadClassification (3bit)
            self.output['PositionOption.RoadClassification'] = str(packet_data[1] & 0x07)

            self.ptr += self.POSITION_OPTION_SIZE

    def __dump_gnss_option(self, packet_data):
        if self.__is_option_available('GNSSOption'):
            if len(packet_data) < self.GNSS_STAT_OPTION_SIZE:
                raise self.ITSConverterError('Data length is too short. '
                                             '[GNSS OPTION]Length : {}, Expected : {}'.format(len(packet_data),
                                                                                                  self.GNSS_STAT_OPTION_SIZE))
            # 7-1 DE_SemiMajorAxisOfPositionalErrorEllipse (8bit)
            self.output['GNSSOption.SemiMajorAxisOfPositionalErrorEllipse'] = packet_data[0] * 0.5

            # 7-2 DE_SemiMinorAxisOfPositionalErrorEllipse (8bit)
            self.output['GNSSOption.SemiMinorAxisOfPositionalErrorEllipse'] = packet_data[1] * 0.5

            # 7-3 DE_SemiMajorAxisOrientationOfPositionalErrorEllipse (16bit)
            semi_major_axis_orientation_of_positional_error_ellipse = \
                round(struct.unpack('>H', packet_data[2:4])[0] * 0.0125, 4)
            self.output['GNSSOption.SemiMajorAxisOrientationOfPositionalErrorEllipse'] = \
                semi_major_axis_orientation_of_positional_error_ellipse

            self.ptr += self.GNSS_STAT_OPTION_SIZE

    def __dump_position_acquisition_option(self, packet_data):
        if self.__is_option_available('PositionAcquisitionOption'):
            if len(packet_data) < self.POSITION_ACQUISITION_OPTION_SIZE:
                raise self.ITSConverterError('Data length is too short. '
                                             '[POSSITION ACQUISITION OPTION]Length : {}, Expected : {}'.format(len(packet_data),
                                                                                                  self.POSITION_ACQUISITION_OPTION_SIZE))
            # 8-1 DE_GNSSPositioningMode (2bit)
            self.output['PositionAcquisitionOption.GNSSPositioningMode'] = str((packet_data[0] & 0xc0) >> 6)
            # 8-2 DE_GNSSPDOP (6bit)
            self.output['PositionAcquisitionOption.GNSSPDOP'] = round((packet_data[0] & 0x3f) * 0.2,1)

            # 8-3 DE_NumberOfGNSSSatellitesInUse (4bit)
            self.output['PositionAcquisitionOption.NumberOfGNSSSatellitesInUse'] = ((packet_data[1] & 0xf0) >> 4)
            # 8-4 DE_GNSSMultipathDetection (2bit)
            self.output['PositionAcquisitionOption.GNSSMultipathDetection'] = str((packet_data[1] & 0x0c) >> 2)
            # 8-5 DE_DeadReckoningAvailability (1bit)
            self.output['PositionAcquisitionOption.DeadReckoningAvailability'] = str((packet_data[1] & 0x02) >> 1)
            # 8-6 DE_MapMatchingAvailability (1bit)
            self.output['PositionAcquisitionOption.MapMatchingAvailability'] = str(packet_data[1] & 0x01)

            self.ptr += self.POSITION_ACQUISITION_OPTION_SIZE

    def __dump_vehicle_status_option(self, packet_data):
        if self.__is_option_available('VehicleStatusOption'):
            if len(packet_data) < self.VEHICLE_STATUS_OPTION_SIZE:
                raise self.ITSConverterError('Data length is too short. '
                                             '[VEHICLE STATUS OPTION]Length : {}, Expected : {}'.format(len(packet_data),
                                                                                                  self.VEHICLE_STATUS_OPTION_SIZE))
            # 9-1 DE_YawRate (16bit)
            self.output['VehicleStatusOption.YawRate'] = struct.unpack('>h', packet_data[:2])[0] / 100

            # 9-2 DE_BrakeAppliedStatus (6bit)
            break_status = packet_data[2] >> 2
            self.output['VehicleStatusOption.BreakAppliedStatus.LeftFront'] = str(break_status & 0x01)
            self.output['VehicleStatusOption.BreakAppliedStatus.LeftRear'] = str((break_status & 0x02) >> 1)
            self.output['VehicleStatusOption.BreakAppliedStatus.RightFront'] = str((break_status & 0x04) >> 2)
            self.output['VehicleStatusOption.BreakAppliedStatus.RightRear'] = str((break_status & 0x08) >> 3)
            self.output['VehicleStatusOption.BreakAppliedStatus.Available'] = str((break_status & 0x10) >> 4)
            self.output['VehicleStatusOption.BreakAppliedStatus.Independent'] = str((break_status & 0x20) >> 5)
            # 9-3 DE_AuxiliaryBrakeAppliedStatus (2bit)
            self.output['VehicleStatusOption.AuxiliaryBrakeAppliedStatus'] = str(packet_data[2] & 0x03)

            # 9-4 DE_ThrottlePosition (8bit)
            self.output['VehicleStatusOption.ThrottlePosition'] = packet_data[3] * 0.5

            # 9-5 DE_ExteriorLights(8bit)
            exterior_lights = packet_data[4]
            self.output['VehicleStatusOption.ExteriorLights.LowBeam'] = str(exterior_lights & 0x01)
            self.output['VehicleStatusOption.ExteriorLights.HighBeam'] = str((exterior_lights & 0x02) >> 1)
            self.output['VehicleStatusOption.ExteriorLights.LeftTurn'] = str((exterior_lights & 0x04) >> 2)
            self.output['VehicleStatusOption.ExteriorLights.RightTurn'] = str((exterior_lights & 0x08) >> 3)
            self.output['VehicleStatusOption.ExteriorLights.HeadLightAvailable'] = str((exterior_lights & 0x10) >> 4)
            self.output['VehicleStatusOption.ExteriorLights.TurnLightAvailable'] = str((exterior_lights & 0x20) >> 5)
            self.output['VehicleStatusOption.ExteriorLights.HazardSignalAvailable'] = str((exterior_lights & 0x40) >> 6)

            # 9-6 DE_AdaptiveCruiseControlStatus(2bit)
            self.output['VehicleStatusOption.AdaptiveCruiseControlStatus'] = str((packet_data[5] & 0xc0) >> 6)
            # 9-7 DE_CooperativeAdaptiveCruiseControlStatus (2bit)
            self.output['VehicleStatusOption.CooperativeAdaptiveCruiseControlStatus'] = str((packet_data[5] & 0x30) >> 4)
            # 9-8 DE_PreCrashSafetyStatus (2bit)
            self.output['VehicleStatusOption.PreCrashSafetyStatus'] = str((packet_data[5] & 0x0c) >> 2)
            # 9-9 DE_AntilockBrakeStatus (2bit)
            self.output['VehicleStatusOption.AntilockBrakeSystem'] = str(packet_data[5] & 0x03)

            # 9-10 DE_TractionControlStatus (2bit)
            self.output['VehicleStatusOption.TractionControlStatus'] = str((packet_data[6] & 0xc0) >> 6)
            # 9-11 DE_ElectronicStabilityControlStatus (2bit)
            self.output['VehicleStatusOption.ElectronicStabilityControlStatus'] = str((packet_data[6] & 0x30) >> 4)
            # 9-12 DE_LaneKeepingAssistStatus (2bit)
            self.output['VehicleStatusOption.LaneKeepingAssistStatus'] = str((packet_data[6] & 0x0c) >> 2)
            # 9-13 DE_LaneDepartureWarningStatus (2bit)
            self.output['VehicleStatusOption.LaneDepartureWarningStatus'] = str(packet_data[6] & 0x03)

            self.ptr += self.VEHICLE_STATUS_OPTION_SIZE

    def __dump_intersection_option(self, packet_data):
        if self.__is_option_available('IntersectionOption'):
            if len(packet_data) < self.INTERSECTION_OPTION_SIZE:
                raise self.ITSConverterError('Data length is too short. '
                                             '[INTERCECTION OPTION]Length : {}, Expected : {}'.format(len(packet_data),
                                                                                                  self.INTERSECTION_OPTION_SIZE))
            # 10-1 DE_IntersectionDistanceInformationAvailability(3bit)
            self.output['IntersectionOption.DistanceInformationAvailability'] = \
                str(packet_data[0] >> 5)

            # 10-2 DE_IntersectionDistance(10bit)
            self.output['IntersectionOption.Distance'] = \
                ((packet_data[0] & 0x1f) << 5) + ((packet_data[1] & 0xf8) >> 3)

            # 10-3 DE_IntersectionPositionInformationAvailability(3bit)
            self.output['IntersectionOption.PositionInformationAvailability'] = \
                str(packet_data[1] & 0x07)

            # 10-4 DE_IntersectionLatitude
            lat = struct.unpack('>l', packet_data[2:6])[0] / 10000000
            self.output['IntersectionOption.Latitude'] = lat

            # 10-5 DE_IntersectionLongitude
            long = struct.unpack('>l', packet_data[6:10])[0] / 10000000
            self.output['IntersectionOption.Longitude'] = long

            self.ptr += self.INTERSECTION_OPTION_SIZE

    def __dump_extended_information_option(self, packet_data):
        if self.__is_option_available('ExtendedInformationOption'):
            if len(packet_data) < self.EXTENDED_INFORMATION_OPTION_SIZE:
                raise self.ITSConverterError('Data length is too short. '
                                             '[EXTENDED OPTION]Length : {}, Expected : {}'.format(len(packet_data),
                                                                                                  self.EXTENDED_INFORMATION_OPTION_SIZE))
            # 11-1~7  DE_ExtendedInformationFor*
            self.output['ExtendedInformationOption.InformationUpper'] = str((packet_data[0] & 0xf0) >> 4)
            self.output['ExtendedInformationOption.InformationLower'] = str(packet_data[0] & 0x0f)

            self.ptr += self.EXTENDED_INFORMATION_OPTION_SIZE

    def __debug_dump(self, packet_data, length=15):
        for i in range(len(packet_data)):
            print('[{}]{:02x}'.format(i, packet_data[i]))

    def convert_preparation(self, pakcet_data):
        self._reset()
        self.is_prepared = True

        return True

    def is_supported(self):
        return True

    def __is_option_available(self, option_tag):
        if option_tag in self.output and self.output[option_tag] == '1':
            return True

        return False
    
    def __dump_free_field_management_info(self, packet_data):
        if len(packet_data) < self.APP_OPTION_SIZE:
                raise self.ITSConverterError('Data length is too short. '
                                             '[INTERCECTION OPTION]Length : {}, Expected : {}'.format(len(packet_data),
                                                                                                  self.INTERSECTION_OPTION_SIZE))

        free_field_mng_info = packet_data[0]
        self.output['IndividualAppHeaderLength'] = str(free_field_mng_info >> 3)
        self.output['NumberOfIndividualAppData'] = str(free_field_mng_info & 0x07)

        self.ptr += self.APP_OPTION_SIZE

    def __dump_indivisual_appData_managemnt_informationSet(self, packet_data, num_indivisualAppdata, surfix):
         
        if len(packet_data) < self.INDIV_APP_DATA_MANAGEMENT_INFO_SIZE * num_indivisualAppdata:
                raise self.ITSConverterError('Data length is too short. '
                                             '[INTERCECTION OPTION]Length : {}, Expected : {}'.format(len(packet_data),
                                                                                                  self.INDIV_APP_DATA_MANAGEMENT_INFO_SIZE * num_indivisualAppdata))
        for i in range(num_indivisualAppdata): 
            offset = i * 3 
            
            indiv_serv_std_id, indiv_app_data_address, indiv_app_data_len = struct.unpack('>BBB', packet_data[offset:offset+3])
            self.output[surfix[i] + '.IndividualServiceStandardID'] = str(indiv_serv_std_id)
            self.output[surfix[i] + '.IndividualAppDataAddress'] = str( indiv_app_data_address)
            self.output[surfix[i] + '.IndividualAppDataLength'] = str( indiv_app_data_len)

        self.ptr += self.INDIV_APP_DATA_MANAGEMENT_INFO_SIZE * num_indivisualAppdata

    def __dump_nexco_demo_experiment_2024(self, packet_data, surfix):

        event_info_byte = packet_data[0]
        self.output[surfix + '.VehicleMalfunction'] = str((event_info_byte & 0x01))
        self.output[surfix + '.AutomaticCollision'] = str((event_info_byte & 0x02) >> 1)
        self.output[surfix + '.ManualCollision'] = str((event_info_byte & 0x04) >> 2)
        self.output[surfix + '.WrongWayDriving'] = str((event_info_byte & 0x08) >> 3)
        # [4] to [7] are reserved
         
        # Decode lane_info (8-bit)
        lane_info_byte = packet_data[1]
        self.output[surfix + '.Lane1'] = str(lane_info_byte & 0x01)
        self.output[surfix + '.Lane2'] = str((lane_info_byte & 0x02) >> 1)
        self.output[surfix + '.Lane3'] = str((lane_info_byte & 0x04) >> 2)
        self.output[surfix + '.Lane4'] = str((lane_info_byte & 0x08) >> 3)
        self.output[surfix + '.Lane5'] = str((lane_info_byte & 0x10) >> 4)
        self.output[surfix + '.Lane6'] = str((lane_info_byte & 0x20) >> 5)
        self.output[surfix + '.AdditionalLane'] = str((lane_info_byte & 0x40) >> 6)
        self.output[surfix + '.Roadside'] = str((lane_info_byte & 0x80) >> 7)

        option_flag = packet_data[2]
        self.output[surfix + '.PointInfoOption'] = str(option_flag & 0x01)
        self.output[surfix + '.TrafficInfoOption'] = str((option_flag & 0x02) >> 1)
        self.output[surfix + '.WiperInfoOption'] = str((option_flag & 0x04) >> 2)
        self.output[surfix + '.InterVehicleDistanceOption'] = str((option_flag & 0x08) >> 3)
        # [4] to [7] are reserved
        
        self.output[surfix + '.WiperInfo']  = packet_data[3]  # Assuming 8-bit for the wiper status
        self.output[surfix + '.InterVehicleDistance']  = packet_data[4]  # Assuming 8-bit for the inter-vehicle distance

    def convert(self, pakcet_data):
        assert self.is_prepared is True
        self.__dump_common(pakcet_data[self.ptr:self.ptr + self.COMMON_SIZE])
        self.__dump_time(pakcet_data[self.ptr:self.ptr + self.TIME_SIZE])
        self.__dump_position(pakcet_data[self.ptr:self.ptr + self.POSITION_SIZE])
        self.__dump_vehicle_status(pakcet_data[self.ptr:self.ptr + self.VEHICLE_STATUS_SIZE])
        self.__dump_vehicle_attribute(pakcet_data[self.ptr:self.ptr + self.VEHICLE_ATTRIBUTE_SIZE])

        self.__dump_position_option(pakcet_data[self.ptr:self.ptr + self.POSITION_OPTION_SIZE])

        self.__dump_gnss_option(pakcet_data[self.ptr:self.ptr + self.GNSS_STAT_OPTION_SIZE])

        self.__dump_position_acquisition_option(
                pakcet_data[self.ptr:self.ptr + self.POSITION_ACQUISITION_OPTION_SIZE])

        self.__dump_vehicle_status_option(
                pakcet_data[self.ptr:self.ptr + self.VEHICLE_STATUS_OPTION_SIZE])

        self.__dump_intersection_option(pakcet_data[self.ptr:self.ptr + self.INTERSECTION_OPTION_SIZE])

        self.__dump_extended_information_option(
            pakcet_data[self.ptr:self.ptr + self.EXTENDED_INFORMATION_OPTION_SIZE]
        )

        if self.__is_option_available('ExtendedOption'):
            pass

        if self.__is_option_available('ApplicationOption'):
            self.__covert_applicationOption(pakcet_data)
            
        self.is_prepared = False

        return self.output
    
    def __covert_applicationOption(self, packet_data):

        indivAppData_namelist = [
            "DemoExperiment2024",
        ]

        self.__dump_free_field_management_info(packet_data[self.ptr:self.ptr + self.APP_OPTION_SIZE])
        num_indivisualAppdata = int(self.output['NumberOfIndividualAppData'])

        if num_indivisualAppdata > 0 and num_indivisualAppdata == len(indivAppData_namelist):
            self.__dump_indivisual_appData_managemnt_informationSet(packet_data[self.ptr:self.ptr + self.INDIV_APP_DATA_MANAGEMENT_INFO_SIZE * num_indivisualAppdata], num_indivisualAppdata, indivAppData_namelist)

            for indivAppData_name in indivAppData_namelist:
                indivAppDataAddress = int(self.output[indivAppData_name + ".IndividualAppDataAddress"])
                indivAppDataLen = int(self.output[indivAppData_name + ".IndividualAppDataLength"])
                
                self.__dump_nexco_demo_experiment_2024(packet_data[self.ptr + indivAppDataAddress:self.ptr + indivAppDataLen], indivAppData_name)
        
class ITSConverter_WithEL(ITSConverter):
    def __dump_el_header(self, packet_data):
        if len(packet_data) < 1:
            return False

        elVer = (packet_data[0] & 0xf0) >> 4
        self.output['ELVersion'] = elVer
        elType = str((packet_data[0] & 0x0C) >> 2)
        self.output['ELType'] = elType
        elSecurityClass = str(packet_data[0] & 0x03)
        self.output['ELSecurity'] = elSecurityClass

        if elType == '1' or elType == '0':
            self.ptr = self.EL_MOBILE_STATION_HEADER_SIZE
        elif elType == '2':
            self.ptr = self.EL_BASE_STATION_HEADER_SIZE
        else:
            return False

        return True

    def convert_preparation(self, pakcet_data):
        self._reset()
        if self.__dump_el_header(pakcet_data[self.ptr: self.ptr + self.EL_HEADER_SIZE]) == False:
            return False

        self.is_prepared = True
        return True

class ITSConverter_Mobile(ITSConverter_WithEL):
    def is_supported(self):
        if super().is_supported() == False:
            return False

        if self.output['ELType'] != self.EL_MOBILE_STATION_HEADER:
            return False

        return True

class ITSConverter_MobileWithBasePartial(ITSConverter_WithEL):
    def convert_base_partial(self, packet_data):
        return self.output

    def convert(self, pakcet_data):
        if self.output['ELType'] != self.EL_MOBILE_STATION_HEADER:
            return self.convert_base_partial(pakcet_data)

        return super().convert(pakcet_data)


class ITSConverter_MobileWithBasePartial_KC(ITSConverter_WithEL):
    def convert_base_partial(self, packet_data):
        return self.output

    def convert(self, pakcet_data):
        if self.output['ELType'] != self.EL_MOBILE_STATION_HEADER_KC:
            return self.convert_base_partial(pakcet_data)

        return super().convert(pakcet_data)


