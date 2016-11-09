__author__ = 'unicef-leb-inn'

import json

from rest_framework import status

from EquiTrack.factories import (
    PartnershipFactory,
    PartnerFactory,
    UserFactory,
    ResultFactory,
    ResultStructureFactory,
    LocationFactory,
    AgreementFactory,
)
from EquiTrack.tests.mixins import APITenantTestCase
from reports.models import ResultType, Sector
from funds.models import Grant, Donor
from partners.models import (
    PCA,
    Agreement,
    PartnerOrganization,
    ResultChain,
    PCASector,
    PartnershipBudget,
    PCAGrant,
    AmendmentLog,
    GwPCALocation,
)


class TestPartnershipViews(APITenantTestCase):
    fixtures = ['initial_data.json']
    def setUp(self):
        self.unicef_staff = UserFactory(is_staff=True)
        self.partner = PartnerFactory()
        agreement = AgreementFactory(partner=self.partner)
        self.intervention = PartnershipFactory(partner=self.partner, agreement=agreement)
        assert self.partner == self.intervention.partner

        self.result_type = ResultType.objects.get(id=1)
        self.result = ResultFactory(result_type=self.result_type, result_structure=ResultStructureFactory())
        self.resultchain = ResultChain.objects.create(
            result=self.result,
            result_type=self.result_type,
            partnership=self.intervention,
        )
        self.pcasector = PCASector.objects.create(
            pca=self.intervention,
            sector=Sector.objects.create(name="Sector 1")
        )
        self.partnership_budget = PartnershipBudget.objects.create(
            partnership=self.intervention,
            unicef_cash=100
        )
        self.grant = Grant.objects.create(
            donor=Donor.objects.create(
                name="Donor 1"
            ),
            name="Grant 1"
        )
        self.pcagrant = PCAGrant.objects.create(
            partnership=self.intervention,
            grant=self.grant,
            funds=100
        )
        self.amendment = AmendmentLog.objects.create(
            partnership=self.intervention,
            type="Cost",
        )
        self.location = GwPCALocation.objects.create(
            pca=self.intervention,
            location=LocationFactory()
        )


    def test_api_partners_list(self):
        response = self.forced_auth_req('get', '/api/partners/', user=self.unicef_staff)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)
        self.assertIn("Partner", response.data[0]["name"])

    def test_api_agreements_create(self):

        data = {
            "agreement_type": "PCA",
            "partner": self.intervention.partner.id,
            "status": "active"
        }
        response = self.forced_auth_req(
            'post',
            '/api/partners/'+str(self.intervention.partner.id)+'/agreements/',
            user=self.unicef_staff,
            data=data
        )

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

    def test_api_agreements_list(self):

        response = self.forced_auth_req('get', '/api/partners/'+str(self.intervention.partner.id)+'/agreements/', user=self.unicef_staff)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)
        self.assertIn("PCA", response.data[0]["agreement_type"])

    def test_api_interventions_list(self):

        response = self.forced_auth_req('get', '/api/partners/'+str(self.intervention.partner.id)+'/interventions/', user=self.unicef_staff)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)
        self.assertIn("galaxy", response.data[0]["pca_title"])
        self.assertIn("galaxy", response.data[0]["title"])
        self.assertIn("in_process", response.data[0]["status"])
        self.assertIn("PD", response.data[0]["partnership_type"])

    def test_api_agreement_interventions_list(self):

        response = self.forced_auth_req('get',
                                        '/'.join([
                                            '/api/partners',
                                            str(self.intervention.partner.id),
                                            'agreements',
                                            str(self.intervention.agreement.id),
                                            'interventions/'
                                        ]), user=self.unicef_staff)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)
        self.assertIn("galaxy", response.data[0]["title"])
        self.assertIn("in_process", response.data[0]["status"])

    def test_api_staffmembers_list(self):
        response = self.forced_auth_req('get',
                                        '/'.join(['/api/partners', str(self.partner.id), 'staff-members/']),
                                        user=self.unicef_staff)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)
        self.assertIn("Jedi Master", response.data[0]["title"])
        self.assertIn("Mace", response.data[0]["first_name"])
        self.assertIn("Windu", response.data[0]["last_name"])
        self.assertEqual(True, response.data[0]["active"])

    def test_api_interventions_results_list(self):

        response = self.forced_auth_req('get',
                                        '/'.join([
                                            '/api/partners',
                                            str(self.intervention.partner.id),
                                            'interventions',
                                            str(self.intervention.id),
                                            'results/'
                                        ]), user=self.unicef_staff)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)
        self.assertIn("Result", response.data[0]["result"]["name"])

    def test_api_interventions_sectors_list(self):

        response = self.forced_auth_req('get',
                                        '/'.join([
                                            '/api/partners',
                                            str(self.intervention.partner.id),
                                            'interventions',
                                            str(self.intervention.id),
                                            'sectors/'
                                        ]), user=self.unicef_staff)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)
        self.assertIn("Sector", response.data[0]["sector_name"])

    def test_api_interventions_budgets_list(self):

        response = self.forced_auth_req('get',
                                        '/'.join([
                                            '/api/partners',
                                            str(self.intervention.partner.id),
                                            'interventions',
                                            str(self.intervention.id),
                                            'budgets/'
                                        ]), user=self.unicef_staff)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)
        self.assertEquals(response.data[0]["unicef_cash"], 100)
        self.assertEquals(response.data[0]["total"], 100)

    def test_api_interventions_files_list(self):

        response = self.forced_auth_req('get',
                                        '/'.join([
                                            '/api/partners',
                                            str(self.intervention.partner.id),
                                            'interventions',
                                            str(self.intervention.id),
                                            'files/'
                                        ]), user=self.unicef_staff)

        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_api_interventions_grants_list(self):

        response = self.forced_auth_req('get',
                                        '/'.join([
                                            '/api/partners',
                                            str(self.intervention.partner.id),
                                            'interventions',
                                            str(self.intervention.id),
                                            'grants/'
                                        ]), user=self.unicef_staff)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)
        self.assertEquals(response.data[0]["grant"], self.grant.id)
        self.assertEquals(response.data[0]["funds"], 100)

    def test_api_interventions_amendments_list(self):

        response = self.forced_auth_req('get',
                                        '/'.join([
                                            '/api/partners',
                                            str(self.intervention.partner.id),
                                            'interventions',
                                            str(self.intervention.id),
                                            'amendments/'
                                        ]), user=self.unicef_staff)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)
        self.assertEquals(response.data[0]["type"], "Cost")

    def test_api_interventions_locations_list(self):

        response = self.forced_auth_req('get',
                                        '/'.join([
                                            '/api/partners',
                                            str(self.intervention.partner.id),
                                            'interventions',
                                            str(self.intervention.id),
                                            'locations/'
                                        ]), user=self.unicef_staff)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)
        self.assertIn("Location", response.data[0]["location_name"])


class TestPartnerOrganizationViews(APITenantTestCase):

    def setUp(self):
        self.unicef_staff = UserFactory(is_staff=True)
        self.partner = PartnerFactory()

    def test_api_partners_list(self):
        response = self.forced_auth_req('get', '/api/partners/', user=self.unicef_staff)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)

    def test_api_partners_create(self):
        data = {
            "name": "PO 1",
            "partner_type": "Government",
            "vendor_number": "AAA",
        }
        response = self.forced_auth_req(
            'post',
            '/api/partners/',
            user=self.unicef_staff,
            data=data
        )

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)


class TestAgreementAPIView(APITenantTestCase):

    def setUp(self):
        self.unicef_staff = UserFactory(is_staff=True)
        self.partner = PartnerFactory()
        self.agreement = AgreementFactory(partner=self.partner)
        self.agreement2 = AgreementFactory(
                                partner=self.partner,
                                agreement_type="MOU",
                                status="draft"
                            )
        self.intervention = PartnershipFactory(partner=self.partner, agreement=self.agreement)

    def test_agreements_list(self):
        response = self.forced_auth_req(
            'get',
            '/api/v2/partners/{}/agreements/'.format(self.partner.id),
            user=self.unicef_staff
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 2)
        self.assertIn("Partner", response.data[0]["partner_name"])
        self.assertEquals(response.data[0]["agreement_type"], Agreement.AGREEMENT_TYPES[2][0])

    def test_agreements_create(self):
        data = {
            "agreement_type":"PCA",
            "partner": self.partner.id,
            "status": "draft"
        }
        response = self.forced_auth_req(
            'post',
            '/api/v2/partners/{}/agreements/'.format(self.partner.id),
            user=self.unicef_staff,
            data=data
        )

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

    def test_agreements_update(self):
        data = {
            "status":"active",
        }
        response = self.forced_auth_req(
            'patch',
            '/api/v2/partners/{}/agreements/{}/'.format(self.partner.id, self.agreement.id),
            user=self.unicef_staff,
            data=data
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data["status"], "active")

    def test_agreements_retrieve(self):
        response = self.forced_auth_req(
            'get',
            '/api/v2/partners/{}/agreements/{}/'.format(self.partner.id, self.agreement.id),
            user=self.unicef_staff
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data["agreement_type"], Agreement.AGREEMENT_TYPES[0][0])


    def test_agreements_list_filter_type(self):
        params = {"agreement_type": "PCA"}
        response = self.forced_auth_req(
            'get',
            '/api/v2/partners/{}/agreements/'.format(self.partner.id),
            user=self.unicef_staff,
            data=params
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)
        self.assertEquals(response.data[0]["id"], self.agreement.id)
        self.assertEquals(response.data[0]["agreement_type"], "PCA")

    def test_agreements_list_filter_status(self):
        params = {"status": "active"}
        response = self.forced_auth_req(
            'get',
            '/api/v2/partners/{}/agreements/'.format(self.partner.id),
            user=self.unicef_staff,
            data=params
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 1)
        self.assertEquals(response.data[0]["id"], self.agreement.id)
        self.assertEquals(response.data[0]["status"], "active")

    def test_agreements_list_filter_partner_name(self):
        params = {"partner_name": "Partner"}
        response = self.forced_auth_req(
            'get',
            '/api/v2/partners/{}/agreements/'.format(self.partner.id),
            user=self.unicef_staff,
            data=params
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 2)
        self.assertIn("Partner", response.data[0]["partner_name"])

    def test_agreements_list_filter_search(self):
        params = {"search": "Partner"}
        response = self.forced_auth_req(
            'get',
            '/api/v2/partners/{}/agreements/'.format(self.partner.id),
            user=self.unicef_staff,
            data=params
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), 2)
        self.assertIn("Partner", response.data[0]["partner_name"])
