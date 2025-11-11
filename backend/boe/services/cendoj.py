import requests
from lxml import etree
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Example base URL(s) — replace with provider endpoint or pass full URLs to fetch_decision
DEFAULT_CENDOJ_BASE = "https://www.poderjudicial.es/cendoj"

def fetch_decision_xml(url: str, timeout: int = 20) -> Optional[str]:
    """
    Fetches an XML/HTML representation of a CENDOJ decision from a given URL.
    Caller is responsible for providing a valid URL (API or detail page).
    """
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception:
        logger.exception("fetch_decision_xml failed for %s", url)
        return None

def _text_from_element(el):
    if el is None:
        return ""
    return "".join(el.itertext()).strip()

def parse_cendoj_xml(xml_text: str) -> Dict[str, Any]:
    """
    Parse common CENDOJ-like XML/HTML to extract metadata.
    Tries multiple common tag names; tolerant to missing fields.
    Returns dict with keys: unique_id, court, decision_date, decision_number, subject, parties, content.
    """
    out = {
        "unique_id": None, "court": None, "decision_date": None,
        "decision_number": None, "subject": None, "parties": None,
        "content": None, "raw_xml": xml_text
    }
    try:
        parser = etree.HTMLParser()  # accept HTML as many pages aren't strict XML
        doc = etree.fromstring(xml_text.encode("utf-8"), parser=parser)

        # heuristics for id
        candidates = doc.xpath("//@id | //meta[@name='DC.identifier']/@content | //meta[@name='citation_number']/@content")
        if candidates:
            out["unique_id"] = candidates[0]

        # court / organismo / tribunal
        court_paths = [
            "//organo/text()", "//tribunal/text()", "//div[@class='organo']//text()",
            "//meta[@name='DC.publisher']/@content", "//span[@class='tribunal']//text()"
        ]
        for p in court_paths:
            v = doc.xpath(p)
            if v:
                out["court"] = v[0].strip()
                break

        # date
        date_paths = ["//fecha/text()", "//meta[@name='DC.date']/@content", "//span[@class='fecha']//text()", "//time/@datetime"]
        for p in date_paths:
            v = doc.xpath(p)
            if v:
                try:
                    d = v[0].strip()
                    out["decision_date"] = datetime.fromisoformat(d.split("T")[0]).date()
                except Exception:
                    try:
                        out["decision_date"] = datetime.strptime(v[0].strip(), "%d/%m/%Y").date()
                    except Exception:
                        pass
                break

        # decision number
        num_paths = ["//numResolucion/text()", "//numero/text()", "//meta[@name='DC.identifier']/@content", "//span[@class='number']//text()"]
        for p in num_paths:
            v = doc.xpath(p)
            if v:
                out["decision_number"] = v[0].strip()
                break

        # subject / materia / asunto
        subj_paths = ["//materia/text()", "//asunto/text()", "//meta[@name='DC.subject']/@content", "//title/text()", "//h1/text()"]
        for p in subj_paths:
            v = doc.xpath(p)
            if v:
                out["subject"] = v[0].strip()
                break

        # parties / partes
        parties_paths = ["//partes/text()", "//div[@class='partes']//text()", "//meta[@name='citation_author']/@content"]
        for p in parties_paths:
            v = doc.xpath(p)
            if v:
                out["parties"] = " ".join([x.strip() for x in v if x.strip()])[:2000]
                break

        # main content: try common container selectors
        content_paths = [
            "//div[@class='textoSentencia']",
            "//div[@id='sentencia']",
            "//div[contains(@class,'decision-content')]",
            "//article",
            "//body"
        ]
        content_text = None
        for p in content_paths:
            nodes = doc.xpath(p)
            if nodes:
                # if node list, join texts
                if isinstance(nodes, list):
                    content_text = " ".join([_text_from_element(n) for n in nodes])
                else:
                    content_text = _text_from_element(nodes)
                if content_text and len(content_text) > 50:
                    break
        if not content_text:
            content_text = _text_from_element(doc)

        out["content"] = content_text.strip() if content_text else ""
        # ensure unique_id fallback from content or URL contained BOE-like ids
        if not out["unique_id"]:
            m = doc.xpath("//meta[@name='DC.identifier']/@content")
            if m:
                out["unique_id"] = m[0]

    except Exception:
        logger.exception("parse_cendoj_xml failed")
    return out