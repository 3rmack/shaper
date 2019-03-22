import yaml


file_in = "shaper\\out.yml"
file_out = "shaper\\auto_playbook.yml"

current_envs = ["aqa", "ci", "dev", "fqa1", "fqa2", "fqa3", "fqa4", "perf1", "sit", "uat_", "uat2_", "uat3_", "uat4_",
                "ultraserve_dcm", "ultraserve_dev", "ultraserve_fqa", "ultraserve_nft", "ultraserve_prod", "ultraserve_uat"]


def remove_first_line_in_file(file):
    with open(file, 'r') as fin:
        data = fin.read().splitlines(True)
    with open(file, 'w') as fout:
        fout.writelines(data[1:])


def remove_preceding_whitespaces_from_file(file):
    with open(file, 'r') as f:
        lines = f.readlines()

    lines = [line.lstrip() for line in lines]

    with open(file, 'w') as f:
        f.writelines(lines)


def find_common_properties(properties_list_of_dicts):
    eval_string = "&".join(["properties_list_of_dicts[{0}].items()".format(i) for i in range(len(properties_list_of_dicts))])
    common_properties = dict(eval(eval_string))
    common_properties = dict(sorted(common_properties.items()))
    return common_properties


remove_first_line_in_file(file_in)
with open(file_in, 'r') as f:
    file = yaml.safe_load(f)

envs = ""
mappings = ""
stacks = ""
for env_name in current_envs:
    all_env_filenames = []  # list of all env property files
    all_env_properties = []  # list with dicts which contain all properties for specific env
    for filename, properties_dict in file.items():
        filename = filename.split('\\')[-1]
        if filename.startswith(env_name):
            all_env_filenames.append(filename)
            all_env_properties.append(properties_dict)

    if not all_env_properties:
        continue

    common_env_properties = find_common_properties(all_env_properties)

    for filename, properties in zip(all_env_filenames, all_env_properties):

        env_specific = ""
        for k, v in sorted(properties.items() - common_env_properties.items()):
            env_specific += "      {0}: '{1}'\n".format(k, v)

        if env_specific:
            mappings += "    {0}: &{1}\n".format(filename, filename.replace('.', '_'))
            mappings += env_specific
            stacks += "      {0}:\n        <<: *{1}\n        <<: *{2}\n".format(filename, env_name, filename.replace('.', '_'))
        else:
            stacks += "      {0}:\n        <<: *{1}\n".format(filename, env_name)

    env_common_properties = '    {0}: &{0}\n'.format(env_name)
    for k, v in common_env_properties.items():
        env_common_properties += "      {0}: '{1}'\n".format(k, v)
    envs += env_common_properties

with open(file_out, 'w') as f:
    f.write("templates:\n- template.yml\nvariables:\n  envs:\n")
    f.write(envs)
    f.write("\n")
    f.write("  env_specific:\n")
    f.write(mappings)
    f.write("\n")
    f.write("  stacks:\n  - environments:\n")
    f.write(stacks)
