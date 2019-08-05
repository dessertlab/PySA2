# Copyright 2016 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from oslo_log import log
import oslo_messaging

from vitrage.common.constants import EntityCategory
from vitrage.common.constants import NotifierEventTypes
from vitrage.common.constants import VertexProperties as VProps
from vitrage.evaluator.actions import evaluator_event_transformer as evaluator
from vitrage.messaging import get_transport


LOG = log.getLogger(__name__)


class GraphNotifier(object):
    """Allows writing to message bus"""
    def __init__(self, conf):
        self.oslo_notifier = None
        topics = self._get_topics(conf)
        if not topics:
            LOG.info('Graph Notifier is disabled')
            return
        self.oslo_notifier = oslo_messaging.Notifier(
            get_transport(conf),
            driver='messagingv2',
            publisher_id='vitrage.graph',
            topics=topics)

    @property
    def enabled(self):
        return self.oslo_notifier is not None

    def _get_topics(self, conf):
        topics = []

        try:
            notifier_topic = conf.entity_graph.notifier_topic
            notifier_plugins = conf.notifiers
            if notifier_topic and notifier_plugins:
                topics.append(notifier_topic)
        except Exception as e:
            LOG.info('Graph Notifier - missing configuration %s' % str(e))

        try:
            machine_learning_topic = \
                conf.machine_learning.machine_learning_topic
            machine_learning_plugins = conf.machine_learning.plugins
            if machine_learning_topic and machine_learning_plugins:
                topics.append(machine_learning_topic)
        except Exception as e:
            LOG.info('Machine Learning - missing configuration %s' % str(e))

        return topics

    def notify_when_applicable(self, before, current, is_vertex, graph):
        """Callback subscribed to driver.graph updates

        :param is_vertex:
        :param before: The graph element (vertex or edge) prior to the
        change that happened. None if the element was just created.
        :param current: The graph element (vertex or edge) after the
        change that happened. Deleted elements should arrive with the
        vitrage_is_deleted property set to True
        :param graph: The graph
        """
        notification_types = _get_notification_type(before, current, is_vertex)
        if not notification_types:
            return

        # in case the vertex point to some resource add the resource to the
        # notification (useful for deduce alarm notifications)
        if current.get(VProps.VITRAGE_RESOURCE_ID):
            current.properties[VProps.RESOURCE] = graph.get_vertex(
                current.get(VProps.VITRAGE_RESOURCE_ID))

        LOG.info('notification_types : %s', str(notification_types))
        LOG.info('notification properties : %s', current.properties)

        for notification_type in notification_types:
            try:
                self.oslo_notifier.info(
                    {},
                    notification_type,
                    current.properties)
            except Exception as e:
                LOG.exception('Cannot notify - %s - %s', notification_type, e)


def _get_notification_type(before, current, is_vertex):
    if not is_vertex:
        return None

    def notification_type(is_active,
                          activate_event_type,
                          deactivate_event_type):
        if not is_active(before):
            if is_active(current):
                return activate_event_type
        else:
            if not is_active(current):
                return deactivate_event_type

    notification_types = [
        notification_type(_is_active_deduced_alarm,
                          NotifierEventTypes.ACTIVATE_DEDUCED_ALARM_EVENT,
                          NotifierEventTypes.DEACTIVATE_DEDUCED_ALARM_EVENT),
        notification_type(_is_active_alarm,
                          NotifierEventTypes.ACTIVATE_ALARM_EVENT,
                          NotifierEventTypes.DEACTIVATE_ALARM_EVENT),
        notification_type(_is_marked_down,
                          NotifierEventTypes.ACTIVATE_MARK_DOWN_EVENT,
                          NotifierEventTypes.DEACTIVATE_MARK_DOWN_EVENT),
    ]
    return list(filter(None, notification_types))


def _is_active_deduced_alarm(vertex):
    if not vertex:
        return False
    if vertex.get(VProps.VITRAGE_CATEGORY) == EntityCategory.ALARM and \
            vertex.get(VProps.VITRAGE_TYPE) == evaluator.VITRAGE_DATASOURCE:
        return _is_relevant_vertex(vertex)
    return False


def _is_active_alarm(vertex):
    if vertex and vertex.get(VProps.VITRAGE_CATEGORY) == EntityCategory.ALARM:
        return _is_relevant_vertex(vertex)
    return False


def _is_marked_down(vertex):
    if not vertex:
        return False
    if vertex.get(VProps.VITRAGE_CATEGORY) == EntityCategory.RESOURCE and \
            vertex.get(VProps.IS_MARKED_DOWN) is True:
        return _is_relevant_vertex(vertex)
    return False


def _is_relevant_vertex(vertex):
    if vertex.get(VProps.VITRAGE_IS_DELETED, False) or \
            vertex.get(VProps.VITRAGE_IS_PLACEHOLDER, False):
        return False
    return True