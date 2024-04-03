import pytest
from pyinstrument import Profiler
from ..async_email_spammer import AsyncEmailSpammer


@pytest.mark.asyncio
async def test_just_send_async():
    import aiosmtplib
    from email.message import EmailMessage

    message = EmailMessage()
    message["From"] = "pytest@localhost"
    message["To"] = "somebody@example.com"
    message["Subject"] = "Hello World!"
    message.set_content("Sent via aiosmtplib")

    await aiosmtplib.send(message, hostname="172.23.111.200", port=1026, timeout=3)


@pytest.mark.asyncio
async def test_create_spammer(smtpconfig):
    import logging

    logging.getLogger("aiosmtplib").setLevel(logging.DEBUG)

    spammer = AsyncEmailSpammer(
        username=smtpconfig["username"],
        account=smtpconfig["account"],
        password=smtpconfig["password"],
        smtp_server=smtpconfig["server"],
        smtp_port=smtpconfig["port"],
        useSSL=smtpconfig["useSSL"],
        timeout=5,
    )
    await spammer.connect()


@pytest.fixture
def asyncspammer(smtpconfig):
    spammer = AsyncEmailSpammer(
        username=smtpconfig["username"],
        account=smtpconfig["account"],
        password=smtpconfig["password"],
        smtp_server=smtpconfig["server"],
        smtp_port=smtpconfig["port"],
        useSSL=smtpconfig["useSSL"],
    )
    yield spammer


@pytest.mark.asyncio
async def test_simple(asyncspammer):
    await asyncspammer.send(to="lazada@shopee.com", subject="test_simple", body="this is the body")


@pytest.mark.asyncio
async def test_simple_multiple(asyncspammer):
    await asyncspammer.send(
        to="lazada@lazada.com,shopee@shopee.com", subject="test_simple_multiple", body="this is the body"
    )


@pytest.mark.asyncio
async def test_simple_multiple_with_cc_bcc(asyncspammer):
    await asyncspammer.send(
        to="lazada@lazada.com,shopee@shopee.com",
        cc="vietnameairline@domain.com,a@a.com",
        bcc="example@example.com,ok@ok.org",
        subject="test_simple_multiple_with_cc_bcc",
        body="this is the body",
    )


@pytest.mark.asyncio
async def test_with_attachment_file(asyncspammer, excelfile):
    await asyncspammer.send(
        to="lazada@lazada.com,shopee@shopee.com",
        cc="vietnameairline@domain.com,a@a.com",
        bcc="example@example.com,ok@ok.org",
        subject="test_with_attachment_file",
        body="this is the body",
        attachment_filename=excelfile,
    )


@pytest.mark.asyncio
async def test_with_attachment_rawdata(asyncspammer, excelbytes):
    await asyncspammer.send(
        to="lazada@lazada.com,shopee@shopee.com",
        cc="vietnameairline@domain.com,a@a.com",
        bcc="example@example.com,ok@ok.org",
        subject="test_with_attachment_rawdata",
        body="this is the body",
        attachment_filename="testing.xlsx",
        attachment_data=excelbytes,
    )


@pytest.mark.asyncio
async def test_send_nothing(asyncspammer):
    with pytest.raises(ValueError):
        await asyncspammer.send(to="", subject="test_simple", body="this is the body")


@pytest.mark.asyncio
async def test_send_wrong_address(asyncspammer):
    await asyncspammer.send(to="[totheworld]", subject="test_simple", body="this is the body")


@pytest.mark.asyncio
async def test_spammer_performance(smtpconfig):
    with Profiler(async_mode=True) as profiler:
        for _ in range(10):
            spammer = AsyncEmailSpammer(
                username=smtpconfig["username"],
                account=smtpconfig["account"],
                password=smtpconfig["password"],
                smtp_server=smtpconfig["server"],
                smtp_port=smtpconfig["port"],
                useSSL=smtpconfig["useSSL"],
            )
            await spammer.connect()
            await spammer.send(to="lazada@shopee.com", subject="test_simple", body="this is the body")

    profiler.write_html("profile_asyncemailspammer.html")
