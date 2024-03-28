#!/usr/bin/env python3

import argparse
import os
from pathlib import PurePath
import pandas as pd
from tqdm import tqdm
import csv

import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
itsconverter_path = os.path.join(current_dir, 'itsconverter-0.0.1')

# Pythonのモジュール検索パスに追加
if itsconverter_path not in sys.path:
    sys.path.append(itsconverter_path)

from itsconnectconverter import pcapng_helper as ph
from itsconnectconverter import converter as cv

MAX_DICT = 500000

class ConvertLog(object):
    def __init__(self):
        self.__success = 0
        self.__error = 0

    def inc_success(self):
        self.__success += 1

    def inc_error(self):
        self.__error += 1

    def print_log(self):
        print('Success : {}'.format(self.__success))
        print('Error   : {}'.format(self.__error))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="specify input file name here")
    parser.add_argument("-output", help="specify output file name here")

    args = parser.parse_args()

    input = args.input
    print("Input file : '{}'".format(input))

    if os.path.exists(input) is False:
        print("The file '{}' doesn't exist.".format(input))
        exit(0)

    if args.output is None:
        suffix = PurePath(input).suffix
        destination = input.replace(suffix, '.csv')
    else:
        destination = args.output

    print("Output file : '{}'".format(destination))

    log = ConvertLog()

    with open(input, 'rb') as fp:
        print('Preparing...')
        reader = ph.TricRecordedData()
        try :
            filtered = reader.read_file(fp)
        except ph.PcapNgHelper.PcapNgHelperError as pe:
            print(pe.error_message())
            exit(0)

        # converter = cv.ITSConverter_MobileWithBasePartial()
        converter = cv.ITSConverter()

        json_data = []
        file_idx = 0

        print(len(filtered))

        for i, data in enumerate(tqdm(filtered[:])):
            try:
                converter.convert_preparation(data)
                if converter.is_supported() is True:
                    output = converter.convert(data)
                    json_data.append(
                        output
                    )
                    log.inc_success()
                    if len(json_data) > MAX_DICT:
                        suffix = PurePath(destination).suffix
                        partial_destination = destination.replace(suffix, '_{}{}'.format(file_idx, suffix))
                        print("Writing to '{}'...".format(partial_destination))
                        df = pd.DataFrame(json_data)
                        df.to_csv(partial_destination, quoting=csv.QUOTE_NONNUMERIC)
                        json_data = []
                        file_idx += 1
                        del df
                        
            except cv.ITSConverter.ITSConverterError as ex:
                print(ex.error_message())
                log.inc_error()
            except Exception as ex:
                print(ex)
                log.inc_error()
            filtered[i] = None
            del data

        if len(json_data) > 0:
            if file_idx > 0:
                suffix = PurePath(destination).suffix
                destination = destination.replace(suffix, '_{}{}'.format(file_idx, suffix))
                
            print("Writing to '{}'...".format(destination))
            df = pd.DataFrame(json_data)
            df.to_csv(destination, quoting=csv.QUOTE_NONNUMERIC)
            log.print_log()
        else:
            print('No appropriate data found.')
