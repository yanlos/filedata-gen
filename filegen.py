import yaml
import os
import numpy as np
import re
import time
import string
import random
import argparse


class InvalidFormatException(Exception):
    pass


class HaltAndCatchFire:

    def __init__(self, dic):
        self._dic = dic
        return

    def show_yaml(self):
        """
        Shows the YAML file contents (optional method)
        """
        with open(input_file, 'r') as stream:
            try:
                print(yaml.safe_load(stream))
            except yaml.YAMLError as exc:
                print(exc)

    def get_params(self):
        """
        Grabs 'generate_file' and 'generate_database' from YAML file, using lists b/c dictionaries overwrites keys
        ANY OTHER PARAMETERS IN THE FUTURE HAVE TO BE UPDATED HERE
        """
        file_list = []
        settings = []
        file_count = 0

        for gen_type, get_data in self._dic.items():

            if "settings" in gen_type:

                ddSameSize = get_data["dedup_same_size"]
                if ddSameSize:
                    settings.append("ddSameSize")

                database_type = get_data["create_database"]
                if database_type is False:
                    pass
                elif database_type.lower() == "msexchange":
                    print("Generating Database For: " + database_type)
                    settings.append("msexchange")

            # We are pulling the parameters from the dict / YAML and adding them to a single list to
            # avoid log(n^3) time when iterating through
            if "generate_file" in gen_type:

                d = get_data["directory"]
                s = get_data["size"]
                n = get_data["number_files"]
                c = get_data["compression_rate"]
                t = get_data["type_data"]
                f = get_data["folder_depth"]

                # if any parameters in the YAML are missing
                if (d and s and n and c and t and f) is None:
                    raise ValueError("Missing Parameter(s)")

                file_params = [d, s, n, c, t, f]
                file_list.extend(file_params)
                file_count += 1

        return file_list, file_count, settings

    def generate_file(self, file_list, file_count, settings):
        """
        This is where the file parameters are split up, folders are created, randomly assigned a size, and generated
        :param file_list: the list of files (parameters) retrieved from the YAML
        :param file_count: how many times in the YAML "generate_file" was found
        :param settings: settings specified for the file / database generation
        """
        # since the parameters have to be symmetrical, we can assume that the number of total args (file_length)
        # divided by the amount of files generated (file_count), gives us the number of parameters given in each file
        file_length = len(file_list)
        number_of_parameters_file_gen = int(file_length / file_count)
        start = 0

        # uses the same seed for all files generated in a single YAML file to compare deduplication rates
        if 'ddSameSize' in settings:
            is_same_size = np.random.randint(0, 10000)
        else:
            is_same_size = False

        # d: directory, s: size, n: number_files, c:compression_rate, t: type_data, f: folder_depth
        while file_count is not 0:
            d = file_list[start]
            s = file_list[start+1]
            n = file_list[start+2]
            c = file_list[start+3]
            t = file_list[start+4]
            f = file_list[start+5]

            # Creates the directory with the specified amount of layers
            folder_depth = self.create_folder_layers(f)

            try:
                os.makedirs(d + folder_depth)
            except FileExistsError:
                d = d + ''.join(random.sample(string.ascii_letters, 4))
                print("File already exists. Changing file name to: " + d)
                os.makedirs(d + folder_depth)

            # Gets the total amount of bytes, creates a list of random %'s to split up files, and multiplies them
            bytes_total = self.get_bytes(s)
            random_sizes_list = self.randomize_size(n, is_same_size)
            final_sizes_list = []
            for item in random_sizes_list:
                item = bytes_total * item
                final_sizes_list.append(int(item))

            print("List of file's sizes in bytes:")
            print(final_sizes_list)

            # This works by writing the deduplicatable (empty space first) and then finding the remaining amount of
            # space by finding the spot where it stopped writing (rest_of_data) then fills in with the data type
            for file_size in final_sizes_list:

                database_type = ""
                if 'msexchange' in settings:
                    database_type = ".edb"

                directory_create = d + folder_depth + str(file_size)
                # If the files already exists, then we change the name (add 8 random chars) so they don't get rewritten
                if os.path.exists(directory_create + database_type):
                    f = open(directory_create + ''.join(random.sample(string.ascii_letters, 8)) + database_type, 'wb')
                else:
                    f = open(directory_create + database_type, 'wb')

                # Push data in a file, this goes to the byte you want and fills it up with white space and then
                # puts a small message at the end, very fast and compressible if we can use empty space
                if c is 100:
                    f.seek(int(file_size))
                    f.write(("end of file").encode())
                else:
                    compression_start = file_size * (c / 100)
                    f.seek(int(compression_start))
                    rest_of_data = file_size - compression_start
                    if t.lower() == "ascii":
                        rand = bytes.maketrans(bytearray(range(256)), bytearray([ord(b'a') + b % 26 for b in range(256)]))
                        f.write(os.urandom(int(rest_of_data)).translate(rand))
                    elif t.lower() == "bytes":
                        f.write(os.urandom(int(rest_of_data)))
                    else:
                        raise ValueError("Data Type Not Supported")

                f.close()

            file_count -= 1
            start += number_of_parameters_file_gen

    def get_bytes(self, size):
        """
        This splits the size parameters into an int and type of gig and then calculates total amount in bytes
        :param size: the total size of the file to calculate in bytes
        :return: the size in bytes ex: 1 GB turns into 1073741824 bytes
        """
        split = re.match(r'([0-9) ]+)([a-z]+)', size, re.IGNORECASE)
        if split:
            # ex: splits "10MB" or "10 MB" into ->  "10""MB"
            num = int(split.group(1))
            gigtype = split.group(2)
        elif "." in size:
            raise InvalidFormatException("Decimals Not Supported Please Use '512 MB' not '.5 GB' Use B for exact bytes")
        else:
            raise InvalidFormatException("Bad Formatting, Please Use Example Format '10 MB' or '10MB'")

        gigtype = gigtype.upper()
        if gigtype == 'TB' and 'T':
            bytes_total = 1024 * 1024 * 1024 * 1024 * num
        elif gigtype == 'GB' and 'G':
            bytes_total = 1024 * 1024 * 1024 * num
        elif gigtype == 'MB' and "M":
            bytes_total = 1024 * 1024 * num
        elif gigtype == 'KB' and "K":
            bytes_total = 1024 * num
        elif gigtype == 'B':
            bytes_total = num
        else:
            raise InvalidFormatException("Bad Formatting, Please Make Sure You Are Using: B,K,M,G,T,KB,MB,GB,or TB")
        return bytes_total

    def create_folder_layers(self, f):
        """
        Creates the folders in the directory based on the folder depth before placing the data inside
        :param f: how many folders the user wants in the directory
        :return: a string to add to the directory for the OS to write
        """
        folder_string = ""
        for i in range(f):
            folder_string += "/" + str(i)
        return folder_string + "/"

    def randomize_size(self, number_of_files, is_same_size):
        """
        Returns a list of randomly generated floats to use to later multiply and randomize the file sizes
        :param number_of_files: how many elements to put into the list
        :param is_same_size: if the multiple files generated are meant to be the same size for deduplication
        :return: a list (size = to number_of_files) of randomly generated elements (float percentages that add up to 1)
        """

        if is_same_size is not False:
            np.random.seed(is_same_size)
        sizes_list = np.random.random(number_of_files)
        sizes_list /= sizes_list.sum()
        return sizes_list


start_time = time.time()

try:
    input_file = "filegen.yaml"
    with open(input_file, 'r') as dic:
        dic = yaml.safe_load(dic)
except:
    parser = argparse.ArgumentParser(description="Run File Generator Script + YAML File")
    parser.add_argument('--conf', action="store", type=str, required=True, help="YAML configuration file")
    arg = parser.parse_args()
    input_file = os.path.realpath(arg.conf)
    with open(input_file, 'r') as dic:
        dic = yaml.safe_load(dic)


cease = HaltAndCatchFire(dic)
# cease.show_yaml()
file_list, file_count, settings = cease.get_params()

if file_count > 0:
    cease.generate_file(file_list, file_count, settings)

print("--- %s seconds ---" % (time.time() - start_time))
