# -*- coding: utf-8 -*-
# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import logging
import time
from datetime import timedelta
from datetime import datetime
from threading import Lock

import pymongo
from pymongo import MongoClient
import json

from opcua import ua
from opcua.common.utils import Buffer
from opcua.common import events
from opcua.server.history import HistoryStorageInterface


class HistoryMongo(HistoryStorageInterface):
    """
    history backend which stores data values and object events in a Mongo database
    this backend is intended to only be accessed via OPC UA, therefore all UA Variants saved in
    the history database are in binary format (Mongo BLOBs)
    note that PARSE_DECLTYPES is active so certain data types (such as datetime) will not be BLOBs
    """

    def __init__(self, host='localhost', port=27017, path="history"):
        self.logger = logging.getLogger(__name__)
        self._datachanges_period = {}
        self._host = host
        self._port = port
        self._lock = Lock()
        self._event_fields = {}
        self._path = path

        self._client = MongoClient(self._host, self._port)
        self._db = self._client[self._path]

    def new_historized_node(self, node_id, period, count=0):
        with self._lock:

            table = self._get_table_name(node_id)

            self._datachanges_period[node_id] = period, count

    def save_node_value(self, node_id, datavalue):
        with self._lock:
            table = self._get_table_name(node_id)
            try:
                if datavalue.Value.VariantType is ua.VariantType.Null:
                    return
                query = "{\'ServerTimeStamp\':\'" + str(
                    datavalue.ServerTimestamp) + "\',\'SourceTimeStamp\':\'" + str(
                    datavalue.SourceTimestamp) + "\',\'StatusCode\':" + str(
                    datavalue.StatusCode.value) + ",\'Value\':" + json.dumps(
                    datavalue.Value.Value) + ",\'VariantType\':\'" + datavalue.Value.VariantType.name + "\'}"
                print(query)
                self._db[table].insert(eval(query))
            finally:
                pass
            # get this node's period from the period dict and calculate the
            # limit
            period, count = self._datachanges_period[node_id]

            if period:
                # after the insert, if a period was specified delete all
                # records older than period
                date_limit = datetime.utcnow() - period
                try:
                    self._db[table].remove(
                        {"ServerTimeStamp": {"$lt": date_limit}})
                finally:
                    pass

            if count:
                # ensure that no more than count records are stored for the
                # specified node
                if count < self._db[table].find().count():
                    results = self._db[table].find().sort(
                        'ServerTimeStamp', pymongo.DESCENDING).limit(count)
                    self._db[table].remove(
                        {"ServerTimeStamp": {"$lt": results[count - 1]['ServerTimeStamp']}})

    def read_node_history(self, node_id, start, end, nb_values):
        with self._lock:
            table = self._get_table_name(node_id)
            if nb_values > 300:
                nb_values = 300
            start_time, end_time, order, limit = self._get_bounds(
                start, end, nb_values)
            cont = None
            results = []
            # select values from the database; recreate UA Variant from binary
            try:
                if limit > 0:
                    cursor = self._db[table].find({"ServerTimeStamp": {"$gte": start_time, "$lt": end_time}}).sort(
                        'ServerTimeStamp', pymongo.DESCENDING).limit(limit)
                else:
                    cursor = self._db[table].find(
                        {"ServerTimeStamp": {"$gte": start_time, "$lt": end_time}})
                for result in cursor:
                    dv = ua.DataValue(result['Value'])
                    dv.ServerTimestamp = datetime.strptime(
                        result['ServerTimeStamp'], "%Y-%m-%d %H:%M:%S.%f")
                    dv.SourceTimestamp = datetime.strptime(
                        result['SourceTimeStamp'], "%Y-%m-%d %H:%M:%S.%f")
                    dv.StatusCode = ua.StatusCode(result['StatusCode'])
                    results.append(dv)
            finally:
                pass

            if nb_values:
                if len(results) > nb_values:
                    cont = results[nb_values].ServerTimestamp
                results = results[:nb_values]
                for result in results:
                    print(result)
            return results, cont

    def new_historized_event(self, source_id, evtypes, period, count=0):

        with self._lock:
            #_c_new = self._conn.cursor()

            # get all fields for the event type nodes
            ev_fields = self._get_event_fields(evtypes)

            self._datachanges_period[source_id] = period
            self._event_fields[source_id] = ev_fields

            table = self._get_table_name(source_id)
            columns = self._get_event_columns(ev_fields)

    def save_event(self, event):

        with self._lock:

            table = self._get_table_name(event.SourceNode)
            columns, placeholders, evtup = self._format_event(event)
            event_type = event.EventType  # useful for troubleshooting database

            # insert the event into the database
            try:
                query = "{\'_Timestamp\':\'" + str(event.Time) + "\',\'_EventTypeName\':\'" + str(
                    event_type) + "\',\'" + columns + "\':" + str(placeholders) + "}"
                self._db[table].insert(eval(query))
            finally:
                pass

            # get this node's period from the period dict and calculate the
            # limit
            period = self._datachanges_period[event.SourceNode]

            if period:
                # after the insert, if a period was specified delete all
                # records older than period
                date_limit = datetime.utcnow() - period

                try:
                    self._db[table].remove({"_Timestamp": {"$lt": date_limit}})
                finally:
                    pass

    def read_event_history(self, source_id, start, end, nb_values, evfilter):

        with self._lock:
            #_c_read = self._conn.cursor()

            table = self._get_table_name(source_id)
            start_time, end_time, order, limit = self._get_bounds(
                start, end, nb_values)
            clauses, clauses_str = self._get_select_clauses(
                source_id, evfilter)

            cont = None
            cont_timestamps = []
            results = []

            # select events from the database; SQL select clause is built from
            # EventFilter and available fields
            try:
                cursor = self._db[table].find({"_Timestamp": {"$gte": start_time, "$lt": end_time}}).sort(
                    '_Timestamp', pymongo.DESCENDING).limit(limit)
                for result in cursor:
                    fdict = {}
                    cont_timestamps.append(result['_Timestamp'])
                    for i, field in enumerate(result['clauses_str']):
                        if field is not None:
                            fdict[clauses[i]] = variant_from_binary(
                                Buffer(field))
                        else:
                            fdict[clauses[i]] = ua.Variant(None)

                    results.append(events.Event.from_field_dict(fdict))

            finally:
                pass

            if nb_values:
                if len(results) > nb_values:  # start > ua.get_win_epoch() and
                    cont = cont_timestamps[nb_values]

                results = results[:nb_values]

            return results, cont

    def _get_table_name(self, node_id):
        return 'table_' + str(node_id.NamespaceIndex) + \
            '_' + str(node_id.Identifier)

    def _get_event_fields(self, evtypes):
        """
        Get all fields from the event types that are to be historized
        Args:
            evtypes: List of event type nodes

        Returns: List of fields for all event types

        """
        # get all fields from the event types that are to be historized
        ev_aggregate_fields = []
        for event_type in evtypes:
            ev_aggregate_fields.extend(
                (events.get_event_properties_from_type_node(event_type)))

        ev_fields = []
        for field in set(ev_aggregate_fields):
            ev_fields.append(field.get_display_name().Text)
        return ev_fields

    @staticmethod
    def _get_bounds(start, end, nb_values):
        order = "ASC"

        if start is None or start == ua.get_win_epoch():
            order = "DESC"
            start = ua.get_win_epoch()

        if end is None or end == ua.get_win_epoch():
            end = datetime.utcnow() + timedelta(days=1)

        if start < end:
            start_time = start.isoformat(' ')
            end_time = end.isoformat(' ')
        else:
            order = "DESC"
            start_time = end.isoformat(' ')
            end_time = start.isoformat(' ')

        if nb_values:
            limit = nb_values + 1  # add 1 to the number of values for retrieving a continuation point
        else:
            limit = -1  # in SQLite a LIMIT of -1 returns all results

        return start_time, end_time, order, limit

    def _format_event(self, event):
        """
        Convert an event object triggered by the subscription into ordered lists for the SQL insert string

        Args:
            event: The event returned by the subscription

        Returns: List of event fields (SQL column names), List of '?' placeholders, Tuple of variant binaries

        """
        placeholders = []
        ev_variant_binaries = []

        ev_variant_dict = event.get_event_props_as_fields_dict()
        names = sorted(ev_variant_dict.keys())

        # split dict into two synchronized lists which will be converted to SQL strings
        # note that the variants are converted to binary objects for storing in
        # SQL BLOB format
        for name in names:
            variant = ev_variant_dict[name]
            placeholders.append('?')
            ev_variant_binaries.append(
                sqlite3.Binary(
                    variant_to_binary(variant)))

        return self._list_to_sql_str(names), self._list_to_sql_str(
            placeholders, False), tuple(ev_variant_binaries)

    def _get_event_columns(self, ev_fields):
        fields = []
        for field in ev_fields:
            fields.append(field + ' BLOB')
        return self._list_to_sql_str(fields, False)

    def _get_select_clauses(self, source_id, evfilter):
        s_clauses = []
        for select_clause in evfilter.SelectClauses:
            try:
                if not select_clause.BrowsePath:
                    s_clauses.append(select_clause.Attribute.name)
                else:
                    name = select_clause.BrowsePath[0].Name
                    s_clauses.append(name)
            except AttributeError:
                self.logger.warning(
                    'Historizing SQL OPC UA Select Clause Warning for node %s,'
                    ' Clause: %s:', source_id, select_clause)

        # remove select clauses that the event type doesn't have; SQL will
        # error because the column doesn't exist
        clauses = [x for x in s_clauses if x in self._event_fields[source_id]]
        return clauses, self._list_to_sql_str(clauses)

    @staticmethod
    def _list_to_sql_str(ls, quotes=True):
        sql_str = ''
        for item in ls:
            if quotes:
                sql_str += '"' + item + '", '
            else:
                sql_str += item + ', '
        return sql_str[:-2]  # remove trailing space and comma for SQL syntax

    def stop(self):
        with self._lock:
            self._client.close()
            self.logger.info('Historizing SQL connection closed')
