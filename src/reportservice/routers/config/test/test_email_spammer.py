import pytest
from pytest_mock import MockerFixture
from ..email_spammer import EmailSpammer


def test_email_spammer(mocker: MockerFixture):
    # mock the smtplib.SMTP object
    object = "src.reportservice.routers.config.email_spammer.smtplib.SMTP_SSL"
    mock_SMTP = mocker.MagicMock(name=object)
    mocker.patch(object, new=mock_SMTP)

    mailer = EmailSpammer("Nguyen Van Mock", "mock@lazada.com", "khongphaipassword")

    assert mock_SMTP.return_value.ehlo.call_count == 1
    assert mock_SMTP.return_value.login.call_count == 1

    mailer.send("to", "subject", "body")
    assert mock_SMTP.return_value.send_message.call_count == 1


@pytest.fixture
def spammerwithlove(stmpsettings):
    spammer = EmailSpammer(
        username=stmpsettings["username"],
        account=stmpsettings["account"],
        password=stmpsettings["password"],
        smtp_server=stmpsettings["server"],
        smtp_port=stmpsettings["port"],
        useSSL=stmpsettings["useSSL"],
    )
    yield spammer


def test_simple(spammerwithlove):
    spammerwithlove.send(to="lazada@shopee.com", subject="test_simple", body="this is the body")


def test_simple_multiple(spammerwithlove):
    spammerwithlove.send(
        to="lazada@lazada.com,shopee@shopee.com", subject="test_simple_multiple", body="this is the body"
    )


def test_simple_multiple_with_cc_bcc(spammerwithlove):
    spammerwithlove.send(
        to="lazada@lazada.com,shopee@shopee.com",
        cc="vietnameairline@vietnameairfine@.com,a@a.com",
        bcc="example@example.com,ok@ok.org",
        subject="test_simple_multiple_with_cc_bcc",
        body="this is the body",
    )


def test_with_attachment_file(spammerwithlove, excelfile):
    spammerwithlove.send(
        to="lazada@lazada.com,shopee@shopee.com",
        cc="vietnameairline@vietnameairfine@.com,a@a.com",
        bcc="example@example.com,ok@ok.org",
        subject="test_with_attachment_file",
        body="this is the body",
        attachment_filename=excelfile,
    )


def test_with_attachment_rawdata(spammerwithlove, excelbytes):
    spammerwithlove.send(
        to="lazada@lazada.com,shopee@shopee.com",
        cc="vietnameairline@vietnameairfine@.com,a@a.com",
        bcc="example@example.com,ok@ok.org",
        subject="test_with_attachment_rawdata",
        body="this is the body",
        attachment_filename="testing.xlsx",
        attachment_data=excelbytes,
    )
