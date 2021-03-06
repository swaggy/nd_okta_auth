import datetime
import unittest
import mock

from nd_okta_auth import aws


class TestCredentials(unittest.TestCase):

    @mock.patch('configparser.ConfigParser')
    @mock.patch('nd_okta_auth.aws.open')
    def test_add_profile(self, open_mock, parser_mock):
        fake_parser = mock.MagicMock(name='config_parser')
        parser_mock.return_value = fake_parser

        # Trigger the code to try to create a new section
        fake_parser.has_section.return_value = None

        profile = aws.Credentials('/test')
        profile.add_profile(
            name='TestProfile',
            region='us-east-1',
            access_key='key',
            secret_key='secret',
            session_token='token')

        fake_parser.assert_has_calls([
            mock.call.has_section(u'TestProfile'),
            mock.call.add_section(u'TestProfile'),
            mock.call.set(u'TestProfile', u'region', u'us-east-1'),
            mock.call.set(u'TestProfile', u'aws_session_token', u'token'),
            mock.call.set(u'TestProfile', u'aws_security_token', u'token'),
            mock.call.set(u'TestProfile', u'aws_secret_access_key', u'secret'),
            mock.call.set(u'TestProfile', u'output', u'json'),
            mock.call.set(u'TestProfile', u'aws_access_key_id', u'key')
        ])

    @mock.patch('configparser.ConfigParser')
    @mock.patch('nd_okta_auth.aws.open')
    def test_add_profile_missing_file_creates_new(self,
                                                  open_mock,
                                                  parser_mock):
        fake_parser = mock.MagicMock(name='config_parser')
        parser_mock.return_value = fake_parser

        # First time its called, throw an IOError to indicate the file doesnt
        # exist. Second time its called it returns a Mock for fake writing of
        # data.
        open_mock.side_effect = [IOError(), mock.MagicMock()]

        profile = aws.Credentials('/test')
        profile.add_profile(
            name='TestProfile',
            region='us-east-1',
            access_key='key',
            secret_key='secret',
            session_token='token')

        open_mock.assert_has_calls([
            mock.call('/test', 'r'),
            mock.call('/test', 'w+')
        ])


class TestSesssion(unittest.TestCase):

    @mock.patch('aws_role_credentials.models.SamlAssertion')
    def setUp(self, mock_saml):
        self.fake_assertion = mock.MagicMock(name='FakeAssertion')
        mock_saml.return_value = self.fake_assertion

    def test_is_valid_false(self):
        session = aws.Session('BogusAssertion')

        # Mock out the expiration time to 4:10PM UTC
        expir_mock = datetime.datetime(2017, 7, 25, 16, 10, 00, 000000)
        # Now set our current time to 4:05PM UTC
        mock_now = datetime.datetime(2017, 7, 25, 16, 4, 00, 000000)

        # Should return False - less than 600 seconds away from expiration
        with mock.patch('datetime.datetime') as dt_mock:
            dt_mock.utcnow.return_value = mock_now
            dt_mock.strptime.return_value = expir_mock
            ret = session.is_valid

        self.assertEquals(False, ret)

    def test_is_valid_true(self):
        session = aws.Session('BogusAssertion')

        # Mock out the expiration time to 4:10PM UTC
        expir_mock = datetime.datetime(2017, 7, 25, 16, 10, 00, 000000)
        # Now set our current time to 3:55PM UTC
        mock_now = datetime.datetime(2017, 7, 25, 15, 55, 00, 000000)

        # Should return False - less than 600 seconds away from expiration
        with mock.patch('datetime.datetime') as dt_mock:
            dt_mock.utcnow.return_value = mock_now
            dt_mock.strptime.return_value = expir_mock
            ret = session.is_valid

        self.assertEquals(True, ret)
