import pcapng
from pcapng.blocks import EnhancedPacket


class PcapNgHelper(object):
    class PcapNgHelperError(Exception):
        def __init__(self, ex, message):
            self.__ex = ex
            self.__message = message

        def __str__(self):
            return self.__ex.str()

        def error_message(self):
            return self.__message


    OFFSET_PROTOCOL = 12
    OFFSET_PAYLOAD = 14

    def __init__(self):
        pass

    def set_config(self, offset=0, protocol_filters=[]):
        self.offset = offset
        self.protocol_filters = protocol_filters

    def is_supported_protocol(self, packet_data):
        if len(self.protocol_filters) < 1:
            return True

        self.OFFSET_PROTOCOL
        protocol_id = '0x{:02x}{:02x}'.format(packet_data[self.OFFSET_PROTOCOL],
                                              packet_data[self.OFFSET_PROTOCOL + 1])

        for protocol_filter in self.protocol_filters:
            if protocol_filter == protocol_id:
                return True

        return False

    def read_file(self, fp, start=0, count=None):
        try:
            scanner = pcapng.FileScanner(fp)
            filtered_data = []
            for block in scanner:
                if isinstance(block, EnhancedPacket):
                    # if self.is_supported_protocol(block.packet_data):
                    packet_data = block.packet_data
                    total_header_length = self.extract_header_length(packet_data)
                    if self.meets_criteria(packet_data, total_header_length):
                    
                        # print(' => {:02x}'.format(block.packet_data[total_header_length + self.offset:][0]))
                        filtered_data.append(packet_data[total_header_length + self.offset:])

                        # Debugging
                        if count is not None:
                           if len(filtered_data) > count:
                                break
        except ValueError as ve:
            raise self.PcapNgHelperError(ve, 'File parse error. The file is maybe not in its-connect data format.')
        except Exception as ex:
            raise self.PcapNgHelperError(ex, 'Unknown error.')

        return filtered_data
    
    def meets_criteria(self, packet_data, total_header_length):
        src_ip = packet_data[26:30]  
        dest_ip = packet_data[30:34] 

        payload_length = len(packet_data) - total_header_length
        
        return src_ip == self.source_ip and dest_ip == self.dest_ip and payload_length == self.data_length
    
    def extract_header_length(self, packet_data):
        eth_header_length = 14
        udp_header_length = 8
        ip_header_length = (packet_data[14] & 0x0F) * 4

        total_header_length = eth_header_length + udp_header_length +ip_header_length

        return total_header_length


class TricRecordedData(PcapNgHelper):
    def __init__(self):
        self.set_config(8, ['0xf101'])
        self.source_ip = bytes([192, 168, 0, 47]) # 送信先IP
        self.dest_ip = bytes([192, 168, 0, 1]) # 宛先IP
        self.data_length = 68 # データ長




