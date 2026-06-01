from __future__ import annotations

import re


PHONE_FLEX_PAT = re.compile(r"((?:\(?0\d{1,2}\)?)[\s.\-)]*\d{3,4}[\s.\-]*\d{4}|0\d{1,2}\d{7,8})")
CONTACT_DEPT_SUFFIXES = (
    "기획팀", "행정팀", "관리실", "민원실", "홍보실", "부서", "지원청", "추진단", "센터", "본부", "담당관", "담당",
    "과", "팀", "실", "국", "처",
)
CONTACT_DEPT_SUFFIX_PATTERN = "|".join(re.escape(suffix) for suffix in sorted(CONTACT_DEPT_SUFFIXES, key=len, reverse=True))
CONTACT_PERSON_TITLE_PATTERN = r"(?:주무관|담당자?|팀장|과장|실장|센터장|국장|처장|장학사|장학관|소장|계장)"
CONTACT_DEPT_PAT_LIGHT = re.compile(
    rf"([가-힣A-Za-z0-9·\s]{{1,40}}(?:{CONTACT_DEPT_SUFFIX_PATTERN})(?:\s+[가-힣A-Za-z0-9·\s]{{1,20}}(?:{CONTACT_DEPT_SUFFIX_PATTERN}))?)"
)
CONTACT_STRUCTURED_DEPT_PHONE_PAT = re.compile(
    rf"(?:[가-힣A-Za-z0-9·]{{2,20}}(?:교육청|시청|구청|도청)\s+)?(?P<dept>[가-힣A-Za-z0-9·\s]{{2,40}}(?:{CONTACT_DEPT_SUFFIX_PATTERN}))(?:\s+담당자?\s*[:：]?\s*(?P<person>[가-힣]{{2,4}})(?:\s*(?:{CONTACT_PERSON_TITLE_PATTERN}))?)?|"
    rf"(?:[가-힣A-Za-z0-9·]{{2,20}}(?:교육청|시청|구청|도청)\s+)?(?P<dept_alt>[가-힣A-Za-z0-9·\s]{{2,40}}(?:{CONTACT_DEPT_SUFFIX_PATTERN}))(?:\s+(?P<person_alt>[가-힣]{{2,4}})(?:\s*(?:{CONTACT_PERSON_TITLE_PATTERN}))?)?\s*[\(（]?\s*[☎☏]?\s*(?P<phone>0\d{{1,2}}-?\d{{3,4}}-?\d{{4}})"
)
CONTACT_REVIEWER_TABLE_PAT = re.compile(r"(심사위원|위원장|성명|직위|소속)")
CONTACT_EXPLICIT_CUE_PAT = re.compile(r"(문의|문의처|연락처|전화|담당|☎|☏|TEL|Tel|tel)")
ATTACHMENT_FILENAME_LINE_PAT = re.compile(r"\.(?:hwp|hwpx|pdf)\b", re.I)


def norm_space(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip().lower()


CONTACT_GENERIC_DEPT_EXACT = {
    norm_space("문의"), norm_space("문의사항"), norm_space("기타문의사항"), norm_space("문의처"), norm_space("연락처"),
    norm_space("전화"), norm_space("문의전화"), norm_space("담당전화"), norm_space("담당자연락처"),
}
CONTACT_COMPANY_NOISE_PAT = re.compile(r"(?:주식회사|건축사사무소|종합건축사사무소|건축사무소|건축설계사무소|엔지니어링기술사사무소)", re.I)
CONTACT_DEPT_SENTENCE_NOISE_PAT = re.compile(r"(?:자료\s*전송|접수\s*장소|회신\s*메일|우선\s*홍보|반드시\s*확인|전송하고|확인하여|등록\s*후\s*통해|공모전\s*분석|분석하고\s*공정)", re.I)
CONTACT_MANAGEMENT_AGENCY_NOISE_PAT = re.compile(r"(?:공모관리기관|공모\s*관리기관|공모운영기관|공모\s*운영기관|공모운영업체|공모\s*운영업체|평가업체)", re.I)
CONTACT_SHORT_NOISE_DEPTS = {"마실", "관실", "사실"}
CONTACT_EXTERNAL_PORTAL_PAT = re.compile(r"(?:공모전.kr|competition\.kr|competition@masilwide\.com|masilwide\.com|마실와이드)", re.I)
CONTACT_EXTERNAL_PORTAL_CUE_PAT = re.compile(r"(?:질의\s*접수|질의\s*답변|응모\s*접수|제출\s*방법|설계공모\s*홈페이지|개별\s*질의\s*불가|전자우편.*개별\s*질의\s*불가)", re.I)
CONTACT_EXTERNAL_PORTAL_NOISE_PHONES = {"02-6010-1022"}
CONTACT_SUBMISSION_CUE_PAT = re.compile(r"(?:접수처|제출처|접수장소|질의\s*접수|응모\s*접수|제안서\s*제출처|방문\s*접수|우편\s*접수|전자우편\s*접수|접수\s*및\s*문의)", re.I)
CONTACT_ENTRUSTED_MANAGEMENT_CUE_PAT = re.compile(r"(?:공모관리기관|공모\s*관리기관|공모관리용역사|공모\s*관리용역사|설계공모\s*관리용역사|관리용역사|운영용역사|운영업체|공모전\s*운영|마실와이드|마실\b|평가\s*용역업체|평가기관|서울경제진흥원|산업정책연구원)", re.I)
CONTACT_CONTRACT_CUE_PAT = re.compile(r"(?:계약담당|계약부서|계약일|착공|착수|준공|완공|계약서\s*관리)", re.I)
CONTACT_RESULT_CUE_PAT = re.compile(r"(?:결과공고|당선자|당선작|입상작|선정업체)", re.I)
CONTACT_GUIDELINE_CUE_PAT = re.compile(r"(?:설계지침서|과업지시서|지침서)", re.I)
SCHOOL_ORG_CUE_PAT = re.compile(r"(?:학교|교육청|교육지원청|유치원|대학교|대학병원)")
OWNER_SUBORDINATE_DEPT_CUE_PAT = re.compile(r"(?:과|팀|실|국|처|센터|본부|지원청|추진단|행정실)$")
CONTACT_OTHER_SENTENCE_FRAGMENT_PAT = re.compile(r"(?:명이\s*변경되었을\s*경우|후속\s*기타\s*공모전\s*진행|등록\s*후\s*통해|공모전을\s*분석하고\s*공정)", re.I)
MANUAL_FIELD_OVERRIDES: dict[str, dict[str, str]] = {}
