from bokeh.models.widgets import DataTable, TableColumn

import param

from ...core import Dataset
from ...element import ItemTable
from ..plot import GenericElementPlot
from .plot import BokehPlot
from .util import bokeh_version

class TablePlot(BokehPlot, GenericElementPlot):

    height = param.Number(default=None)

    width = param.Number(default=400)

    style_opts = ['row_headers', 'selectable', 'editable',
                  'sortable', 'fit_columns', 'width', 'height']

    _update_handles = ['source', 'glyph']

    def __init__(self, element, plot=None, **params):
        super(TablePlot, self).__init__(element, **params)
        self.handles = {} if plot is None else self.handles['plot']
        element_ids = self.hmap.traverse(lambda x: id(x), [Dataset, ItemTable])
        self.static = len(set(element_ids)) == 1 and len(self.keys) == len(self.hmap)


    def get_data(self, element, ranges=None, empty=False):
        dims = element.dimensions()
        return ({d.name: [] if empty else
                 [d.pprint_value(v) for v in element.dimension_values(d)]
                 for d in dims},
                {d.name: d.name for d in dims})


    def initialize_plot(self, ranges=None, plot=None, plots=None, source=None):
        """
        Initializes a new plot object with the last available frame.
        """
        # Get element key and ranges for frame
        element = self.hmap.last
        key = self.keys[-1]
        self.current_frame = element
        self.current_key = key

        data, _ = self.get_data(element, ranges)
        if source is None:
            source = self._init_datasource(data)
        self.handles['source'] = source

        dims = element.dimensions()
        columns = [TableColumn(field=d.name, title=str(d)) for d in dims]
        properties = self.lookup_options(element, 'style')[self.cyclic_index]
        table = DataTable(source=source, columns=columns, height=self.height,
                          width=self.width, **properties)
        self.handles['plot'] = table
        self.handles['glyph_renderer'] = table
        self.drawn = True

        return table


    @property
    def current_handles(self):
        """
        Returns a list of the plot objects to update.
        """
        handles = []
        if self.static and not self.dynamic:
            return handles

        previous_id = self.handles.get('previous_id', None)
        current_id = id(self.current_frame.data) if self.current_frame else None
        for handle in self._update_handles:
            if (handle == 'source' and self.dynamic and
                current_id == previous_id):
                continue
            if handle in self.handles:
                handles.append(self.handles[handle])

        # Cache frame object id to skip updating if unchanged
        if self.dynamic:
            self.handles['previous_id'] = current_id

        return handles


    def update_frame(self, key, ranges=None, plot=None):
        """
        Updates an existing plot with data corresponding
        to the key.
        """
        element = self._get_frame(key)
        source = self.handles['source']
        data, _ = self.get_data(element, ranges)
        self._update_datasource(source, data)
