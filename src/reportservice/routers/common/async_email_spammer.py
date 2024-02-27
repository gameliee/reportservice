from typing import Optional, Any
from logging import Logger, getLogger
import aiosmtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.header import Header
from email.utils import formataddr
import os.path as osp
import certifi  # ensure we always have certificate


class AsyncEmailSpammer:
    def __init__(
        self: str,
        username: str,
        account: str,
        password: str,
        smtp_server="smtp.gmail.com",
        smtp_port=465,
        logger: Logger | None = None,
        useSSL: bool = True,
        timeout: int = 5,
    ) -> None:
        """create a email handler for sending a lot of emails
        :param username: e.g: 'Nguyen Van Test'
        :param account: username, e.g: 'testnv@gmail.com'
        :password, e.g.: 'xxxxxx'
        :smtp_server
        :smtp_port
        """
        super().__init__()
        if logger is None:
            logger = getLogger()
        self.logger = logger
        self.username = username
        self.account = account
        self.pwd = password
        self.useSSL = useSSL
        self.timeout = timeout
        if useSSL is True:
            context = ssl.create_default_context(cafile=certifi.where())
            smtp_server = aiosmtplib.SMTP(hostname=smtp_server, port=smtp_port, timeout=timeout, tls_context=context)
        else:
            smtp_server = aiosmtplib.SMTP(hostname=smtp_server, port=smtp_port, timeout=timeout, start_tls=False)

        self.smtp_server = smtp_server

    async def connect(self):
        server: aiosmtplib.SMTP = self.smtp_server
        await server.connect()
        if server.is_ehlo_or_helo_needed:
            await server.ehlo()
        response = await self.smtp_server.login(self.account, self.pwd, timeout=self.timeout)
        return response

    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        attachment_filename: Optional[str] = None,
        attachment_data: Optional[bytes] = None,
    ) -> Any:
        """actually sending

        Args:
            to (str): receiver addresses in comma-splited format, eg 'm@gmail.com,n@gmail.com'
            subject (str): the email subject
            body (str): the email body
            cc (Optional[str], optional): CC addresses in comma-splited format, eg 'm@gmail.com,n@gmail.com'. Defaults to None.
            bcc (Optional[str], optional): BCC addresses in comma-splited format, eg 'm@gmail.com,n@gmail.com'. Defaults to None.
            attachment_filename (Optional[str], optional): If a filepath, attach the file and ignore `attachment_data`, otherwise a name to represent `attachment_data`. Defaults to None.
            attachment_data (Optional[bytes], optional): Raw file data to be attach. Ignore if `attachment_filename` was used. Defaults to None.

        Returns:
            Any: The output of `smtplib.SMTP_SSL.send_message`
        """
        message = MIMEMultipart()
        message["From"] = formataddr((str(Header(self.username, "utf-8")), self.account))
        message["To"] = to
        if cc is not None:
            message["Cc"] = cc
        if bcc is not None:
            message["Bcc"] = bcc
        message["Subject"] = subject
        _bd = MIMEText(body, "html")
        message.attach(_bd)
        if attachment_filename is not None:
            if osp.isfile(attachment_filename):
                with open(attachment_filename, "rb") as _fp:
                    attach_data = MIMEApplication(_fp.read(), _subtype="xlsx")
                attach_data.add_header("Content-Disposition", "attachment", filename=osp.basename(attachment_filename))
                print("attach a file into attachment")
                message.attach(attach_data)
            else:
                attach_data = MIMEApplication(attachment_data, _subtype="xlsx")
                attach_data.add_header("Content-Disposition", "attachment", filename=attachment_filename)
                print("attach bytestream into attachment")
                message.attach(attach_data)

        async with self.smtp_server:
            ret = await self.smtp_server.send_message(message)

        return ret
