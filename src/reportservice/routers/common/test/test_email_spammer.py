import pytest
from pytest_mock import MockerFixture
from smtplib import SMTPRecipientsRefused
from pyinstrument import Profiler
from ..email_spammer import EmailSpammer


def test_email_spammer(mocker: MockerFixture):
    # mock the smtplib.SMTP object
    object = "src.reportservice.routers.common.email_spammer.smtplib.SMTP_SSL"
    mock_SMTP = mocker.MagicMock(name=object)
    mocker.patch(object, new=mock_SMTP)

    mailer = EmailSpammer("Nguyen Van Mock", "mock@lazada.com", "khongphaipassword")

    assert mock_SMTP.return_value.ehlo.call_count == 1
    assert mock_SMTP.return_value.login.call_count == 1

    mailer.send("to", "subject", "body")
    assert mock_SMTP.return_value.send_message.call_count == 1


@pytest.fixture
def spammerwithlove(smtpconfig):
    spammer = EmailSpammer(
        username=smtpconfig["username"],
        account=smtpconfig["account"],
        password=smtpconfig["password"],
        smtp_server=smtpconfig["server"],
        smtp_port=smtpconfig["port"],
        useSSL=smtpconfig["useSSL"],
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
        cc="vietnameairline@domain.com,a@a.com",
        bcc="example@example.com,ok@ok.org",
        subject="test_simple_multiple_with_cc_bcc",
        body="this is the body",
    )


def test_with_attachment_file(spammerwithlove, excelfile):
    spammerwithlove.send(
        to="lazada@lazada.com,shopee@shopee.com",
        cc="vietnameairline@domain.com,a@a.com",
        bcc="example@example.com,ok@ok.org",
        subject="test_with_attachment_file",
        body="this is the body",
        attachment_filename=excelfile,
    )


def test_with_attachment_rawdata(spammerwithlove, excelbytes):
    spammerwithlove.send(
        to="lazada@lazada.com,shopee@shopee.com",
        cc="vietnameairline@domain.com,a@a.com",
        bcc="example@example.com,ok@ok.org",
        subject="test_with_attachment_rawdata",
        body="this is the body",
        attachment_filename="testing.xlsx",
        attachment_data=excelbytes,
    )


def test_send_nothing(spammerwithlove):
    with pytest.raises(SMTPRecipientsRefused):
        spammerwithlove.send(to="", subject="test_simple", body="this is the body")


def test_send_wrong_address(spammerwithlove):
    spammerwithlove.send(to="[totheworld]", subject="test_simple", body="this is the body")


def test_spammer_performance(smtpconfig):
    with Profiler() as profiler:
        for i in range(10):
            EmailSpammer(
                username=smtpconfig["username"],
                account=smtpconfig["account"],
                password=smtpconfig["password"],
                smtp_server=smtpconfig["server"],
                smtp_port=smtpconfig["port"],
                useSSL=smtpconfig["useSSL"],
            )

    profiler.write_html("profile_emailspammer.html")
