import json
import pathlib
import httpx
import yaml
from app.config import settings

FIELDS = yaml.safe_load(
    pathlib.Path("app/config_files/fields.yaml").read_text(encoding="utf-8")
)

SYSTEM_PROMPT = """1、你是一个公司合同信息提取专家，只能帮我提取合同内容的信息，**绝对不可以加入任何主观分析和判断**。
2、我方集团下包括的公司有："艾德韦宣","艾迪霖杰","愿景艾德","范思广告","设计周"。
请按照要求提取合同内的信息，如果某项信息未找到，请回答"未找到"。"""

FIELD_RULES = {
    "合同类型": "请从以下五种类型中判断：承揽合同, 运输合同, 租赁合同, 财产保险合同, 押金合同。如若合同中只有押金没有其他付款需求则为押金合同；如果有则写为：租赁合同（含押金）。如有酒店住宿、订房、晚宴，则写为承揽合同。如果不属于以上，则归类为承揽合同。",
    "合同名称": "把提供某某服务中的\"某某服务\"作为合同名称，且以合同两字结尾。如有判断为：保密，终止，补充协议，需括号提示（xx协议）（不是文档标题）",
    "合作方": "1.必须提取合同中除我方公司（本公司）所扮演角色（如甲方/乙方/丙方等）对应的名称以外的所有签约主体名称。2.签约主体类型包括但不限于：公司、事务所、学校、机构、行政单位或自然人。【高优先级覆盖规则】如果合同内容中明确出现\"实际付款对象某某公司\"或\"由某某公司代付\"等描述，则该实际付款或代付的\"某某公司\"（仅限公司）必须被提取为唯一的合作方。3.【无付款描述时适用】如果合同中未出现第3条所述的付款公司描述：4.如果是双边协议，提取唯一的签约主体名称。5.如果是三方或多方协议，必须根据合同中甲乙丙丁方角色定义，将所有非我方公司所对应的签约主体名称全部列出。6.提取出的合作方名称之间必须且仅能使用英文逗号加一个空格分隔。7.【禁止】包含我方公司名称。8.如果甲乙双方都是我方公司名称，则提取乙方公司名称为合作方。",
    "项目编号": "查找以SRQ、SEQ、SWQ、SPQ或SDQ开头的项目编号，如果没有找到则写：未找到",
    "合同金额": "强制提取第一个出现的金额数字，格式化为xxx,xxx.xx的形式（如134500元格式化为134,500.00）。如果合同名称里面包含保密协议，则不填写金额。",
    "合同币种": "币种类型，统一格式为[币种]（如人民币记录为[RMB]，美元记录为[USD]等）。如合同中没有体现币种，则记录为[RMB]",
    "甲方公司": "强制覆盖逻辑：1.唯一信息来源是合同中涉及款项支付或收取的条款。2.甲方公司必须是合同项下款项的支付义务方（Payer）。如果支付是由其关联公司、搭建公司或供应商代付，该支付义务方仍视作甲方。如果没有支付信息，就以合同中甲方作为甲方公司。",
    "乙方公司": "强制覆盖逻辑：1.唯一信息来源是合同中涉及款项支付或收取的条款。2.乙方公司必须是合同项下款项的最终接收方/收款方（Payee/Recipient）。如果没有支付信息，就以合同中乙方作为乙方公司。",
    "合同年度": "查找以SRQ、SEQ、SWQ、SPQ或SDQ开头的项目编号，并且取第四位和第五位作为年份，且在前面补上20，结果为4位纯数字。如果没有找到则写：未找到",
    "合同期限": "合同的有效期限或服务起止时间。",
    "违约金额/比例": "违约金的具体金额或比例，未找到则写：未找到",
    "审计条款": "合同中关于审计相关的条款描述，未找到则写：未找到",
    "项目序号": "留空字符串。",
}


def _build_schema():
    keys = [f["key"] for f in FIELDS]
    return {
        "type": "object",
        "properties": {
            k: {"type": "string", "description": FIELD_RULES.get(k, "")} for k in keys
        },
        "required": keys,
    }


def extract_fields(text: str) -> dict:
    if not settings.ollama_url:
        raise RuntimeError("OLLAMA_URL 未配置")

    user_prompt = (
        "请仔细分析以下合同内容，并严格按照要求提取信息，并且严格按照json格式输出：\n"
        f"合同内容：{text}"
    )

    resp = httpx.post(
        f"{settings.ollama_url.rstrip('/')}/api/chat",
        json={
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "format": _build_schema(),
            "stream": False,
            "options": {"temperature": 0, "num_predict": 1200},
        },
        timeout=900,
    )
    resp.raise_for_status()
    raw = resp.json()["message"]["content"]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        s, e = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[s : e + 1])

    data.setdefault("项目序号", "")
    return data
