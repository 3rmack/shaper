#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Java Options Manager
    Parse java properties to datastructure
    and create properties from datastructure.

    Support ivan.bogomazov@gmail.com
    Minsk 2018


    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    EXAMPLES:
        TBD
"""

from __future__ import print_function

import argparse
import ConfigParser
import fnmatch
import os
import StringIO
import sys
from collections import OrderedDict

import yaml


class JavaPropertiesParser(object):
    """Java options manager tool"""

    @staticmethod
    def dump_yaml(data, path_to_file):
        """Dump datastructure to yaml

        :param data: configuration dataset
        :type data: dict

        :param path_to_file: filepath
        :type path_to_file: str

        :return: None
        :rtype: None

        """
        try:
            with open(path_to_file, 'w') as outfile:
                yaml.dump(
                    data,
                    outfile,
                    default_flow_style=False,
                    allow_unicode=True,
                )

        except OSError as error:
            sys.stderr.write("Bad file path {0}: {1}".format(
                path_to_file,
                error
            ))

    @staticmethod
    def read_yaml(path_to_file):
        """YAML read
        :param path_to_file: path to yaml file
        :type path_to_file: str

        :return: yaml datastructure
        :rtype: dict
        """
        try:
            with open(path_to_file, 'r') as _fp:
                return yaml.load(
                    _fp,
                    # object_pairs_hook=OrderedDict
                )

        except ValueError as error:
            sys.stderr.write("Bad format {0}: {1}".format(
                path_to_file,
                error
            ))

        except OSError as error:
            sys.stderr.write("Bad file {0}: {1}".format(
                path_to_file,
                error
            ))

    @staticmethod
    def walk_on_path(path, pattern='*.properties'):
        """recursive find files with pattern"""
        matches = []
        for root, _dirnames, files in os.walk(path):
            for filename in fnmatch.filter(files, pattern):
                matches.append(os.path.join(root, filename))

        return matches

    @staticmethod
    def read_properties_file(path_to_file):
        """read ini properties"""
        with open(path_to_file, 'rb') as properties_file:

            config = StringIO.StringIO()
            config.write('[dummy_section]\n')
            config.write(properties_file.read().replace('%', '%%'))
            config.seek(0, os.SEEK_SET)

            conf_parser = ConfigParser.SafeConfigParser()
            conf_parser.readfp(config)

            return dict(conf_parser.items('dummy_section'))

    @staticmethod
    def read_properties(path_to_dir):
        """interface for recursive read properties"""
        data = {}
        files = JavaPropertiesParser.walk_on_path(path_to_dir)

        for filename in files:
            data.update({
                filename: JavaPropertiesParser.read_properties_file(filename)
            })

        return data

    @staticmethod
    def write_properties_file(path_to_file, datastructure):
        """write kv ini like style"""
        with open(path_to_file, "wb") as properties_file:
            for key, value in datastructure.iteritems():
                properties_file.write(
                    "{}={}\n".format(key, value)
                )

    @staticmethod
    def create_folders(path_to_folder):
        """recursive creating folders"""
        try:
            os.makedirs(path_to_folder)
        except OSError as exc:
            if os.path.isdir(path_to_folder):
                pass
            else:
                raise EOFError

    @staticmethod
    def write_properties(datastructure, out_path):
        """interface for recursive write properties"""
        for filename, properties in datastructure.iteritems():
            directories = os.path.join(
                out_path,
                os.path.dirname(filename)
            )
            property_file = os.path.basename(filename)
            JavaPropertiesParser.create_folders(directories)
            JavaPropertiesParser.write_properties_file(
                os.path.join(
                    directories,
                    property_file
                ),
                properties
            )

    @staticmethod
    def forward_path_parser(_input):
        """parsing plain dict to nested"""

        def get_or_create_by_key(key, current_tree):
            """update dict by key"""
            if key not in current_tree:
                last = keys.pop()
                dict_update = {last: value}

                for _key in reversed(keys):
                    dict_update = {_key: dict_update}

                current_tree.update(dict_update)
            else:
                keys.pop(0)
                get_or_create_by_key(keys[0], current_tree[key])

        output = {}
        for key, value in OrderedDict(_input).items():
            keys = key.split('/')

            get_or_create_by_key(keys[0], output)

        return output

    @staticmethod
    def backward_path_parser(_input):
        """make nested structure plain"""

        def path_builder(current_tree, key=''):
            """make plain"""
            for _key, _value in current_tree.items():
                _key = key + '/' + _key if key else _key
                if '.' in _key:
                    output.update({_key: _value})
                else:
                    path_builder(_value, _key)

        output = {}
        path_builder(_input)

        return output


def parse_arguments():
    """Argument parsing

    :return: args namespace
    :rtype: namespace
    """
    parser = argparse.ArgumentParser(
        description='Tool to manage java properties'
    )

    subparsers = parser.add_subparsers(
        dest="parser"
    )

    read = subparsers.add_parser(
        "read",
        help="Recursive read properties from files"
    )

    write = subparsers.add_parser(
        "write",
        help="Write properties files from datastructure"
    )

    read.add_argument(
        'src_path',
        type=str,
        help='Path to properties directory',
    )

    read.add_argument(
        '-o',
        '--out',
        dest='out',
        default='out.yml',
        help='Output file. Default out.yaml',
    )

    write.add_argument(
        "src_structure",
        type=str,
        help="Path to yaml with datastructure."
    )

    write.add_argument(
        '-o',
        '--out',
        dest='out',
        default='./out/',
        help='Path to output directory. Default ./out/',
    )

    return parser.parse_args()


def main():
    """main"""
    arguments = parse_arguments()
    jom = JavaPropertiesParser()

    if arguments.parser == "read":
        tree = jom.forward_path_parser(jom.read_properties(arguments.src_path))
        jom.dump_yaml(tree, arguments.out)

    elif arguments.parser == "write":
        yaml_data = jom.read_yaml(arguments.src_structure)
        datastructure = jom.backward_path_parser(yaml_data)
        jom.write_properties(datastructure, arguments.out)

    else:
        raise NotImplementedError


if __name__ == "__main__":
    main()