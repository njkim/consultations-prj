'''
ARCHES - a program developed to inventory and manage immovable cultural heritage.
Copyright (C) 2013 J. Paul Getty Trust and World Monuments Fund

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

from django.http import HttpRequest, HttpResponseNotFound
from django.views.generic import View
from django.core.paginator import Paginator
from arches.app.utils.response import JSONResponse
from arches.app.models import models
from arches.app.models.resource import Resource
from arches.app.models.tile import Tile
from arches.app.datatypes.datatypes import DataTypeFactory
import json


class ActiveConsultationsView(View):

    def __init__(self):
        self.cons_details_nodegroupid = '8d41e4c0-a250-11e9-a7e3-00224800b26d'
        self.consultation_graphid = '8d41e49e-a250-11e9-9eab-00224800b26d'
        self.active_cons_node_list = {
            "Map":"8d41e4d6-a250-11e9-accd-00224800b26d",
            "Name":"8d41e4ab-a250-11e9-87d1-00224800b26d",
            "Consultation Type":"8d41e4dd-a250-11e9-9032-00224800b26d",
            "Proposal":"8d41e4bd-a250-11e9-89e8-00224800b26d",
            "Target Date":"8d41e4cb-a250-11e9-9cf2-00224800b26d",
            "Casework Officer":"8d41e4d4-a250-11e9-a3ff-00224800b26d"
        }
        self.active_cons_nodegroupid_list = {
            "Target Date":"8d41e4a5-a250-11e9-840c-00224800b26d",
            "Casework Officer":"8d41e4a8-a250-11e9-aff0-00224800b26d",
            "Name":"8d41e4ab-a250-11e9-87d1-00224800b26d",
            "Proposal":"8d41e4bd-a250-11e9-89e8-00224800b26d",
            "Consultation Type":"8d41e4c0-a250-11e9-a7e3-00224800b26d",
            "Geospatial Location":"8d41e4c6-a250-11e9-a54d-00224800b26d"
        }
        self.layout = 'grid'
        self.exclude_statuses = ["Aborted","Completed"]
        self.cons_status_node_id = '8d41e4d3-a250-11e9-8977-00224800b26d'
    
    def get(self, request):
        page_num = 1 if request.GET.get('page') == '' else int(request.GET.get('page'))
        datatype_factory = DataTypeFactory()
        cons_details_tiles = Tile.objects.filter(nodegroup_id=self.cons_details_nodegroupid)
        exclude_list = self.build_exclude_list(cons_details_tiles, datatype_factory)
        filtered_consultations = Resource.objects.filter(graph_id=self.consultation_graphid).exclude(resourceinstanceid__in=exclude_list)

        search_results_setting_nodeid = "d0987de3-fad8-11e6-a434-6c4008b05c4c"
        search_results_setting_nodegroupid = "d0987880-fad8-11e6-8cce-6c4008b05c4c"
        page_ct_tile = Tile.objects.get(nodegroup_id=search_results_setting_nodegroupid)
        page_ct = page_ct_tile.data[search_results_setting_nodeid]

        if filtered_consultations is not None:
            if page_num == -1:
                self.layout = 'table'
                tiles = self.get_tile_dict(filtered_consultations, datatype_factory)
                return JSONResponse({'results': tiles})
            elif page_num >= 1:
                tiles = self.get_tile_dict(filtered_consultations, datatype_factory)
                paginator = Paginator(tiles, page_ct)
                page_results = paginator.page(page_num)
                if page_results.has_next() is True:
                    next_page_number = page_results.next_page_number()
                else:
                    next_page_number = False
                if page_results.has_previous() is True:
                    prev_page_number = page_results.previous_page_number()
                else:
                    prev_page_number = False
                page_ct = paginator.num_pages
                pages = [page_num]
                if paginator.num_pages > 1: # all below creates abridged page list UI
                    before = range(1, page_num)
                    after = range(page_num+1, paginator.num_pages+1)
                    default_ct = 2
                    ct_before = default_ct if len(after) > default_ct else default_ct*2-len(after)
                    ct_after = default_ct if len(before) > default_ct else default_ct*2-len(before)
                    if len(before) > ct_before:
                        before = [1,None]+before[-1*(ct_before-1):]
                    if len(after) > ct_after:
                        after = after[0:ct_after-1]+[None,paginator.num_pages]
                    pages = before+pages+after

                page_config = {
                    'current_page':page_num,
                    'end_index':page_results.end_index(),
                    'has_next':page_results.has_next(),
                    'has_other_pages':page_results.has_other_pages(),
                    'has_previous':page_results.has_previous(),
                    'next_page_number':next_page_number,
                    'pages':pages,
                    'previous_page_number':prev_page_number,
                    'start_index':page_results.start_index()
                }
                return JSONResponse({'page_results': page_results.object_list, 'paginator': page_config})

        return HttpResponseNotFound()


    def build_exclude_list(self, tiles, datatype_factory):
        exclude_list = []
        cons_status_node = models.Node.objects.get(nodeid=self.cons_status_node_id)
        datatype = datatype_factory.get_instance(cons_status_node.datatype)
        for tile in tiles:
            if self.cons_status_node_id in tile.data.keys():
                tile_status = datatype.get_display_value(tile, cons_status_node)
                if tile_status in self.exclude_statuses:
                    exclude_list.append(str(tile.resourceinstance.resourceinstanceid))

        return exclude_list


    def get_tile_dict(self, consultations, datatype_factory):
        tiles = []
        active_cons_list_vals = self.active_cons_node_list.values()
        for consultation in consultations:
            res = {}
            consultation.load_tiles()
            for tile in consultation.tiles:
                for k, v in tile.data.items():
                    if k in active_cons_list_vals:
                        node = models.Node.objects.get(nodeid=k)
                        try:
                            datatype = datatype_factory.get_instance(node.datatype)
                            val = datatype.get_display_value(tile, node)
                            if self.layout == 'grid' and k == self.active_cons_node_list["Map"]:
                                val = json.loads(val)
                        except Exception as e:
                            val = v

                        res[node.name] = val
            res['resourceinstanceid'] = consultation.resourceinstanceid
            tiles.append(res)

        return tiles
