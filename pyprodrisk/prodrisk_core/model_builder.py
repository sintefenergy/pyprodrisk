from graphviz import Digraph

from ..prodrisk_core.prodrisk_api import get_attribute_value, get_xyt_attribute, get_attribute_info, \
    set_attribute, get_object_info

# This check can be used to stops infinite recursion in some debuggers when stepping into __init__. Debuggers can call
# __dir__ before/during the initialization, and if any class attributes are referred to in both __dir__ and __getattr__
# the call to dir will invoke __getattr__, which in turn will call itself indefinitely
def is_private_attr(attr):
    return attr[0] == '_'

class ModelBuilderType(object):

    def __init__(self, api, ignores=[]):
        self._api = api
        self._all_types = [object_type for object_type in api.GetObjectTypeNames() if object_type not in ignores ]
                           #  if api.GetObjectInfo(object_type, 'isInput')]
        self._types = []
        self._ignores = ignores
        self.update()

    def __getattr__(self, object_type):
        # Recursion guard
        if is_private_attr(object_type):
            return

        # if self._api.UpdateNeeded():
        #     self.update()
        return self._types[object_type]

    def __dir__(self):
        return [object_type for object_type in self._types] + \
               [x for x in super().__dir__() if x[0] != '_' and x not in self._types]

    def __getitem__(self, item):
        return self.__getattr__(item)

    def update(self):
        objects = {object_type: [] for object_type in self._all_types}
        for object_name, object_type in zip(self._api.GetObjectNamesInSystem(),
                                            self._api.GetObjectTypesInSystem()):
            if object_type not in self._ignores:
                objects[object_type].append(object_name)

        self._types = {object_type: ModelBuilderObject(self._api, self, object_type, object_names)
                       for object_type, object_names in objects.items()}

    def build_connection_tree(self, filename='topology', write_file=False):
        obj_map = {'module': ['reservoir', 'plant', 'gate']}
        # relation_types = ['connection_standard', 'connection_spill', 'connection_bypass']
        object_types = self._api.GetObjectTypesInSystem()
        object_names = self._api.GetObjectNamesInSystem()
        dot = Digraph(comment='ProdRisk topology')
        connections = []
        subgraphs = []

        # Number of detailed object described by the ProdRisk module object.
        # Each object need special handling in the hacky implementation below.
        n_shop_objs = len(obj_map['module'])

        # Mapping used to find module based on external module number.
        mod_nr_to_int_nr = {}
        i = 0
        for (name, object_type) in zip(object_names, object_types):
            if object_type == 'module':
                mod = self.module[name]
                mod_nr_to_int_nr[mod.number.get()] = i
                i = i + 1
            elif object_type == 'pump':
                i = i + 1

        shop_object_types = []
        shop_object_names = []
        shop_object_no = 0
        for i, (name, object_type) in enumerate(zip(object_names, object_types)):
            if object_type == 'module':
                shop_object_name = name
                mod = self.module[name]
                max_prod = mod.maxProd.get()
                max_vol = mod.rsvMax.get()
                topo = mod.topology.get()

                shape = 'invtriangle'
                bgcolor = 'skyblue'
                subgraph = None

                for shop_object_type in obj_map[object_type]:
                    shop_object_types.append(shop_object_type)

                    shape = 'invtriangle'
                    bgcolor = 'skyblue'
                    subgraph = None

                    shape = 'ellipse'
                    bgcolor = 'none'
                    subgraph = None
                    if shop_object_type == 'plant':
                        if max_prod <= 0:
                            shop_object_names.append(shop_object_name)
                            shop_object_no = shop_object_no + 1
                            continue
                        shape = 'box'
                        bgcolor = 'rosybrown1'
                        shop_object_name = mod.plantName.get()
                        connections.append((shop_object_no - 1, shop_object_no, 'connection_standard'))
                        if topo[0] > 0:
                            connections.append(
                                (shop_object_no, mod_nr_to_int_nr[topo[0]] * n_shop_objs, 'connection_standard'))
                    elif shop_object_type == 'reservoir' and max_vol > 0:
                        shape = 'invtriangle'
                        bgcolor = 'skyblue'
                        shop_object_name = mod.name.get()

                        if max_prod <= 0 and topo[0] > 0:
                            connections.append((shop_object_no, mod_nr_to_int_nr[topo[0]] * n_shop_objs, 'connection_standard'))

                    elif shop_object_type == 'gate':
                        shop_object_name = f"{mod.name.get()}_bypass"
                        connections.append(
                            (shop_object_no - 2, shop_object_no, 'connection_bypass'))

                        if topo[1] > 0:
                            connections.append((shop_object_no, mod_nr_to_int_nr[topo[1]] * n_shop_objs, 'connection_bypass'))

                    shop_object_names.append(shop_object_name)

                    shop_object_no = shop_object_no + 1
                    dot.node('{0}_{1}'.format(shop_object_type, shop_object_name), label=shop_object_name,
                             shape=shape, style='filled',
                             fillcolor=bgcolor)

            elif object_type == 'pump':
                shop_object_type = 'pump'
                shape = 'box'
                bgcolor = 'lightblue'

                pump = self.pump[name]
                shop_object_name = f"{pump.name.get()}"
                topo = pump.topology.get()

                for j in range(n_shop_objs):
                    shop_object_names.append(shop_object_name)
                    shop_object_types.append(shop_object_type)

                connections.append(
                    (shop_object_no, mod_nr_to_int_nr[topo[1]]* n_shop_objs, 'connection_standard'))
                connections.append(
                    (mod_nr_to_int_nr[topo[2]]* n_shop_objs, shop_object_no, 'connection_standard'))

                shop_object_no = shop_object_no + 3
                dot.node('{0}_{1}'.format(shop_object_type, shop_object_name), label=shop_object_name,
                         shape=shape, style='filled',
                         fillcolor=bgcolor)


        for connection in connections:
            if (shop_object_types[connection[0]] == 'gate' or shop_object_types[connection[1]] == 'gate') \
                    and connection[2] != 'connection_standard':
                dot.attr('edge', style='dashed')
            else:
                dot.attr('edge', style='solid', arrowtail='none', arrowhead='none')
            dot.edge('{0}_{1}'.format(shop_object_types[connection[0]], shop_object_names[connection[0]]),
                     '{0}_{1}'.format(shop_object_types[connection[1]], shop_object_names[connection[1]]))
        for s in subgraphs:
            dot.subgraph(s)
        if write_file:
            dot.render(filename + '.gv', view=True)
        return dot

class ModelBuilderObjectIterator(object):
    def __init__(self, model_builder_object):
        self._model_builder_object = model_builder_object
        self._index = 0

    def __next__(self):
        if self._index < len(self._model_builder_object.get_object_names()):
            self._index += 1
            return self._model_builder_object.__getattr__(
                self._model_builder_object.get_object_names()[self._index - 1])
        raise StopIteration


class ModelBuilderObject(object):
    def __init__(self, api, parent, object_type, object_names):
        self._api = api
        self._parent = parent
        self._type = object_type
        self._names = object_names
        self.attributes = {}

    def __getattr__(self, name):
        # Recursion guard
        if is_private_attr(name):
            return

        if name in self._names:
            if name not in self.attributes:
                attribute = AttributeBuilderObject(self._api, self._type, name)
                self.attributes[name] = attribute
            return self.attributes[name]
        else:
            raise AttributeError()

    def __dir__(self):
        return [x for x in super().__dir__() if x[0] != '_'] + self._names

    def __getitem__(self, item):
        return self.__getattr__(item)

    def add_object(self, name):
        self._api.AddObject(self._type, name)
        if name in self._api.GetObjectNamesInSystem():
            self._add_object_name(name)
        return self._parent.__getattr__(self._type).__getattr__(name)

    def _add_object_name(self, name):
        self._names.append(name)

    def get_object_names(self):
        return self._names

    def info(self):
        return get_object_info(self._api, self._type)

    def __iter__(self):
        return ModelBuilderObjectIterator(self)


class AttributeBuilderObject(object):
    def __init__(self, api, object_type, object_name):
        self._api = api
        self._type = object_type
        self._name = object_name
        self._attr_names = list(api.GetObjectTypeAttributeNames(object_type))
        self._attr_types = list(api.GetObjectTypeAttributeDatatypes(object_type))
        self.datatype_dict = dict(zip(self._attr_names, self._attr_types))

    def __getattr__(self, attr_name):
        # Recursion guard
        if is_private_attr(attr_name):
            return

        if attr_name in self._attr_names:
            return AttributeObject(self._api, self._type, self._name, attr_name, self.datatype_dict[attr_name])
        elif attr_name == 'generators' and self._type == 'plant':
            return self._get_generators()
        elif attr_name == 'unit_combinations' and self._type == 'plant':
            return self._get_unit_combinations()
        else:
            raise ValueError(f'Unknown attribute: "{attr_name}" for "{self._name}" ({self._type})')

    def __dir__(self):
        dirs = [x for x in super().__dir__() if x[0] != '_'] + self._attr_names
        if self._type == 'plant':
            return dirs + ['generators']
        else:
            return dirs

    def __getitem__(self, item):
        return self.__getattr__(item)

    def _get_generators(self):
        object_names = self._api.GetObjectNamesInSystem()
        generator_indices = self._api.GetRelations(self._type, self._name, 'generator_of_plant')
        gen_names = [object_names[i] for i in generator_indices]
        gen_objects = []
        for gen_name in gen_names:
            new_gen = AttributeBuilderObject(self._api, 'generator', gen_name)
            gen_objects.append(new_gen)
        return gen_objects

    def _get_unit_combinations(self):
        object_names = self._api.GetObjectNamesInSystem()
        comb_indices = self._api.GetRelations(self._type, self._name, 'unit_combination_of_plant')
        comb_names = [object_names[i] for i in comb_indices]
        comb_objects = []
        for comb_name in comb_names:
            new_comb = AttributeBuilderObject(self._api, 'unit_combination', comb_name)
            comb_objects.append(new_comb)
        return comb_objects

    def get_relations(self, direction="both", relation_type="all"):
        direction = direction.lower()
        relation_type = relation_type.lower()
        if direction not in ["both", "input", "output"]:
            raise ValueError('Unknown direction, possible values are "both", "input" and "output"')
        object_names = self._api.GetObjectNamesInSystem()
        object_types = self._api.GetObjectTypesInSystem()
        if relation_type == "all":
            relation_types = self._api.GetValidRelationTypes(self._type)
        else:
            relation_types = [relation_type]

        obj_list = []
        if direction == "input" or direction == "both":
            for relation_type in relation_types:
                input_relations = self._api.GetInputRelations(self._type, self._name, relation_type)
                for object_index in input_relations:
                    rel_object = AttributeBuilderObject(self._api, object_types[object_index],
                                                        object_names[object_index])
                    obj_list.append(rel_object)
        if direction == "output" or direction == "both":
            for relation_type in relation_types:
                output_relations = self._api.GetRelations(self._type, self._name, relation_type)
                for object_index in output_relations:
                    rel_object = AttributeBuilderObject(self._api, object_types[object_index],
                                                        object_names[object_index])
                    obj_list.append(rel_object)
        return obj_list

    # def connect(self, connection_type=''):
    #     connection_type = connection_type.lower()
    #     return ConnectToObjectType(self._api, self._type, self._name, connection_type)

    def connect_to(self, related_object, connection_type=''):
        connection_type = connection_type.lower()
        if not connection_type:
            connection_type = self._api.GetDefaultRelationType(self._type, related_object.get_type())
        else:
            if connection_type == "spill":
                connection_type = "connection_spill"
            elif connection_type == "bypass":
                connection_type = "connection_bypass"
            elif connection_type == "standard":
                connection_type = "connection_standard"
            else:
                raise ValueError(f'Unknown connection type: "{connection_type}"\nPyShop will use default connection '
                                 f'types if none are provided. Provided values can be "spill" or "bypass"')
        self._api.AddRelation(self._type, self._name, connection_type, related_object.get_type(),
                                   related_object.get_name())

    def get_name(self):
        return self._name

    def get_type(self):
        return self._type


class AttributeObject(object):
    def __init__(self, api, object_type, name, attr_name, attr_datatype):
        self._api = api
        self._type = object_type
        self._name = name
        self._attr_name = attr_name
        self._attr_datatype = attr_datatype

    def __getattr__(self, call):
        # Recursion guard
        if is_private_attr(call):
            return

        if call == 'get':
            if self._attr_datatype == 'xyt' and call == 'get':
                return self._get_xyt
            else:
                return self._get
        else:
            raise AttributeError()

    def __dir__(self):
        return [x for x in super().__dir__() if x[0] != '_'] + ['get']

    def __getitem__(self, item):
        return self.__getattr__(item)

    def _get(self):
        return get_attribute_value(self._api, self._name, self._type, self._attr_name, self._attr_datatype)

    def _get_xyt(self, start_time=None, end_time=None):
        if start_time and end_time:
            return get_xyt_attribute(self._api, self._name, self._type, self._attr_name, start_time, end_time)
        else:
            return get_attribute_value(self._api, self._name, self._type, self._attr_name, self._attr_datatype)

    def set(self, value):
        set_attribute(self._api, self._name, self._type, self._attr_name, self._attr_datatype, value)

    def help(self):
        print(self._api.GetAttributeInfo(self._type, self._attr_name, 'description'))

    # def web_help(self):
    #     url = self._api.GetAttributeInfo(self._type, self._attr_name, 'documentationUrl')
    #     if not url:
    #         print("Could not find attribute type")
    #         return
    #     opened = webbrowser.open(url)
    #     if not opened:
    #         print("Could not open browser, documentation can be found at {}".format(url))

    # def web_example(self):
    #     url_prefix = self._api.GetAttributeInfo(self._type, self._attr_name, 'exampleUrlPrefix')
    #     example = self._api.GetAttributeInfo(self._type, self._attr_name, 'example')
    #     if not example:
    #         print("Attribute does not currently have an associated example")
    #         return
    #     opened = webbrowser.open(url_prefix + example)
    #     if not opened:
    #         print("Could not open browser, documentation can be found at {}".format(url_prefix + example))

    def info(self):
        return get_attribute_info(self._api, self._type, self._attr_name)