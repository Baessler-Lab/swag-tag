import json
import typing
from collections import defaultdict, ChainMap
from collections.abc import Sequence, Mapping
from itertools import chain
from pathlib import Path

import yaml


def flatten_sequence(sequence: yaml.Node) -> typing.Iterator[str]:
    """Flatten a nested sequence to a list of strings
        A nested structure is always a SequenceNode
    """
    if isinstance(sequence, yaml.ScalarNode):
        yield sequence.value
        return
    if not isinstance(sequence, yaml.SequenceNode | yaml.MappingNode):
        raise TypeError(f"'!flatten' can only flatten sequence nodes, not {sequence}")
    for el in sequence.value:
        if isinstance(el, yaml.SequenceNode):
            yield from flatten_sequence(el)
        elif isinstance(el, yaml.ScalarNode):
            yield el.value
        elif isinstance(el, yaml.MappingNode):
            yield from flatten_sequence(el.value[0])
        else:
            raise TypeError(f"'!flatten' can only take scalar nodes, not {el}")


def construct_flat_list(loader: yaml.Loader, node: yaml.Node) -> typing.List[str]:
    """Make a flat list, should be used with '!flatten'

    Args:
        loader: Unused, but necessary to pass to `yaml.add_constructor`
        node: The passed node to flatten
    """
    return list(flatten_sequence(node))


yaml.add_constructor("!flatten", construct_flat_list)


def transform_flat_to_nested(template: Path | str | typing.Mapping[str, typing.Any]):
    if isinstance(template, Path) or isinstance(template, str):
        template_dir_fpath = Path(__file__).with_name("templates")
        template_fpath = template_dir_fpath / template
        with template_fpath.open("r") as f:
            template = yaml.load(f, yaml.Loader)

    structures = template['structures']
    pretty = json.dumps(structures, indent=4)
    print(pretty)
    nested_template = defaultdict(lambda: 'None')

    parse_template_recursive(structures, name=template, parent_id='1')
    # for headline, structure_item in structures.items():
    #     # lookup global attr_opts
    #     attr_opts = attr_options[headline]
    #
    #     if isinstance(structure_item, list):
    #         try:
    #             items =
    #         sub_structure = dict()
    #         for item in structure_item:
    #             for attr_opts in
    #             sub_structure[item] =
    #
    #
    #
    #     nested_template[headline] = sub_structure


def parse_template_recursive(
        template: typing.Mapping[str, typing.Any],
        name: str = None,
        parent_id: str = None,
) -> typing.Dict[str, typing.Any]:
    # outer structure should be headlines
    if 'items' in template:
        # sanity checks:
        assert isinstance(template['items'], Sequence)

        # is a pathology Node
        node = {
            "name": name,
            "id": parent_id,
            "activatable": True,
        }
        if 'global_opts' not in template:
            global_opts = []
        else:
            global_opts = template['global_opts']

            assert isinstance(template['global_opts'], Sequence)

        node["children"] = [
            parse_child(
                child=child,
                parent_id=parent_id,
                child_id=child_id,
                activatable_child=True,
                single_selectable_child=False,
                global_opts=global_opts
            )
            for child_id, child in enumerate(template['items'])
        ]
        return node
    else:
        # is headline/region
        node = {
            "name": name,
            "id": parent_id,
            "activatable": True,
        }

        node["children"] = [
            parse_template_recursive(name=name, template=child, parent_id=parent_id)
            for name, child in template.items()
        ]
        return node


def parse_child(
        child: typing.Mapping[str, typing.Any] | str,
        parent_id: str,
        child_id: int,
        global_opts: typing.Sequence[typing.Any],
        activatable_child: bool = True,
        single_selectable_child: bool = False,

) -> typing.Dict[str, typing.Any]:
    if isinstance(child, str):
        node = {
            "name": child,
            "id": f"{parent_id}_{str(child_id)}",
            "activatable": activatable_child,
            "single-selectable": single_selectable_child,
        }
        if len(global_opts) > 0:
            node['children'] = []
            for sub_child_id, sub_opts in enumerate(global_opts):
                try:
                    single_selection = sub_opts['singe-selection']
                except KeyError:
                    single_selection = True
                else:
                    pass
                finally:
                    single_selection: bool

                node['children'].append(
                    parse_child(
                        child=sub_opts,
                        parent_id=node['id'],
                        child_id=sub_child_id,
                        activatable_child=False,
                        single_selectable_child=single_selection,
                        global_opts=[],
                    )
                )

        else:
            node['activatable'] = True
        return node
    elif isinstance(child, Sequence):
        children = [
            parse_child(
                child=child_item,
                parent_id=f"{parent_id}_{str(child_id)}",
                child_id=sub_child_id,
                activatable_child=activatable_child,
       return children

    elif isinstance(child, Mapping):

        for sub_child_id, (child_name, child_item) in enumerate(child.items()):

            try:
                single_selection = child_item['singe-selection']
            except KeyError:
                single_selection = True
            else:
                pass
            finally:
                single_selection: bool

            node = {
                "name": child_name,
                "id": f"{parent_id}_{str(child_id)}",
                "activatable": activatable_child,
                "single-selectable": single_selection,
            }

            node['children'] = parse_child(
                    child=child_item,
                    parent_id=node['id'],
                    child_id=sub_child_id,
                    activatable_child=False,
                    single_selectable_child=single_selection,
                    global_opts=[],
                )
            return node

            #
            # for sub_child_id, sub_opts in enumerate(child_map.items()):
            #     try:
            #         single_selection = sub_opts['singe-selection']
            #     except KeyError:
            #         single_selection = True
            #     else:
            #         pass
            #     finally:
            #         single_selection: bool
            #
            #     node['children'].append(
            #
            #     )
            #     node['children'] = [
            #         parse_child(child=sub_opts, parent_id=node['id'], child_id=sub_child_id, global_opts=[])
            #         for sub_child_id, sub_opts in enumerate(ChainMap(child_item, global_opts))
            #     ]

            return node


if __name__ == '__main__':
    transform_flat_to_nested('lung_lying_template.yaml')
