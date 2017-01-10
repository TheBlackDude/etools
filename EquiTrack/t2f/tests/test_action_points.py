from __future__ import unicode_literals

import json

from django.core.urlresolvers import reverse

from EquiTrack.factories import UserFactory
from EquiTrack.tests.mixins import APITenantTestCase
from t2f.tests.factories import TravelFactory, ActionPointFactory


class ActionPoints(APITenantTestCase):
    def setUp(self):
        super(ActionPoints, self).setUp()
        self.traveler = UserFactory()
        self.unicef_staff = UserFactory(is_staff=True)
        self.travel = TravelFactory(traveler=self.traveler,
                                    supervisor=self.unicef_staff)

    def test_urls(self):
        list_url = reverse('t2f:action_points:list')
        self.assertEqual(list_url, '/api/t2f/action_points/')

        details_url = reverse('t2f:action_points:details', kwargs={'action_point_pk': 1})
        self.assertEqual(details_url, '/api/t2f/action_points/1/')

    def test_list_view(self):
        with self.assertNumQueries(4):
            response = self.forced_auth_req('get', reverse('t2f:action_points:list'), user=self.unicef_staff)

        response_json = json.loads(response.rendered_content)
        expected_keys = ['data', 'page_count', 'total_count']
        self.assertKeysIn(expected_keys, response_json)

        self.assertEqual(len(response_json['data']), 1)
        action_point_data = response_json['data'][0]
        self.assertEqual(set(action_point_data.keys()),
                         {'id',
                          'action_point_number',
                          'trip_reference_number',
                          'description',
                          'assigned_by',
                          'due_date',
                          'comments',
                          'person_responsible',
                          'status',
                          'completed_at',
                          'actions_taken',
                          'follow_up',
                          'created_at',
                          'trip_id'})

    def test_details(self):
        action_point_pk = self.travel.action_points.first().pk
        response = self.forced_auth_req('get', reverse('t2f:action_points:details',
                                                       kwargs={'action_point_pk': action_point_pk}),
                                        user=self.unicef_staff)
        response_json = json.loads(response.rendered_content)

        self.assertEqual(set(response_json.keys()),
                         {'status',
                          'trip_reference_number',
                          'action_point_number',
                          'actions_taken',
                          'assigned_by',
                          'description',
                          'due_date',
                          'actions_taken',
                          'created_at',
                          'comments',
                          'completed_at',
                          'follow_up',
                          'person_responsible',
                          'id',
                          'trip_id'})

    def test_searching(self):
        ActionPointFactory(travel=self.travel, description='search_in_desc')
        ap_2 = ActionPointFactory(travel=self.travel)

        response = self.forced_auth_req('get', reverse('t2f:action_points:list'), user=self.unicef_staff)
        response_json = json.loads(response.rendered_content)
        self.assertEqual(len(response_json['data']), 3)

        response = self.forced_auth_req('get', reverse('t2f:action_points:list'),
                                        data={'search': 'search_in_desc'},
                                        user=self.unicef_staff)
        response_json = json.loads(response.rendered_content)
        self.assertEqual(len(response_json['data']), 1)

        response = self.forced_auth_req('get', reverse('t2f:action_points:list'),
                                        data={'search': ap_2.action_point_number},
                                        user=self.unicef_staff)
        response_json = json.loads(response.rendered_content)
        self.assertEqual(len(response_json['data']), 1)
