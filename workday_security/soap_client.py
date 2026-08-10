"""Minimal SOAP client for Workday Web Services (WWS).

Workday's delivered ``Get_*`` operations are the authoritative source for many
security objects. Rather than depend on a full WSDL/SOAP stack, this client
builds a WS-Security ``UsernameToken`` envelope with the standard library and
sends it with ``requests`` -- enough to invoke any ``Get_*`` operation and hand
back the parsed XML.

For anything but the simplest calls, consider ``zeep`` with the tenant WSDL;
this class exists to stay dependency-light and self-contained.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Dict, Optional

import requests

from .config import WorkdayConfig

DEFAULT_TIMEOUT = 120

_SOAP_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
_WSSE = (
    "http://docs.oasis-open.org/wss/2004/01/"
    "oasis-200401-wss-wssecurity-secext-1.0.xsd"
)

_ENVELOPE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="{soap_env}" xmlns:wd="{wd_ns}">
  <soapenv:Header>
    <wsse:Security xmlns:wsse="{wsse}" soapenv:mustUnderstand="1">
      <wsse:UsernameToken>
        <wsse:Username>{username}</wsse:Username>
        <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{password}</wsse:Password>
      </wsse:UsernameToken>
    </wsse:Security>
  </soapenv:Header>
  <soapenv:Body>
    {body}
  </soapenv:Body>
</soapenv:Envelope>"""


class SoapFault(RuntimeError):
    """Raised when Workday returns a SOAP fault."""


class SoapClient:
    """Invoke Workday WWS ``Get_*`` operations with WS-Security auth."""

    def __init__(self, config: WorkdayConfig, session: Optional[requests.Session] = None):
        self._config = config
        self._session = session or requests.Session()

    def call(
        self,
        service: str,
        operation: str,
        request_body: str = "",
        page: int = 1,
        count: int = 100,
    ) -> ET.Element:
        """Invoke a WWS operation and return the parsed ``<Body>`` element.

        Args:
            service: WWS service name, e.g. ``Identity_Management``.
            operation: Operation name, e.g. ``Get_Workday_Accounts``.
            request_body: Inner XML for the operation's request (namespaced under
                the ``wd:`` prefix). May include filters/response groups. If empty,
                a bare request with a response filter (page/count) is sent.
            page: 1-based page number for the response filter.
            count: Page size for the response filter.

        Returns:
            The parsed SOAP ``Body`` element (namespace-qualified children).

        Raises:
            SoapFault: if the response contains a SOAP fault.
        """
        wd_ns = f"urn:com.workday/bsvc"
        response_filter = (
            f"<wd:Response_Filter>"
            f"<wd:Page>{page}</wd:Page>"
            f"<wd:Count>{count}</wd:Count>"
            f"</wd:Response_Filter>"
        )
        inner = request_body or response_filter
        body = f'<wd:{operation}_Request>{inner}</wd:{operation}_Request>'

        envelope = _ENVELOPE_TEMPLATE.format(
            soap_env=_SOAP_ENV,
            wd_ns=wd_ns,
            wsse=_WSSE,
            username=_xml_escape(self._config.wws_username),
            password=_xml_escape(self._config.password),
            body=body,
        )

        headers: Dict[str, str] = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "",
        }
        resp = self._session.post(
            self._config.wws_url(service),
            data=envelope.encode("utf-8"),
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )

        root = ET.fromstring(resp.content)
        body_el = root.find(f"{{{_SOAP_ENV}}}Body")
        if body_el is None:
            resp.raise_for_status()
            raise SoapFault("SOAP response contained no Body element")

        fault = body_el.find(f"{{{_SOAP_ENV}}}Fault")
        if fault is not None:
            reason = fault.findtext("faultstring") or ET.tostring(fault, encoding="unicode")
            raise SoapFault(f"Workday SOAP fault: {reason}")

        resp.raise_for_status()
        return body_el


def _xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
