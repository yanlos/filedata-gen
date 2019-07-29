import yaml
import os
import numpy as np
import re
import time
import string
import random

#TODO: if file exists, create another version. files that are not read only


class InvalidParameterException(Exception):
    pass


class InvalidSizeException(Exception):
    pass


class HaltAndCatchFire:

    def __init__(self):
        return

    # Shows the YAML file contents (optional method)
    def show_yaml(self):
        with open(input_file, 'r') as stream:
            try:
                print(yaml.safe_load(stream))
            except yaml.YAMLError as exc:
                print(exc)

    # Grabs generate_file and generate_database from YAML file, using lists b/c dictionaries overwrites keys
    # ANY OTHER PARAMETERS IN THE FUTURE HAVE TO BE UPDATED HERE
    def get_params(self):

        file_list = []
        data_list = []
        file_count = 0
        database_count = 0

        with open(input_file, 'r') as dic:
            dic = yaml.safe_load(dic)

        for gen_type, get_data in dic.items():
            # TODO: implement parameter retrieval of database YAML file
            if "generate_database" in gen_type:
                data_list.append(get_data)
                database_count += 1
                # print("database files count")
                # print(database_count)

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
                    raise InvalidParameterException("Missing Parameter(s)")

                file_params = [d, s, n, c, t, f]
                file_list.extend(file_params)
                file_count += 1

        return file_list, file_count, data_list, database_count

    # TODO look into itertools to iterate multiple lists at once
    # TODO create method to create lists as needed call them x1, x2, x3 etc
    def generate_file(self, file_list, file_count):

        # since the parameters have to be symmetrical, we can assume that the number of total args (file_length)
        # divided by the amount of files generated (file_count), gives us the number of parameters given in each file
        file_length = len(file_list)
        number_of_parameters_file_gen = int(file_length / file_count)
        start = 0

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
            os.makedirs(d + folder_depth)

            # Gets the total amount of bytes, creates a list of random %'s to split up files, and multiplies them
            bytes_total = self.get_bytes(s)
            random_sizes_list = self.randomize_size(n)
            final_sizes_list = []
            for item in random_sizes_list:
                item = bytes_total * item
                final_sizes_list.append(int(item))

            print("List of file's sizes in bytes:")
            print(final_sizes_list)

            # This works by writing the deduplicatable (empty space first) and then finding the remaining amount of
            # space by finding the spot where it stopped writing (rest_of_data) then fills in with the data type
            for file_size in final_sizes_list:
                # TODO: randomize read,write, diff permissions

                directory_create = d + folder_depth + " " + str(file_size)

                # If the files already exists, then we change the name (add 8 random chars) so they don't get rewritten
                if os.path.exists(directory_create):
                    f = open(d + folder_depth + " " + str(file_size) + ''.join(random.sample(string.ascii_letters, 8)), 'wb')
                else:
                    f = open(directory_create, 'wb')

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
                        raise InvalidParameterException("Data Type Not Supported")

                    # TODO: I really want to convert into utf-32 so it's 4 bytes instead of 1 and then write 4x as fast
                    # if t.lower() == "utf32":
                    #     # rand = ''.join(random.choices(string.ascii_letters, k=int(rest_of_data / 4)))
                    #     # rand = rand.encode('utf-32')
                    #     # rand = ''.join(random.choices(string.ascii_letters).encode("utf-32") * int(rest_of_data))
                    #     rand = [r.encode("utf-32") for r in ascii_letters]
                    #     f.write((os.urandom(int(rest_of_data))) for r in bytearray(rand).translate(r))
                    #     # f.write(os.urandom(int(rest_of_data)).translate(rand))

                f.close()

            file_count -= 1
            start += number_of_parameters_file_gen

    def get_bytes(self, size):
        split = re.match(r'([0-9) ]+)([a-z]+)', size, re.IGNORECASE)
        if split:
            # ex: splits "10MB" or "10 MB" into ->  "10""MB"
            num = int(split.group(1))
            gigtype = split.group(2)
        elif "." in size:
            raise InvalidSizeException("Decimals Not Supported. Please Use '512 MB' not '.5 GB'. Use B for exact bytes")
        else:
            raise InvalidSizeException("Bad Formatting, Please Use Example Format '10 MB' or '10MB'")

        gigtype = gigtype.upper()
        if gigtype == 'TB' and 'T':
            bytes_total = 1024 * 1024 * 1024 * 1024 * num
        elif gigtype == 'GB' and "G":
            bytes_total = 1024 * 1024 * 1024 * num
        elif gigtype == 'MB' and "M":
            bytes_total = 1024 * 1024 * num
        elif gigtype == 'KB' and "K":
            bytes_total = 1024 * num
        elif gigtype == 'B':
            bytes_total = num
        else:
            raise InvalidSizeException("Bad Formatting, Please Make Sure You Are Using: B,K,M,G,T,KB,MB,GB,or TB")
        return bytes_total

    def create_folder_layers(self, f):
        folder_string = ""
        for i in range(f):
            folder_string += "/" + str(i)
        return folder_string + "/"

    # Returns a list of randomly generated floats to use as the size
    # TODO: optionally keep random file sizes the same using the same seed -> if(param): np.random.seed(1234)
    def randomize_size(self, number_of_files):
        sizes_list = np.random.random(number_of_files)
        sizes_list /= sizes_list.sum()
        return sizes_list

    # this is returning a dictionary
    def generate_database(self, data_dic, database_count):
        # print(data_dic)
        return


start_time = time.time()
# test.show_yaml()
input_file = "gen.yaml"

test = HaltAndCatchFire()
file_list, file_count, data_list, database_count = test.get_params()
test.generate_file(file_list, file_count)
test.generate_database(data_list, database_count)

print("--- %s seconds ---" % (time.time() - start_time))
