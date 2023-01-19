import json
from typing import Any, Dict, List, Tuple


class VariableJsonOptions:
    def __init__(self, variable_key='$vars', delimiter='.', max_recurse=1024, keep_vars=False, emitted_name='$vars') -> None:
        self.variable_key = variable_key
        self.delimiter = delimiter
        self.max_recurse = max_recurse
        self.keep_vars = keep_vars
        self.emitted_name = emitted_name


class VariableJson:
    @staticmethod
    def parse(json: str = '', options: VariableJsonOptions = VariableJsonOptions()) -> str:
        return VariableJson.__VariableJsonPaser(json, options).parse()

    class __VariableJsonPaser:
        def __init__(self, json_data: str, options: VariableJsonOptions) -> None:
            self.json = json_data
            self.options = options
            self.json_object = json.loads(json_data)
            self.out_object = {}
            self.recurse = 0

            if self.options.variable_key in self.json_object:
                self.variables = json.loads(json.dumps(
                    self.json_object[self.options.variable_key]))
                del self.json_object[self.options.variable_key]

        def parse(self) -> str:
            if self.variables == None or (self.variables and len(self.variables) == 0):
                return json.dumps(self.json_object)

            self.parse_dfs(self.json_object, self.out_object)

            if self.options.keep_vars:
                self.out_object[self.options.emitted_name] = self.variables

            return json.dumps(self.out_object)

        def parse_dfs(self, node: dict | list, out_node: dict | list, path: str = '') -> None:
            if isinstance(node, Dict):
                for key, value in node.items():
                    self.insert_node(out_node, path +
                                     self.options.delimiter + key, value)
            elif isinstance(node, List):
                for index, value in enumerate(node):
                    self.insert_node(out_node, path +
                                     self.options.delimiter + str(index), value)

        def insert_node(self, node: dict | list, path: str, value: Any) -> None:
            (is_ref, ref_name) = self.is_ref(value)
            if is_ref:
                self.recurse = 0
                (found_ref, ref_value) = self.find_ref(ref_name)
                if not found_ref:
                    raise ReferenceError('Variable ' + ref_name + ' not found')
                else:
                    value = ref_value

            (_, key) = self.parse_path(path)

            if value == None:
                self.insert_node_untyped(node, None, key)
            elif isinstance(value, List):
                vnode = []
                self.parse_dfs(value, vnode)
                self.insert_node_untyped(node, vnode, key)
            elif isinstance(value, Dict):
                vnode = {}
                self.parse_dfs(value, vnode)
                self.insert_node_untyped(node, vnode, key)
            else:
                self.insert_node_untyped(node, value, key)

        def insert_node_untyped(self, node, value, key) -> None:
            if isinstance(node, Dict):
                node[key] = value
            elif isinstance(node, List):
                node.append(value)

        def parse_path(self, path: str) -> Tuple[List[str], str]:
            if path.startswith(self.options.delimiter):
                path = path[1:]

            parts = path.split(self.options.delimiter)
            key = parts[len(parts) - 1]
            parts.pop()

            return parts, key

        def is_ref(self, value) -> Tuple[bool, str]:
            if type(value) is not str:
                return False, None

            if len(value) > 3 and value.startswith('$(') and value.endswith(')'):
                return True, value[2:-1]

            return False, None

        def find_ref(self, ref) -> Tuple[bool, Any]:
            (parts, key) = self.parse_path(ref)

            return self.find_ref_dfs(self.variables, parts, key)

        def find_ref_dfs(self, node, path, key) -> Tuple[bool, Any]:
            self.recurse += 1
            if self.recurse > self.options.max_recurse:
                raise RecursionError('Maximum recursion reached')

            if isinstance(node, List):
                if len(path) > 0:
                    index = int(path[0])
                    obj = node[index]

                    (_, ref_name) = self.is_ref(obj)
                    (_, ref_value) = self.find_ref(ref_name)

                    return self.find_ref_dfs(ref_value, path[1:], key)
                else:
                    try:
                        index = int(key)
                        if index < len(node):
                            obj = node[index]
                            (is_ref, ref_name) = self.is_ref(obj)
                            if is_ref:
                                (_, ref_value) = self.find_ref(ref_name)
                                return True, ref_value
                            else:
                                return True, obj
                        else:
                            raise IndexError('Index ' + key + ' out of range')
                    except ValueError:
                        raise ValueError('Index ' + key + ' is not an integer')

            elif isinstance(node, Dict):
                if len(path) > 0:
                    obj = node[path[0]]
                    (is_ref, ref_name) = self.is_ref(obj)
                    if is_ref:
                        (_, ref_value) = self.find_ref(ref_name)
                        return self.find_ref_dfs(ref_value, path[1:], key)
                    else:
                        if isinstance(node, Dict) or isinstance(node, List):
                            return self.find_ref_dfs(obj, path[1:], key)
                        else:
                            raise ReferenceError(
                                'Invalid path ' + path.join(self.options.delimiter) + self.options.delimiter + key)
                else:
                    if key in node:
                        (is_ref, ref_name) = self.is_ref(node[key])
                        if is_ref:
                            return self.find_ref(ref_name)
                        return True, node[key]

            return False, None


def parse(json: str = '', options: VariableJsonOptions = VariableJsonOptions()) -> str:
    return VariableJson.parse(json, options)
